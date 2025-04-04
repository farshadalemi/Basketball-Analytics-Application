from minio import Minio
from minio.error import S3Error
import io
import os
import json
from datetime import timedelta
from app.core.config import settings

class MinioService:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_URL,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=False
        )
        self.ensure_bucket()

    def ensure_bucket(self):
        """Create the videos bucket if it doesn't exist and set public read policy."""
        try:
            if not self.client.bucket_exists(settings.MINIO_BUCKET):
                self.client.make_bucket(settings.MINIO_BUCKET)
                print(f"Bucket '{settings.MINIO_BUCKET}' created")
            else:
                print(f"Bucket '{settings.MINIO_BUCKET}' already exists")

            # Set public read policy for the bucket
            self.set_public_read_policy()
        except S3Error as err:
            print(f"Error creating bucket: {err}")

    def set_public_read_policy(self):
        """Set a public read policy for the bucket."""
        try:
            # Define a policy that allows public read access
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": ["*"]},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{settings.MINIO_BUCKET}/*"]
                    }
                ]
            }

            # Convert policy to JSON string
            policy_str = json.dumps(policy)

            # Set the policy
            self.client.set_bucket_policy(settings.MINIO_BUCKET, policy_str)
            print(f"Set public read policy for bucket: {settings.MINIO_BUCKET}")
        except Exception as e:
            print(f"Error setting bucket policy: {e}")

    def upload_video(self, file, object_name, content_type):
        """Upload a video file to MinIO."""
        try:
            print(f"Starting upload to MinIO: {object_name} with content type: {content_type}")

            # Make sure file is valid
            if not file:
                print("Error: No file provided")
                return False

            if not hasattr(file, "file"):
                print("Error: File object does not have file attribute")
                return False

            # Reset file position to beginning to ensure we read from the start
            file.file.seek(0)

            # Set default content type if none provided
            content_type = content_type or "video/mp4"

            # Get file size for logging only (not used for upload)
            try:
                position = file.file.tell()
                file.file.seek(0, 2)  # Move to end
                file_size = file.file.tell()
                file.file.seek(position)  # Reset position
                print(f"File size: {file_size} bytes")
            except Exception as e:
                print(f"Warning: Could not determine file size: {e}")
                # Continue anyway as we'll use streaming upload

            # Get file size
            file.file.seek(0, 2)  # Seek to the end of the file
            file_size = file.file.tell()  # Get current position (file size)
            file.file.seek(0)  # Reset to the beginning

            print(f"File size: {file_size} bytes")

            # Upload to MinIO using streaming with known size
            print(f"Uploading to bucket: {settings.MINIO_BUCKET}, object: {object_name}")
            self.client.put_object(
                bucket_name=settings.MINIO_BUCKET,
                object_name=object_name,
                data=file.file,
                length=file_size,  # Use actual file size
                content_type=content_type
            )

            print(f"Upload successful: {object_name}")
            return True
        except Exception as err:
            print(f"Error uploading file: {err}")
            import traceback
            traceback.print_exc()
            return False

    def get_presigned_url(self, object_name, expires=3600):
        """Generate a presigned URL for video streaming."""
        try:
            # Convert expires to timedelta if it's an integer
            if isinstance(expires, int):
                expires = timedelta(seconds=expires)

            print(f"[DEBUG] Generating presigned URL for {object_name} with expires={expires}")

            # Generate a presigned URL
            url = self.client.presigned_get_object(
                bucket_name=settings.MINIO_BUCKET,
                object_name=object_name,
                expires=expires
            )

            # Replace internal Docker hostname with external hostname
            # This is needed because the frontend can't access the internal Docker network
            if url:
                # Always replace the internal Docker hostname with localhost
                # This ensures the URL is accessible from the browser
                external_url = url.replace('minio:9000', 'localhost:9000')
                print(f"[DEBUG] Replaced internal URL with external URL: {external_url}")
                return external_url

            return url
        except Exception as err:
            print(f"Error generating URL: {err}")
            return None

    def get_direct_url(self, object_name):
        """Generate a direct URL for accessing objects."""
        try:
            # Create a direct URL to the object
            direct_url = f"http://localhost:9000/{settings.MINIO_BUCKET}/{object_name}"
            print(f"[DEBUG] Generated direct URL: {direct_url}")

            # Set anonymous access for this object to ensure it's publicly accessible
            try:
                self.client.set_object_acl(
                    bucket_name=settings.MINIO_BUCKET,
                    object_name=object_name,
                    acl='public-read'
                )
                print(f"[DEBUG] Set public-read ACL for {object_name}")
            except Exception as acl_err:
                print(f"[DEBUG] Could not set ACL (this is normal if using MinIO): {acl_err}")
                # MinIO doesn't support ACLs in the same way as S3, so this might fail
                # We'll rely on the bucket policy instead
                pass

            return direct_url
        except Exception as err:
            print(f"Error generating direct URL: {err}")
            return None

    def get_object(self, object_name):
        """Get an object from MinIO as a stream."""
        try:
            # Get the object data
            response = self.client.get_object(
                bucket_name=settings.MINIO_BUCKET,
                object_name=object_name
            )

            # Return the response data as a stream
            return response
        except S3Error as err:
            print(f"Error getting object: {err}")
            return None

    def download_file(self, object_name, file_path):
        """Download a file from MinIO to a local path."""
        try:
            # Get the object data
            self.client.fget_object(
                bucket_name=settings.MINIO_BUCKET,
                object_name=object_name,
                file_path=file_path
            )
            return True
        except S3Error as err:
            print(f"Error downloading file: {err}")
            return False

    def upload_file(self, file_obj, object_name, content_type):
        """Upload a file to MinIO."""
        try:
            # Get file size
            file_obj.seek(0, 2)  # Go to the end of the file
            file_size = file_obj.tell()  # Get current position (file size)
            file_obj.seek(0)  # Go back to the beginning

            # Upload the file
            self.client.put_object(
                bucket_name=settings.MINIO_BUCKET,
                object_name=object_name,
                data=file_obj,
                length=file_size,
                content_type=content_type
            )
            return True
        except S3Error as err:
            print(f"Error uploading file: {err}")
            return False

    def delete_video(self, object_name):
        """Delete a video from MinIO."""
        try:
            self.client.remove_object(
                bucket_name=settings.MINIO_BUCKET,
                object_name=object_name
            )
            return True
        except S3Error as err:
            print(f"Error deleting file: {err}")
            return False

# Create a singleton instance
minio_service = MinioService()
