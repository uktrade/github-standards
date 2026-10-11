#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
init_repo "$@"
[[ ${EXPECTED_SECURITY_CONFIGURATION_ID:-} =~ ^[1-9][0-9]*$ ]] ||
    error "Set EXPECTED_SECURITY_CONFIGURATION_ID to the approved positive numeric configuration ID."
configuration=$(api "repos/$REPO/code-security-configuration")
[[ -n $configuration ]] || fail "No security configuration is associated (HTTP 204)."
actual_id=$(jq -r '.configuration.id' <<< "$configuration")
status=$(jq -r '.status' <<< "$configuration")
[[ $actual_id == "$EXPECTED_SECURITY_CONFIGURATION_ID" ]] ||
    fail "Security configuration ID is $actual_id; expected $EXPECTED_SECURITY_CONFIGURATION_ID."
case "$status" in
    attached|enforced|enterprise_enforced) ;;
    *) fail "Approved security configuration is not successfully attached: $status." ;;
esac
pass "Security configuration $actual_id is $status."
