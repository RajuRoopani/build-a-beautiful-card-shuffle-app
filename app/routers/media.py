"""Media router — implements file upload for posts.

⚠️  DEAD CODE — NOT WIRED INTO main.py ⚠️
This router is NOT registered with the FastAPI app and is not part of the
current acceptance criteria. Do NOT import or test it until it is explicitly
added to main.py. The models it references (generate_id, MediaResponse,
media_db) do not exist in app/models.py in their expected form.

AC6:  POST /media/upload — upload image/video (multipart form, 201)
      Rejects files > 10MB with 400.
      Only accepts: image/jpeg, image/png, image/gif, video/mp4, video/webm.
      Returns {media_id, media_url} where media_url = /media/{media_id}/{filename}.
      Stores entry in media_db.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.models import generate_id, MediaResponse

router = APIRouter(tags=["Media"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB in bytes

ALLOWED_CONTENT_TYPES: set[str] = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "video/mp4",
    "video/webm",
}

# In-memory media storage: media_id -> media dict
# Imported lazily to survive architect's models.py update that adds media_db.
# If media_db exists in models, use it; otherwise fall back to a local dict.
try:
    from app.models import media_db  # type: ignore[attr-defined]
except ImportError:
    media_db: dict = {}  # type: ignore[assignment]


@router.post("/media/upload", status_code=201)
async def upload_media(file: UploadFile = File(...)) -> dict:
    """Upload a media file. Returns media_id and a simulated media_url.

    Validations:
    - MIME type must be one of the ALLOWED_CONTENT_TYPES.
    - File size must not exceed 10 MB.
    """
    # Validate MIME type first (cheap check before reading file)
    content_type = file.content_type or ""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{content_type}'. "
                f"Allowed types: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}"
            ),
        )

    # Read file content to check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size {len(content)} bytes exceeds the 10 MB limit",
        )

    # Generate ID and construct simulated URL
    media_id = generate_id()
    filename = file.filename or "upload"
    media_url = f"/media/{media_id}/{filename}"

    # Store in media_db
    media_db[media_id] = {
        "media_id": media_id,
        "filename": filename,
        "content_type": content_type,
        "media_url": media_url,
        "size": len(content),
    }

    return {"media_id": media_id, "media_url": media_url}
