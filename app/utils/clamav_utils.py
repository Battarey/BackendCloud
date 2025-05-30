import pyclamd
import os
from fastapi import HTTPException

CLAMAV_HOST = os.getenv("CLAMAV_HOST", "clamav")
CLAMAV_PORT = int(os.getenv("CLAMAV_PORT", 3310))

# Performs antivirus scanning of transferred bytes using ClamAV
async def scan_bytes(
    data: bytes
) -> bool:
    try:
        cd = pyclamd.ClamdNetworkSocket(host=CLAMAV_HOST, port=CLAMAV_PORT)
        result = cd.scan_stream(data)
        return result is None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ClamAV error: {e}")