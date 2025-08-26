"""
S3 Storage Service for handling file uploads
"""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional, Dict, Any, List
import uuid
import logging
from PIL import Image
import io
import os
from app.core.config import settings

logger = logging.getLogger(__name__)

class S3StorageService:
    def __init__(self):
        self.bucket_name = settings.s3_bucket_name
        self.region = settings.aws_region
        
        # Check if S3 configuration is available
        if not self.bucket_name or not settings.aws_access_key_id or not settings.aws_secret_access_key:
            logger.warning("S3 configuration incomplete. S3 service disabled. Required: S3_BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
            self.s3_client = None
            return
        
        # Initialize S3 client (Supabase S3-compatible)
        try:
            client_config = {
                'aws_access_key_id': settings.aws_access_key_id,
                'aws_secret_access_key': settings.aws_secret_access_key,
                'region_name': self.region
            }
            
            # Add endpoint URL for Supabase S3-compatible storage
            if settings.s3_endpoint_url:
                client_config['endpoint_url'] = settings.s3_endpoint_url
            
            self.s3_client = boto3.client('s3', **client_config)
            
            # Test connection only if bucket name is valid
            if self.bucket_name:
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                logger.info(f"S3 connection established for bucket: {self.bucket_name}")
            
        except NoCredentialsError:
            logger.warning("AWS credentials not found. S3 service disabled.")
            self.s3_client = None
        except ClientError as e:
            logger.error(f"S3 initialization failed: {e}")
            self.s3_client = None
        except Exception as e:
            logger.error(f"S3 service initialization failed: {e}")
            self.s3_client = None
    
    async def upload_property_image(
        self,
        file_content: bytes,
        user_id: str,
        property_id: str,
        filename: str,
        content_type: str = "image/jpeg"
    ) -> Dict[str, Any]:
        """
        Upload property image to S3
        
        Args:
            file_content: Image file content as bytes
            user_id: User ID for organizing files
            property_id: Property ID for organizing files
            filename: Original filename
            content_type: MIME type of the file
            
        Returns:
            Dict with upload result including URL
        """
        if not self.s3_client:
            return {"error": "S3 service not available", "url": None}
        
        try:
            # Generate unique filename
            file_extension = os.path.splitext(filename)[1].lower()
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            
            # Create S3 key
            s3_key = f"properties/{user_id}/{property_id}/{unique_filename}"
            
            # Process and optimize image
            processed_content = await self._process_image(file_content, file_extension)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=processed_content,
                ContentType=content_type,
                CacheControl='max-age=31536000',  # 1 year cache
                Metadata={
                    'user_id': user_id,
                    'property_id': property_id,
                    'original_filename': filename
                }
            )
            
            # Generate URL (Supabase or AWS)
            if settings.s3_endpoint_url:
                # Supabase URL format
                image_url = f"https://bpomacnqaqzgeuahhlka.supabase.co/storage/v1/object/public/{self.bucket_name}/{s3_key}"
            else:
                # Standard AWS S3 URL format
                image_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            
            return {
                "url": image_url,
                "s3_key": s3_key,
                "size": len(processed_content),
                "content_type": content_type
            }
            
        except Exception as e:
            logger.error(f"Image upload failed: {e}")
            return {"error": str(e), "url": None}
    
    async def upload_multiple_images(
        self,
        files: List[Dict[str, Any]],
        user_id: str,
        property_id: str
    ) -> List[Dict[str, Any]]:
        """
        Upload multiple property images
        
        Args:
            files: List of file dictionaries with 'content', 'filename', 'content_type'
            user_id: User ID
            property_id: Property ID
            
        Returns:
            List of upload results
        """
        results = []
        
        for file_data in files:
            result = await self.upload_property_image(
                file_content=file_data['content'],
                user_id=user_id,
                property_id=property_id,
                filename=file_data['filename'],
                content_type=file_data.get('content_type', 'image/jpeg')
            )
            results.append(result)
        
        return results
    
    async def delete_property_image(
        self,
        s3_key: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Delete property image from S3
        
        Args:
            s3_key: S3 object key
            user_id: User ID for authorization
            
        Returns:
            Dict with deletion result
        """
        if not self.s3_client:
            return {"error": "S3 service not available", "success": False}
        
        try:
            # Verify the image belongs to the user
            if not s3_key.startswith(f"properties/{user_id}/"):
                return {"error": "Unauthorized to delete this image", "success": False}
            
            # Delete from S3
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            return {"success": True, "message": "Image deleted successfully"}
            
        except Exception as e:
            logger.error(f"Image deletion failed: {e}")
            return {"error": str(e), "success": False}
    
    async def get_property_images(
        self,
        user_id: str,
        property_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all images for a property
        
        Args:
            user_id: User ID
            property_id: Property ID
            
        Returns:
            List of image information
        """
        if not self.s3_client:
            return []
        
        try:
            prefix = f"properties/{user_id}/{property_id}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            images = []
            for obj in response.get('Contents', []):
                # Generate URL based on storage type
                if settings.s3_endpoint_url:
                    image_url = f"https://bpomacnqaqzgeuahhlka.supabase.co/storage/v1/object/public/{self.bucket_name}/{obj['Key']}"
                else:
                    image_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{obj['Key']}"
                
                images.append({
                    "url": image_url,
                    "s3_key": obj['Key'],
                    "size": obj['Size'],
                    "last_modified": obj['LastModified'].isoformat()
                })
            
            return images
            
        except Exception as e:
            logger.error(f"Get images failed: {e}")
            return []
    
    async def generate_presigned_upload_url(
        self,
        user_id: str,
        property_id: str,
        filename: str,
        content_type: str,
        expiration: int = 3600
    ) -> Dict[str, Any]:
        """
        Generate presigned URL for direct client uploads
        
        Args:
            user_id: User ID
            property_id: Property ID
            filename: Original filename
            content_type: MIME type
            expiration: URL expiration time in seconds
            
        Returns:
            Dict with presigned URL and upload fields
        """
        if not self.s3_client:
            return {"error": "S3 service not available"}
        
        try:
            # Generate unique filename
            file_extension = os.path.splitext(filename)[1].lower()
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            s3_key = f"properties/{user_id}/{property_id}/{unique_filename}"
            
            # Generate presigned POST URL
            response = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=s3_key,
                Fields={
                    'Content-Type': content_type,
                    'Cache-Control': 'max-age=31536000'
                },
                Conditions=[
                    {'Content-Type': content_type},
                    ['content-length-range', 1, 10485760]  # 1 byte to 10MB
                ],
                ExpiresIn=expiration
            )
            
            # Add the final URL where the image will be accessible
            if settings.s3_endpoint_url:
                final_url = f"https://bpomacnqaqzgeuahhlka.supabase.co/storage/v1/object/public/{self.bucket_name}/{s3_key}"
            else:
                final_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            
            return {
                "upload_url": response['url'],
                "fields": response['fields'],
                "final_url": final_url,
                "s3_key": s3_key
            }
            
        except Exception as e:
            logger.error(f"Presigned URL generation failed: {e}")
            return {"error": str(e)}
    
    # Private methods
    
    async def _process_image(
        self,
        file_content: bytes,
        file_extension: str,
        max_width: int = 1920,
        max_height: int = 1080,
        quality: int = 85
    ) -> bytes:
        """
        Process and optimize image
        
        Args:
            file_content: Original image bytes
            file_extension: File extension
            max_width: Maximum width
            max_height: Maximum height
            quality: JPEG quality (1-100)
            
        Returns:
            Processed image bytes
        """
        try:
            # Open image
            image = Image.open(io.BytesIO(file_content))
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            
            # Resize if too large
            if image.width > max_width or image.height > max_height:
                image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Save optimized image
            output = io.BytesIO()
            
            if file_extension.lower() in ['.jpg', '.jpeg']:
                image.save(output, format='JPEG', quality=quality, optimize=True)
            elif file_extension.lower() == '.png':
                image.save(output, format='PNG', optimize=True)
            elif file_extension.lower() == '.webp':
                image.save(output, format='WEBP', quality=quality, optimize=True)
            else:
                # Default to JPEG
                image.save(output, format='JPEG', quality=quality, optimize=True)
            
            return output.getvalue()
            
        except Exception as e:
            logger.warning(f"Image processing failed, using original: {e}")
            return file_content
    
    def _validate_image_file(self, content_type: str, file_size: int) -> Dict[str, Any]:
        """
        Validate image file
        
        Args:
            content_type: MIME type
            file_size: File size in bytes
            
        Returns:
            Validation result
        """
        # Check content type
        allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg']
        if content_type not in allowed_types:
            return {
                "valid": False,
                "error": f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
            }
        
        # Check file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_size:
            return {
                "valid": False,
                "error": f"File too large. Maximum size: {max_size / (1024*1024):.1f}MB"
            }
        
        return {"valid": True}


# Global storage service instance
storage_service = S3StorageService()
