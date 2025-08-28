from pathlib import Path
import aiofiles
from fastapi import UploadFile, HTTPException

from gateway.config.settings import MAX_BYTES, CHUNK_SIZE

async def save_upload_nohash(file: UploadFile, raw_path: Path) -> int:
    """
    Stream `file` to `raw_path` in CHUNK_SIZE blocks.
    - O(1) memory usage
    - Enforces MAX_BYTES
    - Writes to .part, then atomically renames on success
    Returns: bytes_written
    """
    tmp_path = raw_path.with_suffix(raw_path.suffix + ".part")
    written = 0

    try:
        async with aiofiles.open(tmp_path, "wb") as out_file:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                written += len(chunk)
                if written > MAX_BYTES:
                    # cleanup partial and reject
                    await aiofiles.os.remove(tmp_path)
                    raise HTTPException(status_code=413, detail="File too large")
                await out_file.write(chunk)

        # finalize
        tmp_path.replace(raw_path)
        return "success"

    except HTTPException:
        # already cleaned in the size-guard path
        raise
    except Exception as e:
        # best-effort cleanup on unexpected errors
        try:
            await aiofiles.os.remove(tmp_path)
        except Exception:
            pass
        raise HTTPException(status_code=400, detail=f"Upload failed: {e}")
