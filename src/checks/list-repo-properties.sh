#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
[[ $# -le 1 ]] || error "Usage: ${0##*/} [ORG]"
ORG=${1:-uktrade}
[[ $ORG =~ ^[A-Za-z0-9_-]+$ ]] || error "Invalid organisation name."
api_pages "orgs/$ORG/properties/values?per_page=100" |
    jq -c '.[] | {
        repository: .repository_full_name,
        properties: (.properties | map({key: .property_name, value}) | from_entries)
    }'
