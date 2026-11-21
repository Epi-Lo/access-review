import argparse
import csv
import sys
from datetime import date, timedelta

# default only, some policy use 60, can change with --days
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


def login_after_leave(user, leaver):
    # still active is one thing, login after leave date means someone really using it
    last_login = (user["last_login"] or "").strip()
    leave_date = (leaver["leave_date"] or "").strip()
    # one side empty cannot compare, the leaver line still show anyway
    if last_login == "" or leave_date == "":
        return False
    return date.fromisoformat(last_login) > date.fromisoformat(leave_date)


def find_no_id(users):
    no_id = []
    for user in users:
        if is_active(user) and clean_id(user["user_id"]) == "":
            no_id.append(user)
    return no_id


def find_dormant(users, as_of, skip_ids, days=DORMANT_DAYS):
    cutoff = as_of - timedelta(days=days)
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

        # <= not <, exactly on the cutoff day also count
        if date.fromisoformat(last_login) <= cutoff:
            dormant.append(user)

    return dormant


def find_admins(users):
    admins = []
    for user in users:
        if not is_active(user):
            continue
        # TODO: only "admin" for now, real systems also got "superuser", "domain admin" etc
        if (user.get("role") or "").strip().lower() == "admin":
            admins.append(user)
    return admins


def show_login(user):
    return (user["last_login"] or "").strip() or "never"


def main():
    # now got --days also, counting len(sys.argv) getting messy, argparse easier
    parser = argparse.ArgumentParser(description="check a system user list against the hr leaver list")
    parser.add_argument("users", help="users.csv from the system")
    parser.add_argument("leavers", help="leavers.csv from hr")
    # review is always "as of" some date, normally period end. default today
    parser.add_argument("as_of", nargs="?", help="yyyy-mm-dd, default today")
    parser.add_argument("--days", type=int, default=DORMANT_DAYS,
                        help=f"no login for this many days = dormant, default {DORMANT_DAYS}")
    args = parser.parse_args()

    users = load(args.users, USER_COLS)
    leavers = load(args.leavers, LEAVER_COLS)
    as_of = date.fromisoformat(args.as_of) if args.as_of else date.today()

    active_count, found = find_leavers(users, leavers)

    print(f"checked {active_count} active accounts against {len(leavers)} leavers")

    if len(found) == 0:
        print("no leaver still active")
    else:
        print(f"{len(found)} leaver(s) still active:")
        for user, leaver in found:
            line = f"  {user['user_id']}  {user['name']}  left {leaver['leave_date']}  last login {show_login(user)}"
            if login_after_leave(user, leaver):
                line += "  <- login after leaving"
            print(line)

    no_id = find_no_id(users)
    if no_id:
        print()
        print(f"{len(no_id)} active account(s) with no user_id, check by hand:")
        for user in no_id:
            print(f"  {user['name']}  last login {show_login(user)}")

    skip_ids = {clean_id(user["user_id"]) for user, _ in found}
    dormant = find_dormant(users, as_of, skip_ids, args.days)

    print()
    print(f"as of {as_of}, {len(dormant)} account(s) no login for {args.days}+ days:")
    for user in dormant:
        print(f"  {user['user_id']}  {user['name']}  last login {show_login(user)}")

    # role column is optional, old user list without it still can run
    if users and "role" in users[0]:
        admins = find_admins(users)
        print()
        print(f"{len(admins)} active admin account(s), each one should have an approval:")
        for user in admins:
            print(f"  {user['user_id']}  {user['name']}  last login {show_login(user)}")


if __name__ == "__main__":
    main()
