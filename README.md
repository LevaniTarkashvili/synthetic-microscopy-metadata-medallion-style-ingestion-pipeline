# Fixes

## Homework 1 — `FileLogger` class 
`validation.py`

- Added a `FileLogger` class. It logs the first `LIMIT` records (default 10)
  and keeps the issues count, instead of storing every record. A
  `records` list holds the sample, and `count` holds the total.

- `add(record)` counts every issue but only keeps the first `LIMIT` records.

- `__str__` prints a short report. It shows the first `LIMIT` records and a
  final `"and M more"` line, where `M` is how many issues were counted but not
  shown.

- `missing` and `etag_mismatch` are now `FileLogger` instances, and the report 
   just prints each one.
