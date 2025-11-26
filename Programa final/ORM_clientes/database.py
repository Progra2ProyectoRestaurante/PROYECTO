# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


import os
# Ruta absoluta a restaurante.db dentro de la carpeta ORM_clientes
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'restaurante.db')}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()
