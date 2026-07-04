import logging
import os
from concurrent.futures import ThreadPoolExecutor

import boto3
from botocore.client import Config
from dotenv import load_dotenv

SOURCE_MINIO_BUCKET = "microscopy-data"
SOURCE_MINIO_FOLDER = "xml"
DESTINATION_MINIO_BUCKET = "bronze"
DESTINATION_MINIO_FOLDER = "xml"

MAX_WORKERS = 8


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


def build_s3_client():
    """Create a boto3 S3 client for MinIO"""
    return boto3.client(
        "s3",
        endpoint_url=os.environ["MINIO_ENDPOINT"],
        aws_access_key_id=os.environ["MINIO_ACCESS_KEY"],
        aws_secret_access_key=os.environ["MINIO_SECRET_KEY"],
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def files_are_identical(s3, source_key, destination_key):
    """Download both objects and compare their raw bytes."""
    source_bytes = s3.get_object(Bucket=SOURCE_MINIO_BUCKET, Key=source_key)["Body"].read()
    destination_bytes = s3.get_object(Bucket=DESTINATION_MINIO_BUCKET, Key=destination_key)["Body"].read()
    return source_bytes == destination_bytes


def list_source_files(s3):
    """Return {filename: (key, etag)} for every .xml object in the source bucket."""
    paginator = s3.get_paginator("list_objects_v2")
    return {
        obj["Key"].split("/")[-1]: (obj["Key"], obj["ETag"])
        for page in paginator.paginate(Bucket=SOURCE_MINIO_BUCKET, Prefix=SOURCE_MINIO_FOLDER)
        for obj in page.get("Contents", [])
        if obj["Key"].endswith(".xml")
    }


def compare_buckets(s3, source_files):
    """Compare the destination bucket against source_files."""

    paginator = s3.get_paginator("list_objects_v2")
    missing = FileLogger()
    etag_mismatch = FileLogger()
    ok = 0
    dest_count = 0
    pending = []

    for page in paginator.paginate(Bucket=DESTINATION_MINIO_BUCKET, Prefix=DESTINATION_MINIO_FOLDER):
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

    def compare_pending(item):
        filename, source_key, source_etag, dest_key, dest_etag = item
        identical = files_are_identical(s3, source_key, dest_key)
        return identical, filename, source_etag, dest_etag

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for identical, filename, source_etag, dest_etag in executor.map(compare_pending, pending):
            if identical:
                ok += 1
            else:
                etag_mismatch.add(f"{filename} (source={source_etag}, dest={dest_etag})")

    # Whatever remains in source_files was never matched in the destination.
    for filename in source_files:
        missing.add(filename)

    return ok, dest_count, missing, etag_mismatch


def report(source_count, dest_count, ok, missing, etag_mismatch):
    """Log the comparison summary and any problems."""
    logging.info("Files in source: %s", source_count)
    logging.info("Files in destination: %s", dest_count)
    logging.info("Success: %s", ok)
    logging.info("Missing: %s", missing.count)
    logging.info("ETag mismatch: %s", etag_mismatch.count)
    if missing.count:
        logging.warning("Files missing:\n%s", missing)
    if etag_mismatch.count:
        logging.warning("ETag are not equal:\n%s", etag_mismatch)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    load_dotenv()
    s3 = build_s3_client()
    source_files = list_source_files(s3)
    source_count = len(source_files)
    ok, dest_count, missing, etag_mismatch = compare_buckets(s3, source_files)
    report(source_count, dest_count, ok, missing, etag_mismatch)


if __name__ == "__main__":
    main()
