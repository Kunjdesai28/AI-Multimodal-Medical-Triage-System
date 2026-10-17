"""
Authentication & Multi-Tenant Dependency Resolvers.
Enforces strict database isolation: resolves the operating tenant database
directly from the verified cryptographically signed session token.
"""
from fastapi import Header, HTTPException, status
from typing import Optional

from ..auth.security import decode_access_token
from ..database.repository import MasterRepository, TenantRepository, TriageRepository


class TenantContext:
    def __init__(self, institution_id: str, database_name: str, institution_name: str, email: str, role: str):
        self.institution_id = institution_id
        self.database_name = database_name
        self.institution_name = institution_name
        self.email = email
        self.role = role
        self.repo = TenantRepository(database_name)


def get_tenant_context(authorization: Optional[str] = Header(None)) -> TenantContext:
    """
    STRICT TENANT ISOLATION:
    Extracts and validates institutional session token.
    Resolves dedicated databaseName strictly from master database / token claims.
    Never trusts client-supplied institutionId or databaseName.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access clinical institution data."
        )

    token = authorization.split("Bearer ")[1].strip()
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Institutional session token has expired or is invalid. Please sign in again."
        )

    institution_id = payload["sub"]

    # Resolve databaseName from master registry
    master = MasterRepository()
    inst = master.get_institution_by_identifier(institution_id)
    if not inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registered institution workspace not found."
        )

    database_name = inst.get("databaseName")
    if not database_name:
        database_name = f"triageai_clinic_{institution_id}"

    return TenantContext(
        institution_id=institution_id,
        database_name=database_name,
        institution_name=inst.get("institutionName", "Hospital"),
        email=inst.get("officialEmail", ""),
        role="Institution Administrator"
    )


def get_tenant_context_optional(authorization: Optional[str] = Header(None)) -> TenantContext:
    """
    Fallback resolver: if token is present, resolves dedicated tenant;
    if absent, uses default demonstration clinic without throwing 401.
    """
    if authorization and authorization.startswith("Bearer "):
        try:
            return get_tenant_context(authorization)
        except Exception:
            pass

    return TenantContext(
        institution_id="default_clinic",
        database_name="triageai_clinic_default",
        institution_name="Demo Emergency Center",
        email="demo@triageai.org",
        role="Viewer"
    )
