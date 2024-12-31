from pydantic import BaseModel  # Трябва да добавите този импорт
from typing import List
from sqlalchemy import Table, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import metadata

# Таблица за гаражи
garages = Table(
    "garages", 
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("name", String, index=True),
    Column("location", String),
    Column("city", String),
    Column("capacity", Integer)
)

# Таблица за автомобили
cars = Table(
    "cars",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("make", String, index=True),
    Column("model", String),
    Column("productionYear", Integer),
    Column("licensePlate", String, unique=True)
)

# Ассоциация между автомобили и гаражи
car_garage_association = Table(
    "car_garage_association",
    metadata,
    Column("car_id", Integer, ForeignKey("cars.id")),
    Column("garage_id", Integer, ForeignKey("garages.id"))
)

# Pydantic модел за създаване на автомобил
class CarCreate(BaseModel):
    make: str
    model: str
    productionYear: int
    licensePlate: str
    garages: List[int]  # Списък с ID-та на гаражи, в които е регистриран автомобилът

    class Config:
        orm_mode = True  # Това позволява на Pydantic да работи със SQLAlchemy модели

# Pydantic модел за създаване на гараж
class GarageCreate(BaseModel):
    name: str
    location: str
    city: str
    capacity: int

    class Config:
        orm_mode = True  # Това позволява на Pydantic да работи със SQLAlchemy модели
