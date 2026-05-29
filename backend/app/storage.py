"""ReelIQ Backend — S3-Compatible Storage Client (works with MinIO locally)"""
import boto3
import uuid
from pathlib import Path
from app.config import get_settings

settings = get_settings()


def get_s3_client():
    """Create an S3 client configured for MinIO or Cloudflare R2."""
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        region_name="us-east-1",
    )


async def upload_video(file_content: bytes, filename: str, content_type: str = "video/mp4") -> str:
    """Upload a video file to S3-compatible storage, return the object key."""
    s3 = get_s3_client()
    ext = filename.rsplit(".", 1)[-1] if "." in filename else "mp4"
    key = f"videos/{uuid.uuid4()}.{ext}"

    s3.put_object(
        Bucket=settings.S3_BUCKET_VIDEOS,
        Key=key,
        Body=file_content,
        ContentType=content_type,
    )
    return key


async def upload_thumbnail(file_content: bytes, filename: str, content_type: str = "image/jpeg") -> str:
    """Upload a thumbnail to S3-compatible storage, return the object key."""
    s3 = get_s3_client()
    ext = filename.rsplit(".", 1)[-1] if "." in filename else "jpg"
    key = f"thumbnails/{uuid.uuid4()}.{ext}"

    s3.put_object(
        Bucket=settings.S3_BUCKET_THUMBNAILS,
        Key=key,
        Body=file_content,
        ContentType=content_type,
    )
    return key


def get_video_url(key: str) -> str:
    """Get public URL for a video."""
    return f"{settings.S3_PUBLIC_URL}/{settings.S3_BUCKET_VIDEOS}/{key}"


def get_thumbnail_url(key: str) -> str:
    """Get public URL for a thumbnail."""
    return f"{settings.S3_PUBLIC_URL}/{settings.S3_BUCKET_THUMBNAILS}/{key}"


def download_video(key: str) -> bytes:
    """Download a video from S3-compatible storage."""
    s3 = get_s3_client()
    response = s3.get_object(Bucket=settings.S3_BUCKET_VIDEOS, Key=key)
    return response["Body"].read()


def upload_audio(file_content: bytes, filename: str) -> str:
    """Upload an audio file, return the object key."""
    ext = filename.rsplit(".", 1)[-1] if "." in filename else "mp3"
    key = f"audio/{uuid.uuid4()}.{ext}"

    try:
        s3 = get_s3_client()
        s3.put_object(
            Bucket=settings.S3_BUCKET_VIDEOS,
            Key=key,
            Body=file_content,
            ContentType=f"audio/{ext}",
        )
        return key
    except Exception:
        local_path = Path(settings.LOCAL_STORAGE_DIR) / key
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(file_content)
        return f"local/{key}"


def get_audio_url(key: str) -> str:
    """Get public URL for an audio file."""
    if key.startswith("local/"):
        return f"{settings.LOCAL_STORAGE_PUBLIC_URL}/{key.removeprefix('local/')}"
    return f"{settings.S3_PUBLIC_URL}/{settings.S3_BUCKET_VIDEOS}/{key}"
