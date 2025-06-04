from logging.config import fileConfig
from sqlalchemy import create_engine
from alembic import context

from db.database import DATABASE_URL
from db.models import Base

# Alembic config
config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    context.configure(
        url=DATABASE_URL.replace("postgresql+asyncpg", "postgresql"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode using sync SQLAlchemy engine."""
    connectable = create_engine(DATABASE_URL.replace("postgresql+asyncpg", "postgresql"))

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
