import os
import boto3

s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("R2_ENDPOINT"),
    aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
    region_name="auto"
)

BUCKET = os.getenv("R2_BUCKET")


def upload_file(file, key):
    s3.upload_fileobj(
        file,
        BUCKET,
        key
    )

    return key
def delete_file(key):
    s3.delete_object(
        Bucket=BUCKET,
        Key=key
    )
