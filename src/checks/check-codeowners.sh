#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
init_repo "$@"
load_primary_team
pass "$CODEOWNERS_PATH has no GitHub diagnostics and names @$ORG/$TEAM as its valid primary team."
