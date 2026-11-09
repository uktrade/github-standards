#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
init_repo "$@"
value=$(property_value code_security_enrolled)
[[ $value == '"true"' ]] || fail "code_security_enrolled must be \"true\"; observed $value. No legacy-property fallback."
pass 'code_security_enrolled is "true".'
