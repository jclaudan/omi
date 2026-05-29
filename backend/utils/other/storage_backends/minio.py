import datetime
import os

import boto3
from botocore.exceptions import ClientError


def create_storage_client():
    s3 = boto3.client(
        's3',
        endpoint_url=os.getenv('MINIO_ENDPOINT'),
        aws_access_key_id=os.getenv('MINIO_ACCESS_KEY', os.getenv('MINIO_ROOT_USER', 'minioadmin')),
        aws_secret_access_key=os.getenv('MINIO_SECRET_KEY', os.getenv('MINIO_ROOT_PASSWORD', 'minioadmin')),
        region_name=os.getenv('MINIO_REGION', 'us-east-1'),
        use_ssl=os.getenv('MINIO_SSL', 'false').lower() == 'true',
    )
    return _S3StorageClient(s3)


class _S3BlobWriter:
    """Write-mode context manager: buffers in memory, then uploads on __exit__."""

    def __init__(self, s3_client, bucket_name, key, content_type):
        self._s3 = s3_client
        self._bucket = bucket_name
        self._key = key
        self._content_type = content_type
        self._buf = bytearray()

    def __enter__(self):
        return self

    def write(self, data):
        self._buf.extend(data)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self._s3.put_object(Bucket=self._bucket, Key=self._key, Body=bytes(self._buf), ContentType=self._content_type)
        del self._buf
        return False


class _S3Blob:
    """GCS-compatible blob object backed by S3/MinIO."""

    cache_control = None

    def __init__(self, s3_client, bucket_name: str, key: str):
        self._s3 = s3_client
        self._bucket = bucket_name
        self._key = key
        self.name = key
        self.size = None
        self.time_created = None
        self.metadata = None
        self._pending_metadata = {}

    def __setattr__(self, name, value):
        if name == 'metadata' and isinstance(value, dict):
            object.__setattr__(self, '_pending_metadata', value)
        object.__setattr__(self, name, value)

    def exists(self) -> bool:
        try:
            self._s3.head_object(Bucket=self._bucket, Key=self._key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] in ('404', 'NoSuchKey'):
                return False
            raise

    def reload(self):
        try:
            resp = self._s3.head_object(Bucket=self._bucket, Key=self._key)
            self.size = resp.get('ContentLength', 0)
            self.time_created = resp.get('LastModified')
            self.metadata = {k: v for k, v in resp.get('Metadata', {}).items()}
        except ClientError:
            self.metadata = {}

    def upload_from_filename(self, file_path: str, content_type: str = 'application/octet-stream'):
        extra = {}
        if self.cache_control:
            extra['CacheControl'] = self.cache_control
        if self._pending_metadata:
            extra['Metadata'] = {k: str(v) for k, v in self._pending_metadata.items()}
        with open(file_path, 'rb') as f:
            self._s3.put_object(Bucket=self._bucket, Key=self._key, Body=f, ContentType=content_type, **extra)

    def upload_from_string(self, data: bytes, content_type: str = 'application/octet-stream'):
        extra = {}
        if self.cache_control:
            extra['CacheControl'] = self.cache_control
        if self._pending_metadata:
            extra['Metadata'] = {k: str(v) for k, v in self._pending_metadata.items()}
        self._s3.put_object(
            Bucket=self._bucket,
            Key=self._key,
            Body=data if isinstance(data, (bytes, bytearray)) else data.encode(),
            ContentType=content_type,
            **extra,
        )

    def download_as_bytes(self) -> bytes:
        resp = self._s3.get_object(Bucket=self._bucket, Key=self._key)
        return resp['Body'].read()

    def download_to_filename(self, dest_path: str):
        resp = self._s3.get_object(Bucket=self._bucket, Key=self._key)
        with open(dest_path, 'wb') as f:
            f.write(resp['Body'].read())

    def delete(self):
        self._s3.delete_object(Bucket=self._bucket, Key=self._key)

    def make_public(self):
        pass  # Bucket-level public policy set at init by minio-init service

    def generate_signed_url(self, version=None, expiration=None, method='GET') -> str:
        if isinstance(expiration, datetime.timedelta):
            expires_in = int(expiration.total_seconds())
        else:
            expires_in = int(expiration) if expiration else 3600
        op = 'get_object' if method == 'GET' else 'put_object'
        return self._s3.generate_presigned_url(op, Params={'Bucket': self._bucket, 'Key': self._key}, ExpiresIn=expires_in)

    def open(self, mode: str = 'rb', content_type: str = 'application/octet-stream'):
        if mode == 'wb':
            return _S3BlobWriter(self._s3, self._bucket, self._key, content_type)
        raise ValueError(f'Unsupported S3 blob open mode: {mode}')


class _S3Bucket:
    """GCS-compatible bucket object backed by S3/MinIO."""

    def __init__(self, s3_client, bucket_name: str):
        self._s3 = s3_client
        self._name = bucket_name

    def blob(self, key: str) -> '_S3Blob':
        return _S3Blob(self._s3, self._name, key)

    def list_blobs(self, prefix: str = ''):
        blobs = []
        paginator = self._s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=self._name, Prefix=prefix):
            for obj in page.get('Contents', []):
                b = _S3Blob(self._s3, self._name, obj['Key'])
                b.size = obj['Size']
                b.time_created = obj.get('LastModified')
                blobs.append(b)
        return blobs


class _S3StorageClient:
    """GCS-compatible storage client backed by S3/MinIO."""

    def __init__(self, s3_client):
        self._s3 = s3_client

    def bucket(self, bucket_name: str) -> '_S3Bucket':
        return _S3Bucket(self._s3, bucket_name)


class MinIONotFound(Exception):
    pass
