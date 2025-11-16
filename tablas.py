from pydantic import BaseModel
from typing import Optional

# === USUARIOS ===
class UsuarioBase(BaseModel):
    nombre: str
    correo: str
    telefono: Optional[str] = None

class UsuarioCreate(UsuarioBase):
    pass

class Usuario(UsuarioBase):
    id: int
    class Config:
        orm_mode = True

# === CATEGORÍAS ===
class Categoria(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    class Config:
        orm_mode = True

# === MODELOS ===
class Modelo(BaseModel):
    id: int
    nombre_archivo: str
    descripcion: Optional[str]
    id_usuario: int
    id_categoria: int
    class Config:
        orm_mode = True

# === CALIFICACIONES ===
class CalificacionBase(BaseModel):
    puntuacion: float
    comentario: Optional[str] = None

class CalificacionCreate(CalificacionBase):
    id_usuario: int
    id_modelo: int

class Calificacion(CalificacionBase):
    id: int
    id_usuario: int
    id_modelo: int
    class Config:
        orm_mode = True

class Login(BaseModel):
    nombre: str
    correo: str
