# sqlalchemy
from sqlalchemy import update
# app
from app.db.database import SessionLocal # Use SessionLocal to create sessions in the task
from app.models.file import File as FileModel
from app.utils.minio_utils import MINIO_BUCKET
from app.utils.minio_async import get_object_async
from app.config import celery_app
# other
from uuid import UUID
import logging
import os
import pyclamd

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60) 
async def scan_file_task(
    self, 
    file_id_str: str, 
    object_name: str
):
    # Celery background task to scan a file for viruses after upload.
    # Updates the is_infected flag in the DB if a virus is found.
    logger.info(f"Starting virus scan for file_id: {file_id_str}, object_name: {object_name}")
    file_id = UUID(file_id_str)
    # Use service name 'clamav' as default host in Docker
    clamav_host = os.getenv("CLAMAV_HOST", "clamav")
    clamav_port = int(os.getenv("CLAMAV_PORT", 3310))
    cd = None
    response = None

    try:
        # 1. Connecting to ClamAV
        try:
            cd = pyclamd.ClamdNetworkSocket(host=clamav_host, port=clamav_port)
            if not cd.ping():
                logger.warning(f"ClamAV service at {clamav_host}:{clamav_port} is not responding. Retrying...")
                # Using ConnectionError for clarity
                raise ConnectionError("ClamAV ping failed")
        except Exception as clam_err:
            logger.error(f"Failed to connect to ClamAV: {clam_err}. Retrying task...")
            # Repeat the task if there is a connection error
            raise self.retry(exc=clam_err)

        # 2. Getting a file from MinIO (async)
        try:
            file_content = await get_object_async(MINIO_BUCKET, object_name)
        except Exception as minio_err:
            logger.error(f"Failed to get object {object_name} from MinIO: {minio_err}")
            # Do not repeat the task if the file is not in MinIO - this is not a temporary error
            return # Completing the task

        # 3. Scanning
        scan_result = cd.scan_stream(file_content)
        is_infected = scan_result is not None
        if is_infected:
            # Get the virus name from the result
            virus_name = scan_result.get('stream', ('UNKNOWN', 'UNKNOWN'))[1]
            logger.warning(f"Virus found in file_id: {file_id}, object_name: {object_name}. Virus: {virus_name}")
        else:
            logger.info(f"File is clean: file_id: {file_id}, object_name: {object_name}")

        # 4. Updating the status in the database (only if a virus is found)
        if is_infected:
            # Using SessionLocal to create an asynchronous session
            async with SessionLocal() as db:
                try:
                    stmt = (
                        update(FileModel)
                        .where(FileModel.id == file_id)
                        .values(is_infected=True)
                        # Allows to get the update result if the DBMS supports RETURNING
                        # .returning(FileModel.id)
                    )
                    result = await db.execute(stmt)
                    await db.commit()
                    # Check if at least one row has been updated
                    if result.rowcount == 0:
                         logger.warning(f"File with id {file_id} not found in DB during infection status update.")
                    else:
                         logger.info(f"Marked file {file_id} as infected in DB.")
                except Exception as db_err:
                    logger.error(f"Failed to update infection status for file {file_id} in DB: {db_err}")
                    # You can add retry for DB errors too, if they can be temporary
                    # raise self.retry(exc=db_err)
    
    except Exception as e: # Log unexpected errors but don't retry the task to avoid loops
        logger.exception(f"Unhandled error in scan_file_task for file {file_id}: {e}")
