from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os, shutil
from typing import List

from database import SessionLocal, engine
from models import Base, Usuario as UsuarioDB, Categoria as CategoriaDB, Modelo3D, Calificacion as CalificacionDB
from tablas import UsuarioCreate, Usuario, Categoria, Modelo, CalificacionCreate, Calificacion, Login
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Inicializar la aplicación FastAPI
app = FastAPI(title="API de Modelos 3D", version="2.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # para pruebas; en producción restringir al dominio del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carpeta para subir archivos
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Carpeta estática
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dependencia de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Página principal
@app.get("/", response_class=HTMLResponse)
def inicio():
    return "<h2>API de Modelos 3D</h2><p>Desarrollada con FastAPI</p>"

# === USUARIOS ===
@app.post("/usuarios/", response_model=Usuario)
def crear_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    nuevo = UsuarioDB(**usuario.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@app.get("/usuarios/", response_model=List[Usuario])
def listar_usuarios(db: Session = Depends(get_db)):
    return db.query(UsuarioDB).all()

@app.get("/usuarios/{id_usuario}/modelos", response_model=List[Modelo])
def modelos_por_usuario(id_usuario: int, db: Session = Depends(get_db)):
    return db.query(Modelo3D).filter(Modelo3D.id_usuario == id_usuario).all()

# === CATEGORÍAS ===
@app.get("/categorias/", response_model=List[Categoria])
def listar_categorias(db: Session = Depends(get_db)):
    return db.query(CategoriaDB).all()

@app.get("/categorias/{id}/modelos", response_model=List[Modelo])
def modelos_por_categoria(id: int, db: Session = Depends(get_db)):
    return db.query(Modelo3D).filter(Modelo3D.id_categoria == id).all()

# === MODELOS 3D ===
@app.post("/subir_modelo/")
async def subir_modelo(
    file: UploadFile = File(...),
    descripcion: str = "",
    id_usuario: int = None,
    id_categoria: int = None,
    db: Session = Depends(get_db)
):
    if id_usuario is None:
        raise HTTPException(status_code=400, detail="Falta el parámetro id_usuario")

    usuario = db.query(UsuarioDB).filter(UsuarioDB.id == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if id_categoria is None:
        id_categoria = 1

    categoria = db.query(CategoriaDB).filter(CategoriaDB.id == id_categoria).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Archivo inválido o vacío")

    ruta = os.path.join(UPLOAD_DIR, file.filename)
    with open(ruta, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    nuevo = Modelo3D(
        nombre_archivo=file.filename,
        descripcion=descripcion,
        id_usuario=id_usuario,
        id_categoria=id_categoria
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    return {
        "mensaje": "Modelo subido correctamente",
        "id": nuevo.id,
        "archivo": nuevo.nombre_archivo,
        "usuario": usuario.nombre
    }

@app.get("/modelos/", response_model=List[Modelo])
def listar_modelos(db: Session = Depends(get_db)):
    return db.query(Modelo3D).all()

@app.get("/archivos/{nombre}")
def obtener_archivo(nombre: str):
    ruta = os.path.join(UPLOAD_DIR, nombre)
    if os.path.exists(ruta):
        return FileResponse(ruta)
    raise HTTPException(status_code=404, detail="Archivo no encontrado")

@app.delete("/eliminar_modelo/{id}")
def eliminar_modelo(id: int, db: Session = Depends(get_db)):
    modelo = db.query(Modelo3D).filter(Modelo3D.id == id).first()
    if not modelo:
        raise HTTPException(status_code=404, detail="Modelo no encontrado")
    ruta = os.path.join(UPLOAD_DIR, modelo.nombre_archivo)
    if os.path.exists(ruta):
        os.remove(ruta)
    db.delete(modelo)
    db.commit()
    return {"mensaje": "Modelo eliminado correctamente"}

# === CALIFICACIONES ===
@app.post("/calificaciones/")
def crear_calificacion(cal: CalificacionCreate, db: Session = Depends(get_db)):
    modelo = db.query(Modelo3D).filter_by(id=cal.id_modelo).first()
    usuario = db.query(UsuarioDB).filter_by(id=cal.id_usuario).first()
    if not modelo or not usuario:
        raise HTTPException(status_code=404, detail="Modelo o usuario no encontrado")

    existente = db.query(CalificacionDB).filter_by(id_modelo=cal.id_modelo, id_usuario=cal.id_usuario).first()
    if existente:
        existente.puntuacion = cal.puntuacion
        existente.comentario = cal.comentario
    else:
        nueva = CalificacionDB(**cal.dict())
        db.add(nueva)
    db.commit()
    return {"mensaje": "Calificación registrada correctamente"}

@app.get("/calificaciones/{id_modelo}")
def obtener_calificaciones(id_modelo: int, db: Session = Depends(get_db)):
    calificaciones = db.query(CalificacionDB).filter_by(id_modelo=id_modelo).all()
    if not calificaciones:
        return {"promedio": 0, "total": 0, "calificaciones": []}
    promedio = sum(c.puntuacion for c in calificaciones) / len(calificaciones)
    return {
        "id_modelo": id_modelo,
        "promedio": round(promedio, 2),
        "total": len(calificaciones),
        "calificaciones": [
            {"usuario": c.usuario.nombre, "puntuacion": c.puntuacion, "comentario": c.comentario}
            for c in calificaciones
        ]
    }

# === RANKING DE MODELOS ===
@app.get("/ranking/")
def obtener_ranking(db: Session = Depends(get_db)):
    modelos = db.query(Modelo3D).all()
    ranking = []

    for modelo in modelos:
        calificaciones = db.query(CalificacionDB).filter(CalificacionDB.id_modelo == modelo.id).all()
        if calificaciones:
            promedio = sum(c.puntuacion for c in calificaciones) / len(calificaciones)
            total = len(calificaciones)
        else:
            promedio = 0
            total = 0

        ranking.append({
            "id_modelo": modelo.id,
            "nombre_modelo": modelo.nombre_archivo,
            "descripcion": modelo.descripcion,
            "categoria": modelo.categoria.nombre if modelo.categoria else "Sin categoría",
            "usuario": modelo.usuario.nombre if modelo.usuario else "Desconocido",
            "promedio": round(promedio, 2),
            "total_calificaciones": total
        })

    ranking.sort(key=lambda x: x["promedio"], reverse=True)
    return ranking

# === LOGIN / REGISTRO AUTOMÁTICO ===
@app.post("/login")
def login(usuario: Login, db: Session = Depends(get_db)):
    existente = db.query(UsuarioDB).filter_by(correo=usuario.correo).first()

    if existente:
        return {
            "mensaje": "Inicio de sesión exitoso",
            "id": existente.id,
            "nombre": existente.nombre,
            "correo": existente.correo
        }

    # Asignar siguiente ID incremental
    last_user = db.query(UsuarioDB).order_by(UsuarioDB.id.desc()).first()
    next_id = 1 if not last_user else last_user.id + 1

    nuevo = UsuarioDB(id=next_id, nombre=usuario.nombre, correo=usuario.correo)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    return {
        "mensaje": "Usuario creado e inicio de sesión",
        "id": nuevo.id,
        "nombre": nuevo.nombre,
        "correo": nuevo.correo
    }
