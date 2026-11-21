import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date

from access_review import LEAVER_COLS, find_admins, find_dormant, find_leavers, find_no_id, load, login_after_leave


def user(uid, status="active", last_login="2026-11-01"):
    return {"user_id": uid, "name": "x", "status": status, "last_login": last_login}


def leaver(eid):
    return {"employee_id": eid, "name": "x", "leave_date": "2026-09-30"}


class FindLeaversTest(unittest.TestCase):
    def test_exact_id(self):
        count, found = find_leavers([user("E1004"), user("E1005")], [leaver("E1004")])
        self.assertEqual(count, 2)
        self.assertEqual(len(found), 1)

    def test_hr_id_with_space_and_small_letter(self):
        # this one was missed in the first version, report said no leaver at all
        _, found = find_leavers([user("E1004"), user("E1006")], [leaver("e1004"), leaver(" E1006")])
        self.assertEqual(len(found), 2)

    def test_disabled_account_not_counted(self):
        count, found = find_leavers([user("E1003", status="disabled")], [leaver("E1003")])
        self.assertEqual(count, 0)
        self.assertEqual(found, [])

    def test_status_with_big_letter_still_active(self):
        # "Active" used to give 0 active and 0 finding, no warning at all
        count, found = find_leavers([user("E1004", status="Active")], [leaver("E1004")])
        self.assertEqual(count, 1)
        self.assertEqual(len(found), 1)

    def test_blank_ids_not_matched(self):
        _, found = find_leavers([user("")], [leaver("")])
        self.assertEqual(found, [])
        self.assertEqual(len(find_no_id([user("")])), 1)


class LoginAfterLeaveTest(unittest.TestCase):
    def test_login_after_leave_date(self):
        # left 09-30 but still login on 10-12, someone using the account already
        self.assertTrue(login_after_leave(user("E1004", last_login="2026-10-12"), leaver("E1004")))

    def test_never_login_leaver_no_crash(self):
        self.assertFalse(login_after_leave(user("E1010", last_login=""), leaver("E1010")))


class FindDormantTest(unittest.TestCase):
    def test_old_login_is_dormant(self):
        users = [user("E1001", last_login="2026-11-01"), user("E1009", last_login="2026-05-20")]
        dormant = find_dormant(users, date(2026, 11, 18), set())
        self.assertEqual([u["user_id"] for u in dormant], ["E1009"])

    def test_leaver_not_listed_again(self):
        users = [user("E1006", last_login="2026-08-01")]
        dormant = find_dormant(users, date(2026, 11, 18), {"E1006"})
        self.assertEqual(dormant, [])

    def test_exactly_90_days_is_dormant(self):
        # 2026-08-20 to 2026-11-18 is 90 days, was missed because of <
        dormant = find_dormant([user("E2001", last_login="2026-08-20")], date(2026, 11, 18), set())
        self.assertEqual(len(dormant), 1)

    def test_never_login_is_dormant(self):
        dormant = find_dormant([user("E2002", last_login="")], date(2026, 11, 18), set())
        self.assertEqual(len(dormant), 1)

    def test_60_day_policy_catches_70_day_old_login(self):
        # 2026-09-09 to 2026-11-18 is 70 days, 90 day rule miss it but 60 day policy should list
        users = [user("E2003", last_login="2026-09-09")]
        self.assertEqual(find_dormant(users, date(2026, 11, 18), set()), [])
        self.assertEqual(len(find_dormant(users, date(2026, 11, 18), set(), days=60)), 1)


class FindAdminsTest(unittest.TestCase):
    def test_active_admin_listed(self):
        users = [dict(user("E1002"), role="admin"), dict(user("E1001"), role="user")]
        self.assertEqual([u["user_id"] for u in find_admins(users)], ["E1002"])

    def test_disabled_admin_not_listed(self):
        users = [dict(user("E1003", status="disabled"), role="admin")]
        self.assertEqual(find_admins(users), [])


class CommandLineTest(unittest.TestCase):
    def test_days_option_changes_the_dormant_rule(self):
        here = os.path.dirname(os.path.abspath(__file__))
        result = subprocess.run(
            [sys.executable, "access_review.py", "sample/users.csv", "sample/leavers.csv", "2026-11-18", "--days", "60"],
            cwd=here, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("no login for 60+ days", result.stdout)

    def test_report_marks_login_after_leaving(self):
        here = os.path.dirname(os.path.abspath(__file__))
        result = subprocess.run(
            [sys.executable, "access_review.py", "sample/users.csv", "sample/leavers.csv", "2026-11-18"],
            cwd=here, capture_output=True, text=True,
        )
        e1004 = [line for line in result.stdout.splitlines() if "E1004" in line][0]
        self.assertIn("login after leaving", e1004)


class LoadTest(unittest.TestCase):
    def test_missing_column_exit(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write("staff_id,name,leave_date\nE1004,x,2026-09-30\n")
        try:
            with self.assertRaises(SystemExit):
                load(f.name, LEAVER_COLS)
        finally:
            os.remove(f.name)


if __name__ == "__main__":
    unittest.main()
