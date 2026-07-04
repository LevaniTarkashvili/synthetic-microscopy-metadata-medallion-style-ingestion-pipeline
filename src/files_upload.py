import os

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv

SOURCE_FOLDER = "./data"
MINIO_BUCKET = "microscopy-data"
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
