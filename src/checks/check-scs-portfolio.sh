#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
init_repo "$@"
value=$(property_value scs_portfolio)
jq -e 'type == "string" and test("\\S")' <<< "$value" >/dev/null ||
    fail "scs_portfolio must contain a non-blank string; observed $value."
pass "scs_portfolio is populated: $(jq -r '.' <<< "$value")."
