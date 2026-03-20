import pytest
from uuid import uuid4
from fastapi import HTTPException
from app.deps import get_tenant_id
from app.models import AppUser, FileUpload

def test_tenant_scoping_logic():
    tenant_a = uuid4()
    tenant_b = uuid4()
    
    user_a = AppUser(id=uuid4(), email="a@a.com", hashed_password="...", tenant_id=tenant_a)
    
    # Simulating a resource check
    resource_of_b = FileUpload(
        id=uuid4(),
        tenant_id=tenant_b,
        original_filename="secret.csv",
        file_type="bank",
        storage_path="/tmp/b"
    )
    
    # Logic we want to enforce in our app
    def check_access(resource, user_tenant_id):
        if resource.tenant_id != user_tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        return True

    with pytest.raises(HTTPException) as excinfo:
        check_access(resource_of_b, get_tenant_id(user_a))
    
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "Access denied"
