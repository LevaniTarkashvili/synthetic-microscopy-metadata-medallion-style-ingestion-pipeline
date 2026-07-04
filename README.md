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

## Homework 2 — scale the comparison
`validation.py`

- The old code built two full dicts in memory (every source file and every
  destination file) before comparing. Now only the source side is kept in a
  dict.

- The destination is streamed page by page and each destination file is compared 
  as it arrives and popped out of the source dict. `pop` looks a file up and
  removes it in one step: a match is checked, then taken off the source dict.

- Whatever is left in the source dict after the stream was never seen in the
  destination, so those are the `missing` files.

## Homework 3 — byte-by-byte check on ETag mismatch
`validation.py`

- Added a `files_are_identical` helper. When two ETags differ, it downloads both
  objects and compares their raw bytes.

- Equal bytes now count as `ok`. only a real byte difference is reported as an
  ETag mismatch. 
  
- The source dict now holds `(key, etag)` instead of just the etag.
