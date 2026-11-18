# access-review

Small script for user access review. Give it the user list from a system and the leaver list from HR, it tells you which leavers still got an active account.

This is the most common finding in an ITGC access review, so start from this one first.

It also lists active accounts with no login for 90+ days, as of the date you give (default today).

```sh
python access_review.py sample/users.csv sample/leavers.csv 2026-11-18
```

```
checked 8 active accounts against 3 leavers
2 leaver(s) still active:
  E1004  Chan Tai Man  left 2026-09-30  last login 2026-10-12
  E1006  Ho Chi Kit  left 2026-07-31  last login 2026-08-01

as of 2026-11-18, 1 account(s) no login for 90+ days:
  E1009  Cheung Wing Yan  last login 2026-05-20
```

## csv format

`users.csv`: `user_id,name,status,last_login` (status is `active` or `disabled`)

`leavers.csv`: `employee_id,name,leave_date`

If a column is missing it stops and tells you which one. Active account with empty `last_login` is listed as `never`. Active account with empty `user_id` cannot be matched, so it is listed for checking by hand.

Sample files are in `sample/`, all fake people.

## not done yet

- 90 days is fixed for now
- no admin / privileged account check

Python 3, no extra package needed.

```sh
python -m unittest
```
