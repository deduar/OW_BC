import pytest
from uuid import uuid4
from app.deps import get_tenant_id
from app.models import AppUser

def test_get_tenant_id_returns_user_tenant():
    tenant_id = uuid4()
    mock_user = AppUser(
        id=uuid4(),
        email="test@example.com",
        hashed_password="...",
        tenant_id=tenant_id
    )
    
    result = get_tenant_id(mock_user)
    assert result == tenant_id
