#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
init_repo "$@"
load_primary_team
description=$(jq -r '.description // ""' <<< "$TEAM_DATA")
python3 - "$description" "$ORG/$TEAM" <<'PY'
import calendar
import datetime
import re
import sys

def fail(message):
    print(f"FAIL [{sys.argv[2]}] {message}", file=sys.stderr)
    sys.exit(1)

dates = re.findall(r"\[MEMBERSHIP_REVIEW=([^\]]*)\]", sys.argv[1])
if len(dates) != 1 or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", dates[0]):
    fail("Expected one [MEMBERSHIP_REVIEW=YYYY-MM-DD] marker.")
try:
    reviewed = datetime.date.fromisoformat(dates[0])
except ValueError:
    fail("Invalid review calendar date.")
today = datetime.datetime.now(datetime.timezone.utc).date()
if reviewed > today:
    fail(f"Review date {reviewed} is in the future.")
year = reviewed.year + 1
expiry = datetime.date(year, reviewed.month, min(reviewed.day, calendar.monthrange(year, reviewed.month)[1]))
if today > expiry:
    fail(f"Review {reviewed} expired after {expiry}.")
print(f"PASS [{sys.argv[2]}] Review {reviewed} is current through {expiry} (UTC, inclusive).")
PY
