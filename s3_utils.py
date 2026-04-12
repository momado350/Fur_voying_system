import boto3
from botocore.exceptions import NoCredentialsError


def upload_file_to_s3(file, filename, config):
    s3 = boto3.client(
        's3',
        aws_access_key_id=config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=config['AWS_SECRET_ACCESS_KEY'],
        region_name=config['AWS_S3_REGION']
    )

    s3.upload_fileobj(
        file,
        config['AWS_S3_BUCKET_NAME'],
        filename
    )

    return f"https://{config['AWS_S3_BUCKET_NAME']}.s3.{config['AWS_S3_REGION']}.amazonaws.com/{filename}"
