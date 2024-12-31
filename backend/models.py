from sqlalchemy import Column, Integer, String, Table
from database import metadata

# Дефиниция на таблицата "garages"
garages = Table(
    "garages",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("name", String, nullable=False),
    Column("location", String, nullable=False),
    Column("city", String, nullable=False),
    Column("capacity", Integer, nullable=False),
)

# models.py

from pydantic import BaseModel
from typing import List, Optional

# Pydantic модел за създаване на автомобил
class CarCreate(BaseModel):
    make: str
    model: str
    productionYear: int
    licensePlate: str
    garages: List[int]  # Списък с ID на гаражи, в които е регистриран автомобилът

# Pydantic модел за връщане на автомобил
class Car(CarCreate):
    id: int



# models.py

from sqlalchemy import Table, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import metadata

# SQLAlchemy модел за автомобил
cars = Table(
    "cars",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("make", String, index=True),
    Column("model", String),
    Column("productionYear", Integer),
    Column("licensePlate", String, unique=True),
)

# Връзка към гаражи (множество към множество)
# Необходимо е да добавим таблица за асоциации между автомобили и гаражи
car_garage_association = Table(
    "car_garage_association",
    metadata,
    Column("car_id", Integer, ForeignKey("cars.id")),
    Column("garage_id", Integer, ForeignKey("garages.id")),
)


