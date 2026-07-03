import io
import xml.etree.ElementTree as ET

import boto3
from botocore.client import Config

SOURCE_FOLDER = "./data"
SOURCE_MINIO_BUCKET = "microscopy-data"
DESTINATION_MINIO_BUCKET = "bronze"
S3_PREFIX = "xml/"

s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:9100",
    aws_access_key_id="minioadmin",
    aws_secret_access_key="minioadmin123",
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

    # TODO Homework 5: handle the case when generation_date is not found
    year_month = generation_date[:7]
    destination_key = f"{S3_PREFIX}month={year_month}/{key.split('/')[-1]}"
    s3.upload_fileobj(io.BytesIO(content), DESTINATION_MINIO_BUCKET, destination_key)
    print(f"File was transfered to bronze: {destination_key}")
