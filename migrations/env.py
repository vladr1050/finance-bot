from logging.config import fileConfig
from sqlalchemy import create_engine
from alembic import context

from db.database import DATABASE_URL
from db.models import Base

# Alembic config
config = context.config
fileConfig(config.config_file_name)

# Add model metadata
target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # important for detecting column type changes
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode using sync SQLAlchemy engine."""
    connectable = create_engine(DATABASE_URL.replace("postgresql+asyncpg", "postgresql"))

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # important!
        )

        with context.begin_transaction():
            context.run_migrations()

# 🔁 Run the correct method depending on mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
