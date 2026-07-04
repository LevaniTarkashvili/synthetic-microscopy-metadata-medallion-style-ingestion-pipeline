import io
import os
import xml.etree.ElementTree as ET

import boto3
from botocore.client import Config
from dotenv import load_dotenv

SOURCE_FOLDER = "./data"
SOURCE_MINIO_BUCKET = "microscopy-data"
DESTINATION_MINIO_BUCKET = "bronze"
S3_PREFIX = "xml/"

load_dotenv()
s3 = boto3.client(
    "s3",
    endpoint_url=os.environ["MINIO_ENDPOINT"],
    aws_access_key_id=os.environ["MINIO_ACCESS_KEY"],
    aws_secret_access_key=os.environ["MINIO_SECRET_KEY"],
    config=Config(signature_version="s3v4"),
    region_name="us-east-1",
)

paginator = s3.get_paginator("list_objects_v2")
pages = paginator.paginate(
    Bucket=SOURCE_MINIO_BUCKET,
    Prefix=S3_PREFIX,
)

keys = [
    obj["Key"]
    for page in pages
    for obj in page.get("Contents")
    if obj["Key"].endswith(".xml")
]

for key in keys:
    response = s3.get_object(Bucket=SOURCE_MINIO_BUCKET, Key=key)
    content = response["Body"].read()

    root = ET.fromstring(content)
    generation_date = root.findtext("GenerationDate")

    # Homework 5
    if generation_date:
        year_month = generation_date[:7]
    else:
        year_month = "missing"
        print(f"No GenerationDate found in {key}; sending it to month=missing")
    destination_key = f"{S3_PREFIX}month={year_month}/{key.split('/')[-1]}"
    s3.upload_fileobj(io.BytesIO(content), DESTINATION_MINIO_BUCKET, destination_key)
    print(f"File was transfered to bronze: {destination_key}")
