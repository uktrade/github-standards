#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
init_repo "$@"
load_tree
templates=$(jq -r '
    .tree[] | select(.type == "blob") | .path |
    select(test("^(\\.github/|docs/)?pull_request_template\\.(md|txt)$"; "i") or
           test("^(\\.github/|docs/)?pull_request_template/[^/]+$"; "i"))
' <<< "$TREE")
if [[ -z $templates ]]; then
    printf 'SKIP [%s] No repository-local PR templates.\n' "$REPO"
    exit 0
fi
missing=0
while IFS= read -r template; do
    contents=$(read_file "$template")
    if [[ $contents != *"no secret values are present"* ]]; then
        printf 'FAIL [%s] %s lacks "no secret values are present".\n' "$REPO" "$template" >&2
        missing=1
    fi
done <<< "$templates"
[[ $missing == 0 ]] || exit 1
pass 'All repository-local PR templates contain "no secret values are present".'
