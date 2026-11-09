#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
init_repo "$@"
load_tree
matches=$(jq -r '
    .tree[] | .path | select((split("/") | last | ascii_downcase) == "security.md")
' <<< "$TREE")
[[ -z $matches ]] || fail "Forbidden SECURITY.md path(s), case-insensitive: $matches"
pass "No SECURITY.md path exists on $REF."
