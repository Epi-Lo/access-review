import unittest
from datetime import date

from access_review import find_dormant, find_leavers


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


class FindDormantTest(unittest.TestCase):
    def test_old_login_is_dormant(self):
        users = [user("E1001", last_login="2026-11-01"), user("E1009", last_login="2026-05-20")]
        dormant = find_dormant(users, date(2026, 11, 18), set())
        self.assertEqual([u["user_id"] for u in dormant], ["E1009"])

    def test_leaver_not_listed_again(self):
        users = [user("E1006", last_login="2026-08-01")]
        dormant = find_dormant(users, date(2026, 11, 18), {"E1006"})
        self.assertEqual(dormant, [])


if __name__ == "__main__":
    unittest.main()
