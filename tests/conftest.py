"""Pytest fixtures and test environment setup."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from app.api.dependencies import get_db, get_llm_provider_dep, get_tool_registry_dep
from app.db.models import Base
from app.llm.mock import MockLLMProvider
from app.main import app
from app.tools.registry import ToolRegistry, get_default_registry

# In-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all database schema tables once per test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Provide isolated database session per test function with auto-rollback."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def mock_llm():
    """Provide deterministic MockLLMProvider."""
    return MockLLMProvider()


@pytest.fixture
def tool_registry():
    """Provide default tool registry with calculator."""
    return get_default_registry()


@pytest.fixture
def client(db_session, mock_llm, tool_registry):
    """FastAPI TestClient with overridden dependencies."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_llm_provider_dep] = lambda: mock_llm
    app.dependency_overrides[get_tool_registry_dep] = lambda: tool_registry

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
