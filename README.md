# access-review

Small script for user access review. Give it the user list from a system and the leaver list from HR, it tells you which leavers still got an active account.

This is the most common finding in an ITGC access review, so start from this one first.

```sh
python access_review.py sample/users.csv sample/leavers.csv
```

```
checked 7 active accounts against 3 leavers
2 leaver(s) still active:
  E1004  Chan Tai Man  left 2026-09-30  last login 2026-10-12
  E1006  Ho Chi Kit  left 2026-07-31  last login 2026-08-01
```

## csv format

`users.csv`: `user_id,name,status,last_login` (status is `active` or `disabled`)

`leavers.csv`: `employee_id,name,leave_date`

Sample files are in `sample/`, all fake people.

## not done yet

- ids must match exactly for now, no trimming or case fix
- no dormant account check (no login for a long time)
- no admin / privileged account check

Python 3, no extra package needed.
