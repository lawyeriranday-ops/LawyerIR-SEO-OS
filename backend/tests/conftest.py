import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.main import app
from app.models.base import Base


@compiles(UUID, "sqlite")
def _compile_uuid_sqlite(type_, compiler, **kw):
    return "VARCHAR(36)"


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite://")


@pytest.fixture(scope="session")
def engine():
    connect_args = {}
    poolclass = None
    if TEST_DATABASE_URL.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        poolclass = StaticPool

    test_engine = create_engine(
        TEST_DATABASE_URL,
        connect_args=connect_args,
        poolclass=poolclass,
    )

    if not TEST_DATABASE_URL.startswith("sqlite"):
        try:
            with test_engine.connect() as conn:
                conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        except Exception as exc:
            pytest.skip(f"PostgreSQL test database unavailable: {exc}")

    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def seed_user(client):
    response = client.post(
        "/api/v1/users",
        json={
            "email": "admin@lawyerir.com",
            "username": "admin",
            "password": "securepass123",
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def seed_site(client):
    response = client.post(
        "/api/v1/sites",
        json={"url": "https://lawyerir.com", "name": "LawyerIR"},
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def seed_url(client, seed_site):
    response = client.post(
        f"/api/v1/sites/{seed_site['id']}/urls",
        json={
            "path": "/",
            "full_url": "https://lawyerir.com/",
            "title": "LawyerIR Home",
        },
    )
    assert response.status_code == 201
    return response.json()
