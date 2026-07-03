import os

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

SOURCE_FOLDER = "./data"
MINIO_BUCKET = "microscopy-data"
S3_PREFIX = "xml/"

# TODO homework 6: hide the credentials
s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:9100",
    aws_access_key_id="minioadmin",
    aws_secret_access_key="minioadmin123",
    config=Config(signature_version="s3v4"),
    region_name="us-east-1",
)

files = [
    os.path.join(SOURCE_FOLDER, f) for f in os.listdir(SOURCE_FOLDER)
    if os.path.isfile(os.path.join(SOURCE_FOLDER, f))
]

for file in files:
    filename = os.path.basename(file)
    s3_key = S3_PREFIX + filename
    try:
        s3.upload_file(file, MINIO_BUCKET, s3_key)
        print(f"{filename} was successfully uploaded")
    except ClientError as e:
        print(f'Error while loading {filename}: {e}')
