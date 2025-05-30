import sqlalchemy as sa
from sqlalchemy.types import TypeDecorator, CHAR
import uuid

class GUID(TypeDecorator):
    # Platform-independent UUID type.
    # Uses PostgreSQL UUID, and for SQLite stores it as a string.
    impl = CHAR
    cache_ok = True

    # Determines the column type depending on the dialect (PostgreSQL or SQLite)
    def load_dialect_impl(
        self, 
        dialect
    ):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(sa.dialects.postgresql.UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    # Converts UUID value for DB entry
    def process_bind_param(
        self,
        value, 
        dialect
    ):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            else:
                return str(value)

    # Converts a value from the DB back to a UUID
    def process_result_value(
        self, 
        value, 
        dialect
    ):
        if value is None:
            return value
        return uuid.UUID(value)