from fastapi import APIRouter, HTTPException
from app.database import get_db_connection
from app.models import (
    LicenseRequest, LicenseCreateRequest, LicenseRevokeRequest,
    LicenseValidationResponse, LicenseCreateResponse, LicenseRevokeResponse
)

router = APIRouter()

# ✅ Validate license
@router.post(
    "/licenses/validate",
    summary="Validate a license",
    response_description="Returns whether a license is valid",
    response_model=LicenseValidationResponse
)
async def validate_license(req: LicenseRequest):
    """
    Validate if a license is active.
    - **license_key**: The license key to validate
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT status FROM licenses WHERE license_key=%s", (req.license_key,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="License not found")

    status = row[0]
    return LicenseValidationResponse(license_key=req.license_key, valid=status == "active")


# ✅ Create license
@router.post(
    "/licenses/create",
    summary="Create a new license",
    response_description="Returns the created license details",
    response_model=LicenseCreateResponse
)
async def create_license(req: LicenseCreateRequest):
    """
    Create a new license for a given user and product.
    - **user_id**: ID of the user
    - **product_id**: ID of the product
    - **expires_at**: Expiration date (ISO format)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO licenses (user_id, product_id, license_key, expires_at, status) "
        "VALUES (%s, %s, UUID(), %s, 'active')",
        (req.user_id, req.product_id, req.expires_at),
    )
    conn.commit()

    cursor.execute("SELECT LAST_INSERT_ID(), license_key FROM licenses ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    return LicenseCreateResponse(id=row[0], license_key=row[1], status="active")


# ✅ Revoke license
@router.post(
    "/licenses/revoke",
    summary="Revoke a license",
    response_description="Returns the revoked license details",
    response_model=LicenseRevokeResponse
)
async def revoke_license(req: LicenseRevokeRequest):
    """
    Revoke an existing license.
    - **license_key**: The license key to revoke
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE licenses SET status='revoked' WHERE license_key=%s", (req.license_key,))
    conn.commit()

    affected = cursor.rowcount
    conn.close()

    if affected == 0:
        raise HTTPException(status_code=404, detail="License not found")

    return LicenseRevokeResponse(license_key=req.license_key, status="revoked")
