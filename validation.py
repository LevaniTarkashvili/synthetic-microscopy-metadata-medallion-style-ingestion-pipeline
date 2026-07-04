import os
from concurrent.futures import ThreadPoolExecutor

import boto3
from botocore.client import Config
from dotenv import load_dotenv

load_dotenv()

# TODO Homework 0: refactor the solution to make it production-ready:
#  - make sure no destination output paths are hardcoded
#  - organise the code in a better way
#  - fix inconsistencies
#  - mind the naming
#  - use logging instead of print
#  - ... change and any other things which you don't like
MINIO_ENDPOINT = os.environ["MINIO_ENDPOINT"]
MINIO_ACCESS_KEY = os.environ["MINIO_ACCESS_KEY"]
MINIO_SECRET_KEY = os.environ["MINIO_SECRET_KEY"]
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

# Homework 1
class FileLogger:
    """Logs the first LIMIT problematic files plus a count of the rest."""

    limit = 10

    def __init__(self):
        self.records = []
        self.count = 0

    def add(self, record):
        self.count += 1
        if len(self.records) < self.limit:
            self.records.append(record)

    def __str__(self):
        lines = [f"Top {self.limit} problematic files:"]
        lines.extend(f"  {record}" for record in self.records)
        remaining = self.count - len(self.records)
        if remaining > 0:
            lines.append(f"and {remaining} more")
        return "\n".join(lines)


# For Homework 3
def files_are_identical(source_key, destination_key):
    """Download both objects and compare their raw bytes."""
    source_bytes = s3.get_object(Bucket=SOURCE_MINIO_BUCKET, Key=source_key)["Body"].read()
    destination_bytes = s3.get_object(Bucket=DESTINATION_MINIO_BUCKET, Key=destination_key)["Body"].read()
    return source_bytes == destination_bytes


paginator = s3.get_paginator("list_objects_v2")

# Homework 2
source_files = {
    obj["Key"].split("/")[-1]: (obj["Key"], obj["ETag"])
    for page in paginator.paginate(Bucket=SOURCE_MINIO_BUCKET, Prefix=SOURCE_MINIO_FOLDER)
    for obj in page.get("Contents", [])
    if obj["Key"].endswith(".xml")
}
source_count = len(source_files)

missing = FileLogger()
etag_mismatch = FileLogger()
ok = 0
dest_count = 0
pending = []

for folder in DESTINATION_OUTPUT_FOLDERS:
    for page in paginator.paginate(Bucket=DESTINATION_MINIO_BUCKET, Prefix=folder):
        for obj in page.get("Contents", []):
            dest_count += 1
            filename = obj["Key"].split("/")[-1]
            entry = source_files.pop(filename, None)
            if entry is None:
                continue
            source_key, source_etag = entry
            if source_etag == obj["ETag"]:
                ok += 1
                continue

            pending.append((filename, source_key, source_etag, obj["Key"], obj["ETag"]))

# Homework 4
def compare_pending(item):
    filename, source_key, source_etag, dest_key, dest_etag = item
    identical = files_are_identical(source_key, dest_key)
    return identical, filename, source_etag, dest_etag

with ThreadPoolExecutor(max_workers=8) as executor:
    for identical, filename, source_etag, dest_etag in executor.map(compare_pending, pending):
        if identical:
            ok += 1
        else:
            etag_mismatch.add(f"{filename} (source={source_etag}, dest={dest_etag})")

# Whatever remains in source_files was never matched in the destination.
for filename in source_files:
    missing.add(filename)

print(f"Files in source: {source_count}")
print(f"Files in destination: {dest_count}\n")

print(f"Success: {ok}")
print(f"Missing: {missing.count}")
print(f"ETag mismatch: {etag_mismatch.count}\n")

if missing.count:
    print("Files missing:")
    print(missing)

if etag_mismatch.count:
    print("ETag are not equal:")
    print(etag_mismatch)
