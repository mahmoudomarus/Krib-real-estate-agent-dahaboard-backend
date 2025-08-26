"""
File upload routes for S3 integration
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List
import logging

from app.models.schemas import (
    ImageUploadResponse, PresignedUploadRequest, PresignedUploadResponse, SuccessResponse
)
from app.services.storage_service import storage_service
from app.api.dependencies import get_current_user, verify_property_ownership

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/property/{property_id}/images", response_model=List[ImageUploadResponse])
async def upload_property_images(
    property_id: str,
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload multiple images for a property"""
    try:
        # Verify property ownership
        property_data = await verify_property_ownership(property_id, current_user)
        
        # Validate files
        if len(files) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 images allowed per upload"
            )
        
        upload_results = []
        
        for file in files:
            # Validate file type
            if not file.content_type or not file.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid file type: {file.filename}. Only images are allowed."
                )
            
            # Read file content
            file_content = await file.read()
            
            # Validate file size (10MB limit)
            if len(file_content) > 10 * 1024 * 1024:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File too large: {file.filename}. Maximum size is 10MB."
                )
            
            # Upload to S3
            upload_result = await storage_service.upload_property_image(
                file_content=file_content,
                user_id=current_user["id"],
                property_id=property_id,
                filename=file.filename or "image.jpg",
                content_type=file.content_type
            )
            
            if upload_result.get("error"):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to upload {file.filename}: {upload_result['error']}"
                )
            
            upload_results.append(ImageUploadResponse(**upload_result))
        
        # Update property images in database
        from app.core.supabase_client import supabase_client
        
        # Get current images
        current_images = property_data.get("images", [])
        new_image_urls = [result.url for result in upload_results]
        updated_images = current_images + new_image_urls
        
        # Update property
        supabase_client.table("properties").update({
            "images": updated_images
        }).eq("id", property_id).execute()
        
        return upload_results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload images"
        )


@router.post("/property/{property_id}/presigned-upload", response_model=PresignedUploadResponse)
async def get_presigned_upload_url(
    property_id: str,
    request: PresignedUploadRequest,
    current_user: dict = Depends(get_current_user)
):
    """Get presigned URL for direct client upload to S3"""
    try:
        # Verify property ownership
        await verify_property_ownership(property_id, current_user)
        
        # Validate content type
        if not request.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image files are allowed"
            )
        
        # Generate presigned URL
        result = await storage_service.generate_presigned_upload_url(
            user_id=current_user["id"],
            property_id=property_id,
            filename=request.filename,
            content_type=request.content_type
        )
        
        if result.get("error"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return PresignedUploadResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Presigned URL generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate upload URL"
        )


@router.get("/property/{property_id}/images")
async def get_property_images(
    property_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all images for a property"""
    try:
        # Verify property ownership
        await verify_property_ownership(property_id, current_user)
        
        # Get images from S3
        images = await storage_service.get_property_images(
            user_id=current_user["id"],
            property_id=property_id
        )
        
        return {"images": images}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get images error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get images"
        )


@router.delete("/property/{property_id}/images/{s3_key:path}", response_model=SuccessResponse)
async def delete_property_image(
    property_id: str,
    s3_key: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a specific property image"""
    try:
        # Verify property ownership
        property_data = await verify_property_ownership(property_id, current_user)
        
        # Delete from S3
        delete_result = await storage_service.delete_property_image(
            s3_key=s3_key,
            user_id=current_user["id"]
        )
        
        if not delete_result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=delete_result.get("error", "Failed to delete image")
            )
        
        # Update property images in database
        from app.core.supabase_client import supabase_client
        
        current_images = property_data.get("images", [])
        # Remove the deleted image URL from the list
        image_url = f"https://{storage_service.bucket_name}.s3.{storage_service.region}.amazonaws.com/{s3_key}"
        updated_images = [img for img in current_images if img != image_url]
        
        supabase_client.table("properties").update({
            "images": updated_images
        }).eq("id", property_id).execute()
        
        return SuccessResponse(message="Image deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete image error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete image"
        )


@router.post("/property/{property_id}/reorder-images", response_model=SuccessResponse)
async def reorder_property_images(
    property_id: str,
    image_urls: List[str],
    current_user: dict = Depends(get_current_user)
):
    """Reorder property images"""
    try:
        # Verify property ownership
        property_data = await verify_property_ownership(property_id, current_user)
        
        # Validate that all URLs belong to this property
        current_images = property_data.get("images", [])
        if len(image_urls) != len(current_images) or set(image_urls) != set(current_images):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image list for reordering"
            )
        
        # Update property with new order
        from app.core.supabase_client import supabase_client
        
        supabase_client.table("properties").update({
            "images": image_urls
        }).eq("id", property_id).execute()
        
        return SuccessResponse(message="Images reordered successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reorder images error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reorder images"
        )
