#!/usr/bin/env bash
set -euo pipefail
shopt -s inherit_errexit

pass() { printf 'PASS [%s] %s\n' "$REPO" "$*"; }
fail() { printf 'FAIL [%s] %s\n' "${REPO:-input}" "$*" >&2; exit 1; }
error() { printf 'ERROR [%s] %s\n' "${REPO:-input}" "$*" >&2; exit 1; }

init_repo() {
    [[ $# == 1 && $1 =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] ||
        error "Usage: ${0##*/} OWNER/REPO"
    REPO=$1
    ORG=${REPO%%/*}
}

urlencode() { jq -nr --arg value "$1" '$value | @uri'; }
api() { gh api --hostname github.com --method GET "$@"; }
api_pages() { api "$1" --paginate | jq -s 'add'; }

property_value() {
    api "repos/$REPO/properties/values" |
        jq -c --arg name "$1" '[.[] | select(.property_name == $name)][0].value'
}

load_tree() {
    REF=$(api "repos/$REPO" --jq '.default_branch')
    TREE=$(api "repos/$REPO/git/trees/$(urlencode "$REF")?recursive=1")
    jq -e '.truncated == false' <<< "$TREE" >/dev/null ||
        error "Incomplete repository tree; cannot reliably check file absence."
}

read_file() {
    api "repos/$REPO/contents/$(urlencode "$1")" -f "ref=$REF" |
        jq -er 'select(.type == "file" and .encoding == "base64") | .content' |
        base64 --decode
}

load_primary_team() {
    local contents owners diagnostics access
    load_tree
    CODEOWNERS_PATH=$(jq -r '
        [.tree[] | select(.type == "blob") | .path] as $paths |
        [".github/CODEOWNERS", "CODEOWNERS", "docs/CODEOWNERS"] |
        map(select(. as $candidate | $paths | index($candidate))) | .[0] // empty
    ' <<< "$TREE")
    [[ -n $CODEOWNERS_PATH ]] || fail "No CODEOWNERS file in a supported location."
    diagnostics=$(api "repos/$REPO/codeowners/errors" -f "ref=$REF")
    if ! jq -e '.errors | length == 0' <<< "$diagnostics" >/dev/null; then
        jq -r '.errors[] | "\(.path):\(.line): \(.message)"' <<< "$diagnostics" >&2
        fail "GitHub reports CODEOWNERS errors."
    fi
    contents=$(read_file "$CODEOWNERS_PATH")
    owners=$(awk '
        { sub(/#.*/, ""); if ($1 == "*") {
            owners = ""; for (i = 2; i <= NF; i++) owners = owners (i == 2 ? "" : " ") $i
        }}
        END { print owners }
    ' <<< "$contents")
    [[ $owners =~ ^@([A-Za-z0-9_.-]+)/([A-Za-z0-9_-]+)$ ]] ||
        fail "The last * entry must name exactly one primary team."
    [[ ${BASH_REMATCH[1],,} == "${ORG,,}" ]] || fail "Primary team must belong to $ORG."
    TEAM=${BASH_REMATCH[2]}
    TEAM_DATA=$(api "orgs/$ORG/teams/$TEAM")
    jq -e '.privacy == "closed"' <<< "$TEAM_DATA" >/dev/null || fail "Primary team is not visible."
    access=$(api "orgs/$ORG/teams/$TEAM/repos/$REPO" \
        -H 'Accept: application/vnd.github.v3.repository+json')
    jq -e '.permissions.push == true or .permissions.maintain == true or .permissions.admin == true' \
        <<< "$access" >/dev/null || fail "Primary team lacks write-or-higher repository access."
}
