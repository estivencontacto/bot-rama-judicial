from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class OrganizacionRead(BaseModel):
    id: int
    nombre: str
    limite_radicados: int
    activa: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class OrganizacionUpdate(BaseModel):
    nombre: str = Field(min_length=2, max_length=160)
    limite_radicados: int = Field(default=500, ge=1, le=100000)
    activa: bool = True


class UsuarioRead(BaseModel):
    id: int
    email: EmailStr
    nombre: str
    rol: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UsuarioCreate(BaseModel):
    email: EmailStr
    nombre: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=120)
    rol: str = "operador"


class UsuarioUpdate(BaseModel):
    nombre: str | None = None
    rol: str | None = None
    is_active: bool | None = None
