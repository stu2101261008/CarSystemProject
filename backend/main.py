from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from models import garages
from database import engine, metadata, DATABASE_URL
from sqlalchemy import select
from databases import Database
from models import cars, car_garage_association, CarCreate, Car
from typing import Optional


# Pydantic модел за валидиране
class GarageCreate(BaseModel):
    name: str
    location: str
    city: str
    capacity: int

# Инициализация
app = FastAPI()
database = Database(DATABASE_URL)

# Създаване на таблиците
metadata.create_all(engine)

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Основен ендпойнт
@app.get("/")
def read_root():
    return {"message": "Welcome to Car Management System API"}

# Създаване на сервиз
@app.post("/garages/", status_code=201)
async def create_garage(garage: GarageCreate):
    query = garages.insert().values(
        name=garage.name,
        location=garage.location,
        city=garage.city,
        capacity=garage.capacity,
    )
    garage_id = await database.execute(query)
    return {
        "id": garage_id,
        "name": garage.name,
        "location": garage.location,
        "city": garage.city,
        "capacity": garage.capacity,
    }

# Извличане на всички сервизи
@app.get("/garages/")
async def read_garages(city: str = None):
    query = select(garages)
    
    if city:
        query = query.where(garages.c.city == city)  # Добавяме филтър по град
    
    garages_list = await database.fetch_all(query)
    return garages_list


# Извличане на конкретен сервиз
@app.get("/garages/{garage_id}")
async def read_garage(garage_id: int):
    query = select(garages).where(garages.c.id == garage_id)
    garage = await database.fetch_one(query)
    if not garage:
        raise HTTPException(status_code=404, detail="Garage not found")
    return garage

# Обновяване на сервиз
@app.put("/garages/{garage_id}")
async def update_garage(garage_id: int, garage: GarageCreate):
    query = select(garages).where(garages.c.id == garage_id)
    existing_garage = await database.fetch_one(query)
    if not existing_garage:
        raise HTTPException(status_code=404, detail="Garage not found")
    update_query = garages.update().where(garages.c.id == garage_id).values(
        name=garage.name, location=garage.location, city=garage.city, capacity=garage.capacity
    )
    await database.execute(update_query)
    return {"id": garage_id, **garage.dict()}

# Изтриване на сервиз
@app.delete("/garages/{garage_id}", status_code=204)
async def delete_garage(garage_id: int):
    query = select(garages).where(garages.c.id == garage_id)
    existing_garage = await database.fetch_one(query)
    if not existing_garage:
        raise HTTPException(status_code=404, detail="Garage not found")
    delete_query = garages.delete().where(garages.c.id == garage_id)
    await database.execute(delete_query)
    return {"message": "Garage deleted"}

from fastapi.middleware.cors import CORSMiddleware

# Добавяне на CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Или заменете със специфичен URL като "http://localhost:3000"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Създаване на автомобил
@app.post("/cars/", status_code=201)
async def create_car(car: CarCreate):
    # Проверка дали автомобил с такава лицензна табела вече съществува
    query = select(cars).where(cars.c.licensePlate == car.licensePlate)
    existing_car = await database.fetch_one(query)
    if existing_car:
        raise HTTPException(status_code=400, detail="Car with this license plate already exists")

    # Въведете автомобила в базата данни
    query = cars.insert().values(
        make=car.make,
        model=car.model,
        productionYear=car.productionYear,
        licensePlate=car.licensePlate,
    )
    car_id = await database.execute(query)

    # Регистрираме автомобила в гаражите
    for garage_id in car.garages:
        query = car_garage_association.insert().values(car_id=car_id, garage_id=garage_id)
        await database.execute(query)

    return {**car.dict(), "id": car_id}


# Извличане на всички автомобили с филтри
@app.get("/cars/")
async def read_cars(make: Optional[str] = None, year_from: Optional[int] = None, year_to: Optional[int] = None):
    query = select(cars)

    if make:
        query = query.where(cars.c.make == make)
    if year_from:
        query = query.where(cars.c.productionYear >= year_from)
    if year_to:
        query = query.where(cars.c.productionYear <= year_to)

    cars_list = await database.fetch_all(query)
    return cars_list

# Извличане на конкретен автомобил по ID
@app.get("/cars/{car_id}")
async def read_car(car_id: int):
    query = select(cars).where(cars.c.id == car_id)
    car = await database.fetch_one(query)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return car

# Актуализиране на автомобил
@app.put("/cars/{car_id}")
async def update_car(car_id: int, car: CarCreate):
    query = select(cars).where(cars.c.id == car_id)
    existing_car = await database.fetch_one(query)
    if not existing_car:
        raise HTTPException(status_code=404, detail="Car not found")

    update_query = cars.update().where(cars.c.id == car_id).values(
        make=car.make, model=car.model, productionYear=car.productionYear, licensePlate=car.licensePlate
    )
    await database.execute(update_query)

    # Обновяваме също и връзката с гаражите
    delete_query = car_garage_association.delete().where(car_garage_association.c.car_id == car_id)
    await database.execute(delete_query)

    for garage_id in car.garages:
        query = car_garage_association.insert().values(car_id=car_id, garage_id=garage_id)
        await database.execute(query)

    return {"id": car_id, **car.dict()}

# Изтриване на автомобил
@app.delete("/cars/{car_id}", status_code=204)
async def delete_car(car_id: int):
    query = select(cars).where(cars.c.id == car_id)
    existing_car = await database.fetch_one(query)
    if not existing_car:
        raise HTTPException(status_code=404, detail="Car not found")

    delete_query = cars.delete().where(cars.c.id == car_id)
    await database.execute(delete_query)

    # Изтриваме връзката на автомобила с гаражите
    delete_association_query = car_garage_association.delete().where(car_garage_association.c.car_id == car_id)
    await database.execute(delete_association_query)

    return {"message": "Car deleted"}

