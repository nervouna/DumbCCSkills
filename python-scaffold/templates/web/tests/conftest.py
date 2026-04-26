import pytest
from fastapi.testclient import TestClient

from {{project_name_snake}}.app import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)
