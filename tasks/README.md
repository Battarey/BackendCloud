# Description of the tasks folder

The `tasks` folder contains background tasks executed via Celery.

## Main tasks
- **scan.py** — antivirus scanning of files after downloading (ClamAV, pyclamd)
- **cleanup.py** — automatic deletion of files from the trash that were marked as deleted more than 24 hours ago (MinIO + DB)

## Starting Celery worker and beat
- Worker:
```powershell
celery -A tasks.scan.celery_app worker --loglevel=info
```
- Beat (periodic tasks):
```powershell
celery -A tasks.cleanup.celery_app beat --loglevel=info
```
- Via Docker Compose (recommended):
```powershell
docker-compose up -d celery_worker celery_beat
```

## Notes
- All settings (paths to services, keys, ports) are taken from environment variables via app.config
- Redis, MinIO, ClamAV and PostgreSQL are required for correct operation

---