from fastapi import FastAPI, File, UploadFile, HTTPException
import logging
import os

from src.core.services.auth.domain.models.user import UserModel
from src.core.config.config import max_file_size, media_root

logger = logging.getLogger(__name__)

async def handle_photo_upload(photo: UploadFile, user: UserModel):
    try:
        # Validate filename
        if not photo.filename or ".." in photo.filename or "/" in photo.filename:
            if photo.filename:
                raise HTTPException(status_code=400, detail="Invalid file name")
            else:
                return None
        
        save_dir = media_root / 'users' / str(user.id) / "profile"
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate a secure filename
        file_ext = os.path.splitext(photo.filename)[1]
        secure_filename = f"profile_{user.id}{file_ext}"
        local_path = save_dir / secure_filename
        
        # Ensure directory exists with proper permissions
        try:
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # Verify directory is writable
            test_file = save_dir / "permission_test.tmp"
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
            except PermissionError:
                raise HTTPException(
                    status_code=500,
                    detail="Server doesn't have write permissions to the upload directory"
                )
            
        except Exception as e:
            logger.error(f"Directory creation failed: {e}")
            raise HTTPException(
                status_code=500,
                detail="Could not create upload directory"
            )



        logger.debug(f"Attempting to save to: {local_path}")

        # Save file
        try:
            with open(local_path, 'wb') as buffer:
                while content := await photo.read(max_file_size):  # 10MB chunks
                    buffer.write(content)
            return str(local_path.relative_to(media_root).as_posix())
            
        except PermissionError:
            logger.error(f"Permission denied for file: {local_path}")
            raise HTTPException(
                status_code=500,
                detail="Server couldn't write the file due to permission issues"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during file upload"
        )