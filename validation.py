import boto3
from botocore.client import Config

# TODO Homework 0: refactor the solution to make it production-ready:
#  - make sure no destination output paths are hardcoded
#  - organise the code in a better way
#  - fix inconsistencies
#  - mind the naming
#  - use logging instead of print
#  - ... change and any other things which you don't like
MINIO_ENDPOINT = "http://localhost:9100"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin123"
SOURCE_MINIO_BUCKET = "microscopy-data"
SOURCE_MINIO_FOLDER = "xml"
DESTINATION_MINIO_BUCKET = "bronze"
DESTINATION_OUTPUT_FOLDERS = [
    "xml/month=2024-01/",
    "xml/month=2024-02/",
    "xml/month=2024-03/",
    "xml/month=2024-04/",
    "xml/month=2024-05/",
    "xml/month=2024-06/",
    "xml/month=2024-07/",
    "xml/month=2024-08/",
    "xml/month=2024-09/",
    "xml/month=2024-10/",
    "xml/month=2024-11/",
    "xml/month=2024-12/",
    "xml/month=2025-01/",
    "xml/month=2025-02/",
    "xml/month=2025-03/",
    "xml/month=2025-04/",
    "xml/month=2025-05/",
    "xml/month=2025-06/",
]

s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    config=Config(signature_version="s3v4"),
    region_name="us-east-1",
)

# TODO Homework 1
#  implement the class to log first LIMIT records and the general issues count
#  see the draft below
# class FileLogger:
#     # limit = 10
#
#     def __str__(self):
#         return (
#             f'There are top {self.limit} problematic files:',
#             self.records,
#             f'and {self.count} more'
#         )

paginator = s3.get_paginator("list_objects_v2")

# TODO Homework 2: adapt algorithm for the larger files number
source_files = {
    obj["Key"].split("/")[-1]: obj["ETag"]
    for page in paginator.paginate(Bucket=SOURCE_MINIO_BUCKET, Prefix=SOURCE_MINIO_FOLDER)
    for obj in page.get("Contents", [])
    if obj["Key"].endswith(".xml")
}

dest_files = {}
for folder in DESTINATION_OUTPUT_FOLDERS:
    for page in paginator.paginate(Bucket=DESTINATION_MINIO_BUCKET, Prefix=folder):
        for obj in page.get("Contents", []):
            filename = obj["Key"].split("/")[-1]
            dest_files[filename] = obj["ETag"]

# TODO Homework 3: adapt algorithm for comparing the files byte by byte in case of ETags mismatch.
#  For testing purposes, upload the file via multipart upload

# TODO Homework 4: [depends on HW 3]:
#  move the comparison to the separate thread in Python
#  to speed up the processing

print(f"Files in source: {len(source_files)}")
print(f"Files in destination: {len(dest_files)}\n")

missing = []
etag_mismatch = []
ok = 0

for filename, source_etag in source_files.items():
    if filename not in dest_files:
        missing.append(filename)
        continue
    if source_etag != dest_files[filename]:
        etag_mismatch.append((filename, source_etag, dest_files[filename]))
        continue
    ok += 1

print(f"Success: {ok}")
print(f"Missing: {len(missing)}")
print(f"ETag mismatch: {len(etag_mismatch)}\n")

if missing:
    print("Files missing:")
    for f in missing:
        print(f"  {f}")

if etag_mismatch:
    print("\nETag are not equal:")
    for filename, src_etag, dst_etag in etag_mismatch:
        print(f" {filename}")
        print(f" source: {src_etag}")
        print(f" dest: {dst_etag}")
