from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

import os
import sys
from app.db.database import Base # Import Base from project

# Import all models so Base can "see" them
from app.models.user import User
from app.models.user_session import UserSession
from app.models.user_activity_log import UserActivityLog
from app.models.user_settings import UserSettings
from app.models.password_reset_token import PasswordResetToken
from app.models.file import File
from app.models.file_encryption import FileEncryption
from app.models.folder import Folder

# Add the path to the project root (BackEnd folder) so that Alembic can find the app module
# The path is relative to the alembic folder, so '..'
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# --- NEW: Read DB connection details from environment variables ---
db_user = os.environ.get("POSTGRES_USER", "postgres")
db_password = os.environ.get("POSTGRES_PASSWORD", "postgres")
# Имя хоста берем 'db' - имя сервиса в docker-compose
db_host = "db"
db_port = "5432"
# Имя БД берем из переменной или по умолчанию
db_name = os.environ.get("POSTGRES_DB", "battareycloud")

# Construct the URL for Alembic (using psycopg2)
alembic_db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Set the sqlalchemy.url in the config object Alembic uses
config.set_main_option("sqlalchemy.url", alembic_db_url)
# --- END NEW ---

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    #Run migrations in 'offline' mode.

    #This configures the context with just a URL
    #and not an Engine, though an Engine is acceptable
    #here as well.  By skipping the Engine creation
    #we don't even need a DBAPI to be available.

    #Calls to context.execute() here emit the given string to the
    #script output.


    # Use the URL we set in config
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # engine_from_config will now use the URL set in config
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
