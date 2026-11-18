import os
import tempfile
import unittest
from datetime import date

from access_review import LEAVER_COLS, find_dormant, find_leavers, find_no_id, load


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
