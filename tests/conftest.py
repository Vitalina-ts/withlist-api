import importlib
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session


@pytest.fixture(scope="session")
def api():
    # Only suppress import-time DDL. Production startup remains unchanged.
    # Import database first so its engine can never connect during this import.
    import database

    with patch.object(database.engine, "connect", side_effect=AssertionError("Unexpected DB access")):
        with patch.object(database.Base.metadata, "create_all"):
            module = importlib.import_module("main")
    return module


@pytest.fixture
def client(api):
    with TestClient(api.app) as test_client:
        yield test_client


@pytest.fixture
def postgres_session(api):
    from database import DATABASE_URL
    from models import Base

    admin = create_engine(DATABASE_URL)
    schema = "ci_" + uuid4().hex
    schema_created = False
    try:
        assert admin.dialect.name == "postgresql"
        with admin.begin() as connection:
            version = connection.scalar(text("SELECT version()"))
            assert "PostgreSQL" in version
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        schema_created = True
        isolated = create_engine(
            DATABASE_URL,
            connect_args={"options": f"-csearch_path={schema}"},
        )
        try:
            Base.metadata.create_all(isolated)
            with Session(isolated) as session:
                yield session
        finally:
            isolated.dispose()
    finally:
        # Only remove this fixture's UUID schema, never public tables or volumes.
        try:
            if schema_created:
                with admin.begin() as connection:
                    connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        finally:
            admin.dispose()
