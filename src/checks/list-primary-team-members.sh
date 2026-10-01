#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
init_repo "$@"
load_primary_team
members=$(api_pages "orgs/$ORG/teams/$TEAM/members?per_page=100")
jq -r 'map(.login) | unique | sort | .[]' <<< "$members"
