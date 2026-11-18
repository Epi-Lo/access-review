import csv
import sys
from datetime import date, timedelta

# TODO: 90 days hard code for now, some policy use 60
DORMANT_DAYS = 90

USER_COLS = ["user_id", "name", "status", "last_login"]
LEAVER_COLS = ["employee_id", "name", "leave_date"]


def load(path, need):
    # excel csv got BOM in front, utf-8-sig eat it
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        # wrong header before = KeyError traceback, better tell which column
        missing = [c for c in need if c not in (reader.fieldnames or [])]
        if missing:
            print(f"{path} missing column: {', '.join(missing)}")
            sys.exit(1)
        return list(reader)


def clean_id(s):
    # hr export got space and small letter, system side is "E1004"
    return (s or "").strip().upper()


def is_active(user):
    # some export write "Active", last time this one count as 0 active
    return (user["status"] or "").strip().lower() == "active"


def find_leavers(users, leavers):
    active_count = 0
    found = []

    for user in users:
        if not is_active(user):
            continue
        active_count += 1

        uid = clean_id(user["user_id"])
        # blank id cannot prove anything, two blank also not same person
        if uid == "":
            continue

        for leaver in leavers:
            if uid == clean_id(leaver["employee_id"]):
                found.append((user, leaver))

    return active_count, found


def find_no_id(users):
    no_id = []
    for user in users:
        if is_active(user) and clean_id(user["user_id"]) == "":
            no_id.append(user)
    return no_id


def find_dormant(users, as_of, skip_ids):
    cutoff = as_of - timedelta(days=DORMANT_DAYS)
    dormant = []

    for user in users:
        if not is_active(user):
            continue
        # already in the leaver list, no need show again
        if clean_id(user["user_id"]) in skip_ids:
            continue

        last_login = (user["last_login"] or "").strip()
        # active but never login is also a finding, don't crash on it
        if last_login == "":
            dormant.append(user)
            continue

        # <= not <, exactly 90 days also count as 90+
        if date.fromisoformat(last_login) <= cutoff:
            dormant.append(user)

    return dormant


def show_login(user):
    return (user["last_login"] or "").strip() or "never"


def main():
    if len(sys.argv) not in (3, 4):
        print("usage: python access_review.py users.csv leavers.csv [as_of yyyy-mm-dd]")
        sys.exit(1)

    users = load(sys.argv[1], USER_COLS)
    leavers = load(sys.argv[2], LEAVER_COLS)
    # review is always "as of" some date, normally period end. default today
    as_of = date.fromisoformat(sys.argv[3]) if len(sys.argv) == 4 else date.today()

    active_count, found = find_leavers(users, leavers)

    print(f"checked {active_count} active accounts against {len(leavers)} leavers")

    if len(found) == 0:
        print("no leaver still active")
    else:
        print(f"{len(found)} leaver(s) still active:")
        for user, leaver in found:
            print(f"  {user['user_id']}  {user['name']}  left {leaver['leave_date']}  last login {show_login(user)}")

    no_id = find_no_id(users)
    if no_id:
        print()
        print(f"{len(no_id)} active account(s) with no user_id, check by hand:")
        for user in no_id:
            print(f"  {user['name']}  last login {show_login(user)}")

    skip_ids = {clean_id(user["user_id"]) for user, _ in found}
    dormant = find_dormant(users, as_of, skip_ids)

    print()
    print(f"as of {as_of}, {len(dormant)} account(s) no login for {DORMANT_DAYS}+ days:")
    for user in dormant:
        print(f"  {user['user_id']}  {user['name']}  last login {show_login(user)}")


if __name__ == "__main__":
    main()
