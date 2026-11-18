import csv
import sys
from datetime import date, timedelta

# TODO: 90 days hard code for now, some policy use 60
DORMANT_DAYS = 90


def load(path):
    # excel csv got BOM in front, utf-8-sig eat it
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def clean_id(s):
    # hr export got space and small letter, system side is "E1004"
    return s.strip().upper()


def find_leavers(users, leavers):
    active_count = 0
    found = []

    for user in users:
        if user["status"] != "active":
            continue
        active_count += 1

        for leaver in leavers:
            if clean_id(user["user_id"]) == clean_id(leaver["employee_id"]):
                found.append((user, leaver))

    return active_count, found


def find_dormant(users, as_of, skip_ids):
    cutoff = as_of - timedelta(days=DORMANT_DAYS)
    dormant = []

    for user in users:
        if user["status"] != "active":
            continue
        # already in the leaver list, no need show again
        if clean_id(user["user_id"]) in skip_ids:
            continue

        last = date.fromisoformat(user["last_login"])
        if last < cutoff:
            dormant.append(user)

    return dormant


def main():
    if len(sys.argv) not in (3, 4):
        print("usage: python access_review.py users.csv leavers.csv [as_of yyyy-mm-dd]")
        sys.exit(1)

    users = load(sys.argv[1])
    leavers = load(sys.argv[2])
    # review is always "as of" some date, normally period end. default today
    as_of = date.fromisoformat(sys.argv[3]) if len(sys.argv) == 4 else date.today()

    active_count, found = find_leavers(users, leavers)

    print(f"checked {active_count} active accounts against {len(leavers)} leavers")

    if len(found) == 0:
        print("no leaver still active")
    else:
        print(f"{len(found)} leaver(s) still active:")
        for user, leaver in found:
            print(f"  {user['user_id']}  {user['name']}  left {leaver['leave_date']}  last login {user['last_login']}")

    skip_ids = {clean_id(user["user_id"]) for user, _ in found}
    dormant = find_dormant(users, as_of, skip_ids)

    print()
    print(f"as of {as_of}, {len(dormant)} account(s) no login for {DORMANT_DAYS}+ days:")
    for user in dormant:
        print(f"  {user['user_id']}  {user['name']}  last login {user['last_login']}")


if __name__ == "__main__":
    main()
