import csv
import sys


def load(path):
    # excel csv got BOM in front, utf-8-sig eat it
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main():
    if len(sys.argv) != 3:
        print("usage: python access_review.py users.csv leavers.csv")
        sys.exit(1)

    users = load(sys.argv[1])
    leavers = load(sys.argv[2])

    active_count = 0
    found = []

    # TODO: ids not cleaned yet, " E1004" or "e1004" will not match
    for user in users:
        if user["status"] != "active":
            continue
        active_count += 1

        for leaver in leavers:
            if user["user_id"] == leaver["employee_id"]:
                found.append((user, leaver))

    print(f"checked {active_count} active accounts against {len(leavers)} leavers")

    if len(found) == 0:
        print("no leaver still active")
        return

    print(f"{len(found)} leaver(s) still active:")
    for user, leaver in found:
        print(f"  {user['user_id']}  {user['name']}  left {leaver['leave_date']}  last login {user['last_login']}")


if __name__ == "__main__":
    main()
