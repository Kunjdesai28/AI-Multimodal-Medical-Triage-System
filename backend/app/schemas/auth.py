"""
Pydantic Schemas for Healthcare Institution Authentication & Onboarding.
"""
from pydantic import BaseModel, Field, EmailStr, model_validator
from typing import Optional, Dict, Any


class LocationData(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    placeId: Optional[str] = None


class InstitutionRegisterRequest(BaseModel):
    # SECTION 1: Exact 11 Organization fields
    hospitalName: Optional[str] = Field(None, min_length=1, max_length=150, description="Hospital or Clinic Name")
    organizationType: Optional[str] = Field(None, description="Hospital, Clinic, Diagnostic Center")
    registrationNumber: Optional[str] = Field(None, max_length=100, description="Registration / License Number")
    country: Optional[str] = Field("India", max_length=80)
    state: Optional[str] = Field(None, max_length=80)
    city: Optional[str] = Field(None, max_length=80)
    address: Optional[str] = Field(None, max_length=500)
    pincode: Optional[str] = Field(None, max_length=20)
    contactNumber: Optional[str] = Field(None, max_length=30)
    officialEmail: Optional[str] = Field(None, max_length=150)
    website: Optional[str] = Field(None, max_length=200)

    # Optional Google Maps location metadata
    location: Optional[LocationData] = None

    # Legacy fields supported for backwards compatibility
    institutionName: Optional[str] = None
    institutionType: Optional[str] = None
    officialPhone: Optional[str] = None
    postalCode: Optional[str] = None
    timezone: Optional[str] = None
    administratorName: Optional[str] = None
    administratorDesignation: Optional[str] = None
    administratorEmail: Optional[str] = None
    administratorPhone: Optional[str] = None
    institutionId: Optional[str] = None
    password: Optional[str] = None
    confirmPassword: Optional[str] = None
    termsAccepted: Optional[bool] = True

    @model_validator(mode='before')
    @classmethod
    def reconcile_fields(cls, data: Any):
        if isinstance(data, dict):
            h_name = data.get("hospitalName") or data.get("institutionName")
            if h_name:
                data["hospitalName"] = h_name
                data["institutionName"] = h_name

            org_type = data.get("organizationType") or data.get("institutionType")
            if org_type:
                data["organizationType"] = org_type
                data["institutionType"] = org_type

            contact = data.get("contactNumber") or data.get("officialPhone")
            if contact:
                data["contactNumber"] = contact
                data["officialPhone"] = contact

            pin = data.get("pincode") or data.get("postalCode")
            if pin:
                data["pincode"] = pin
                data["postalCode"] = pin

            if not data.get("country"):
                data["country"] = "India"
        return data


class InstitutionLoginRequest(BaseModel):
    identifier: str = Field(..., min_length=2, max_length=120, description="Institution ID, Username, or Official Email")
    password: str = Field(..., min_length=1, max_length=100)
    rememberMe: Optional[bool] = False


class ForgotPasswordRequest(BaseModel):
    identifier: str = Field(..., min_length=2, max_length=120, description="Official Email or Institution ID")


class InstitutionResponse(BaseModel):
    id: str
    institutionId: str
    institutionName: str
    hospitalName: Optional[str] = None
    institutionType: str
    organizationType: Optional[str] = None
    registrationNumber: Optional[str] = None
    officialEmail: str
    officialPhone: Optional[str] = None
    contactNumber: Optional[str] = None
    website: Optional[str] = None
    country: str
    state: str
    city: str
    postalCode: Optional[str] = None
    pincode: Optional[str] = None
    address: str
    timezone: Optional[str] = None
    administratorName: Optional[str] = None
    administratorDesignation: Optional[str] = None
    administratorEmail: Optional[str] = None
    accountStatus: str = "active"
    createdAt: str
    location: Optional[Dict[str, Any]] = None


class AuthTokenResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    institution: Optional[InstitutionResponse] = None
    message: str

