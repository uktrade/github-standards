#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
init_repo "$@"
rulesets=$(api_pages "repos/$REPO/rulesets?includes_parents=false&per_page=100")
jq -e 'any(.[];
    .source_type == "Repository" and .name == "Datadog PR Gates" and
    .enforcement == "active" and .target == "branch"
)' <<< "$rulesets" >/dev/null || fail "No active repository-level Datadog PR Gates branch ruleset."
pass "Datadog PR Gates is present and active; individual gates and branch coverage are not validated."
