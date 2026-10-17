"""
Pytest configuration and fixtures.
Provides dependency overrides for institutional tenant auth during testing.
"""
import pytest
from backend.app.main import app
from backend.app.api.deps import get_tenant_context, get_tenant_context_optional


@pytest.fixture(autouse=True)
def override_auth_for_tests():
    """Bypasses strict institution login during automated test runs."""
    app.dependency_overrides[get_tenant_context] = get_tenant_context_optional
    yield
    app.dependency_overrides.clear()
