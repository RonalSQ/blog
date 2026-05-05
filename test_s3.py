import os
import boto3
from botocore.config import Config
from dotenv import load_dotenv

load_dotenv()

# Config
endpoint_url = os.environ.get('SUPABASE_S3_ENDPOINT')
access_key = os.environ.get('SUPABASE_S3_ACCESS_KEY')
secret_key = os.environ.get('SUPABASE_S3_SECRET_KEY')
bucket_name = os.environ.get('SUPABASE_STORAGE_BUCKET_NAME')

def test_upload(region_name):
    print(f"Testing region: {region_name}")
    s3 = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region_name,
        config=Config(signature_version='s3v4', s3={'addressing_style': 'path'})
    )
    
    try:
        s3.put_object(Bucket=bucket_name, Key='test_file.txt', Body=b'Hello World')
        print(f"SUCCESS with region {region_name}!")
        return True
    except Exception as e:
        print(f"FAILED with region {region_name}: {e}")
        return False

# Test common regions for supabase
regions = ['us-east-1', 'us-west-1', 'us-west-2', 'eu-central-1', 'eu-west-1']
for r in regions:
    if test_upload(r):
        break
