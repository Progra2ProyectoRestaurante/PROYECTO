# main.py
from database import SessionLocal
from models import crear_base

from Restaurante import RestauranteApp
from logic.Menu import poblar_db_con_menus_estaticos

def main():
    # Crear BD si no existe
    crear_base()

    # Crear sesión
    db = SessionLocal()

    # Poblar la base de datos con menús e ingredientes estátiscos si es necesario
    poblar_db_con_menus_estaticos(db)

    # Crear y ejecutar la aplicación principal
    app = RestauranteApp(db=db)
    app.mainloop()

if __name__ == "__main__":
    main()
