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

## Homework 4 — byte checks in threads
`validation.py`

- Moved the byte-by-byte comparison to separate threads to speed up the
  processing. The comparison downloads files from S3, so running it inline made
  the loop wait on every mismatch.

- Each mismatch is collected in a `pending` list, then the comparisons run
  together in a `ThreadPoolExecutor` so the downloads overlap.

- The counting (`ok` / `etag_mismatch`) happens back on the main, so no locks are 
  needed.

## Homework 5 — handle a missing `generation_date`
`raw2bronze_transfer.py`

- NULL date is caught and the file is goes to a `month=missing` partition and also 
  a message is printed. Now the transfer does not crash when generation_date is not 
  found and the file is not lost.

## Homework 6 — hide credentials
`files_upload.py`, `raw2bronze_transfer.py`, `validation.py`

- The MinIO endpoint, access key, and secret key are no longer hardcoded. Each
  script now calls `load_dotenv()` and reads them from environment variables.

- Added `.env.example` 

- Added `python-dotenv` to `requirements.txt`.

## Homework 0 — production-ready cleanup
`validation.py`

- Removed the hardcoded list of `month=YYYY-MM` destination folders. Instead the
  script asks the bronze bucket for everything under the `xml` prefix, so it
  scans whatever folders actually exist (including `month=missing`) without them
  being written in the code.

- Replaced all `print` calls with the `logging` module. Counts are logged at
  `INFO` and problems (missing / mismatched files) at `WARNING`.

- Organised the script into functions (`build_s3_client`, `list_source_files`,
  `compare_buckets`, `report`, `main`) behind an `if __name__ == "__main__"` guard. 
  Also `s3` client is passed into the functions instead of being a global.

- Small consistency fixes: both the source and destination listings now skip
  non-`.xml` objects (previously only the source did), and docstrings were
  tidied up.
