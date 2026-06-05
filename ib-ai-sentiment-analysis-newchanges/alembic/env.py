import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv
from urllib.parse import quote_plus

# CRITICAL: Force override system env vars with .env values
load_dotenv(override=True)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None

def get_database_url():
    """Build URL from .env variables with proper encoding"""
    user = os.getenv('USER')
    password = quote_plus(os.getenv('PASSWORD'))
    host = os.getenv('HOST')
    port = os.getenv('PORT', '5432')
    db_name = os.getenv('DB_NAME')
    
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"

def run_migrations_offline():
    context.configure(url=get_database_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = get_database_url()
    connectable = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
