from sqlalchemy import Column, Integer, String, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    correo = Column(String, unique=True, nullable=False)
    telefono = Column(String)

    modelos = relationship("Modelo3D", back_populates="usuario")
    calificaciones = relationship("Calificacion", back_populates="usuario")

class Categoria(Base):
    __tablename__ = "categorias"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(Text)

    modelos = relationship("Modelo3D", back_populates="categoria")

class Modelo3D(Base):
    __tablename__ = "modelos"
    id = Column(Integer, primary_key=True, index=True)
    nombre_archivo = Column(String, nullable=False)
    descripcion = Column(Text)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"))
    id_categoria = Column(Integer, ForeignKey("categorias.id"))

    usuario = relationship("Usuario", back_populates="modelos")
    categoria = relationship("Categoria", back_populates="modelos")
    calificaciones = relationship("Calificacion", back_populates="modelo")

class Calificacion(Base):
    __tablename__ = "calificaciones"
    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"))
    id_modelo = Column(Integer, ForeignKey("modelos.id"))
    puntuacion = Column(Float, nullable=False)
    comentario = Column(Text)

    usuario = relationship("Usuario", back_populates="calificaciones")
    modelo = relationship("Modelo3D", back_populates="calificaciones")
