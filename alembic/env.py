import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

# Load .env
load_dotenv()

# this is the Alembic Config object, which provides access to .ini
config = context.config

# Override sqlalchemy.url from .env
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))

# Logging setup
fileConfig(config.config_file_name)

# Import your Base and models so Alembic can see them
from app.models.database import Base
# Import all models here so they are registered with Base
# Example:
# from app.models.user import User
# from app.models.skill import Skill
# from app.models.session import Session

target_metadata = Base.metadata

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
