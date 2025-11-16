from database import SessionLocal, engine, Base
from models import Categoria

Base.metadata.create_all(bind=engine)

db = SessionLocal()

categorias = [
    (1, "Personas", "Modelos anatómicos o de personajes humanos"),
    (2, "Ropa y accesorios", "Prendas, zapatos, joyas"),
    (3, "Vehículos", "Autos, motos, aviones, barcos"),
    (4, "Animales", "Criaturas, mascotas, fauna"),
    (5, "Plantas", "Vegetación, flores, árboles"),
    (6, "Hogar y muebles", "Cosas domésticas, muebles, utensilios"),
    (7, "Arquitectura", "Edificios, estructuras, interiores"),
    (8, "Tecnología", "Gadgets, robots, maquinaria"),
    (9, "Fantasía y ficción", "Criaturas mágicas, armas, mundos imaginarios"),
    (10, "Misceláneo", "Cualquier otro modelo no clasificable")
]

for id_cat, nombre, desc in categorias:
    if not db.query(Categoria).filter_by(id=id_cat).first():
        db.add(Categoria(id=id_cat, nombre=nombre, descripcion=desc))

db.commit()
db.close()

print("Categorías iniciales cargadas correctamente.")
