import logging
import boto3
from pathlib import Path
from typing import List, Optional
from botocore.exceptions import ClientError, NoCredentialsError
from src.core.config import settings


class S3Sync:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.s3_client = None
        self._initialize_s3_client()

    def _initialize_s3_client(self):
        try:
            if settings.aws_access_key_id and settings.aws_secret_access_key:
                client_config = {
                    'aws_access_key_id': settings.aws_access_key_id,
                    'aws_secret_access_key': settings.aws_secret_access_key,
                    'region_name': settings.aws_region
                }
                
                # Add endpoint_url for MinIO or custom S3-compatible storage
                if settings.s3_endpoint_url:
                    client_config['endpoint_url'] = settings.s3_endpoint_url
                
                self.s3_client = boto3.client('s3', **client_config)
                self.logger.info("S3 client initialized successfully")
                
                # Create bucket if using MinIO and bucket doesn't exist
                if settings.s3_endpoint_url and settings.s3_bucket_name:
                    self._ensure_bucket_exists()
            else:
                self.logger.warning("AWS credentials not provided")
        except Exception as e:
            self.logger.error(f"Failed to initialize S3 client: {e}")

    def _ensure_bucket_exists(self):
        try:
            self.s3_client.head_bucket(Bucket=settings.s3_bucket_name)
            self.logger.info(f"Bucket {settings.s3_bucket_name} exists")
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                try:
                    self.s3_client.create_bucket(Bucket=settings.s3_bucket_name)
                    self.logger.info(f"Created bucket {settings.s3_bucket_name}")
                except Exception as create_error:
                    self.logger.error(f"Failed to create bucket: {create_error}")
            else:
                self.logger.error(f"Error checking bucket: {e}")

    def list_s3_objects(self, prefix: str = "") -> List[str]:
        if not self.s3_client or not settings.s3_bucket_name:
            self.logger.error("S3 client not initialized or bucket name not provided")
            return []
        
        try:
            objects = []
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=settings.s3_bucket_name, Prefix=prefix):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        key = obj['Key']
                        if key.lower().endswith(('.pdf', '.json')):
                            objects.append(key)
            
            self.logger.info(f"Found {len(objects)} relevant objects in S3")
            return objects
            
        except ClientError as e:
            self.logger.error(f"Error listing S3 objects: {e}")
            return []

    def download_file(self, s3_key: str, local_path: Path) -> bool:
        if not self.s3_client or not settings.s3_bucket_name:
            self.logger.error("S3 client not initialized or bucket name not provided")
            return False
        
        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.s3_client.download_file(
                settings.s3_bucket_name,
                s3_key,
                str(local_path)
            )
            
            self.logger.info(f"Downloaded {s3_key} to {local_path}")
            return True
            
        except ClientError as e:
            self.logger.error(f"Error downloading {s3_key}: {e}")
            return False

    def sync_documents(self, local_dir: Optional[str] = None) -> bool:
        if not self.s3_client:
            self.logger.error("S3 client not available")
            return False
        
        local_path = Path(local_dir or settings.documents_path)
        local_path.mkdir(parents=True, exist_ok=True)
        
        try:
            s3_objects = self.list_s3_objects()
            
            if not s3_objects:
                self.logger.warning("No documents found in S3")
                return True
            
            downloaded_count = 0
            skipped_count = 0
            
            for s3_key in s3_objects:
                file_name = Path(s3_key).name
                local_file_path = local_path / file_name
                
                if local_file_path.exists():
                    try:
                        s3_obj = self.s3_client.head_object(
                            Bucket=settings.s3_bucket_name,
                            Key=s3_key
                        )
                        s3_modified = s3_obj['LastModified'].timestamp()
                        local_modified = local_file_path.stat().st_mtime
                        
                        if s3_modified <= local_modified:
                            self.logger.info(f"Skipping {file_name} (local file is newer)")
                            skipped_count += 1
                            continue
                            
                    except Exception as e:
                        self.logger.warning(f"Error checking file dates for {s3_key}: {e}")
                
                if self.download_file(s3_key, local_file_path):
                    downloaded_count += 1
                else:
                    self.logger.error(f"Failed to download {s3_key}")
            
            self.logger.info(f"Sync complete: {downloaded_count} downloaded, {skipped_count} skipped")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during sync: {e}")
            return False

    def upload_file(self, local_path: Path, s3_key: Optional[str] = None) -> bool:
        if not self.s3_client or not settings.s3_bucket_name:
            self.logger.error("S3 client not initialized or bucket name not provided")
            return False
        
        if not local_path.exists():
            self.logger.error(f"Local file does not exist: {local_path}")
            return False
        
        s3_key = s3_key or local_path.name
        
        try:
            self.s3_client.upload_file(
                str(local_path),
                settings.s3_bucket_name,
                s3_key
            )
            
            self.logger.info(f"Uploaded {local_path} to {s3_key}")
            return True
            
        except ClientError as e:
            self.logger.error(f"Error uploading {local_path}: {e}")
            return False

    def is_configured(self) -> bool:
        return (self.s3_client is not None and 
                settings.s3_bucket_name is not None and 
                settings.aws_access_key_id is not None)