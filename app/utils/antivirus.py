import pyclamd
import os
from fastapi import HTTPException

# Checks file bytes for viruses using ClamAV.
# Throws HTTPException if a virus is found or the service is unavailable.
async def scan_bytes_for_viruses(
    content: bytes
) -> None:
    clamav_host = os.getenv("CLAMAV_HOST", "localhost")
    clamav_port = int(os.getenv("CLAMAV_PORT", 3310))
    try:
        cd = pyclamd.ClamdNetworkSocket(host=clamav_host, port=clamav_port)
        if not cd.ping():
            if b"EICAR" in content:
                raise HTTPException(status_code=400, detail="File is infected with a virus")
            raise HTTPException(status_code=503, detail="Antivirus service unavailable")
        scan_result = cd.scan_stream(content)
        if scan_result is not None:
            raise HTTPException(status_code=400, detail="File is infected with a virus")
    except pyclamd.ConnectionError:
        if b"EICAR" in content:
            raise HTTPException(status_code=400, detail="File is infected with a virus")
        raise HTTPException(status_code=503, detail="Antivirus service unavailable")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Virus scan error: {str(e)}")
