from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from models import Garage, Car, ServiceRequest, CarGarageAssociation
from database import engine, metadata, DATABASE_URL
from sqlalchemy import select
from databases import Database
from datetime import date
from typing import Optional
from sqlalchemy import func


# Инициализация на FastAPI
app = FastAPI()
database = Database(DATABASE_URL)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)


# Създаване на таблиците в базата данни
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

# ---------------------------- Гаражи ----------------------------

# Pydantic модел за създаване на гараж
class GarageCreate(BaseModel):
    name: str
    location: str
    city: str
    capacity: int

# Създаване на нов сервиз
@app.post("/garages/", status_code=201)
async def create_garage(garage: GarageCreate):
    query = Garage.__table__.insert().values(
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

# Извличане на всички сервизи с филтър по град
@app.get("/garages/")
async def read_garages(city: str = None):
    query = select(Garage)

    if city:
        query = query.where(Garage.city == city)  # Филтриране по град
    
    garages_list = await database.fetch_all(query)
    return garages_list

# Извличане на конкретен сервиз по ID
@app.get("/garages/{garage_id}")
async def read_garage(garage_id: int):
    query = select(Garage).where(Garage.id == garage_id)
    garage = await database.fetch_one(query)
    if not garage:
        raise HTTPException(status_code=404, detail="Garage not found")
    return garage

# Обновяване на съществуващ сервиз
@app.put("/garages/{garage_id}")
async def update_garage(garage_id: int, garage: GarageCreate):
    query = select(Garage).where(Garage.id == garage_id)
    existing_garage = await database.fetch_one(query)
    if not existing_garage:
        raise HTTPException(status_code=404, detail="Garage not found")
    
    update_query = Garage.__table__.update().where(Garage.id == garage_id).values(
        name=garage.name, location=garage.location, city=garage.city, capacity=garage.capacity
    )
    await database.execute(update_query)
    return {"id": garage_id, **garage.dict()}

# Изтриване на сервиз по ID
@app.delete("/garages/{garage_id}", status_code=204)
async def delete_garage(garage_id: int):
    query = select(Garage).where(Garage.id == garage_id)
    existing_garage = await database.fetch_one(query)
    if not existing_garage:
        raise HTTPException(status_code=404, detail="Garage not found")
    
    delete_query = Garage.__table__.delete().where(Garage.id == garage_id)
    await database.execute(delete_query)
    return {"message": "Garage deleted"}

# ---------------------------- Автомобили ----------------------------

# Pydantic модел за създаване на автомобил
class CarCreate(BaseModel):
    make: str
    model: str
    productionYear: int
    licensePlate: str
    garages: list[int]  # Списък с ID-та на гаражи

# Създаване на нов автомобил
@app.post("/cars/", status_code=201)
async def create_car(car: CarCreate):
    # Проверка дали автомобил с такава лицензна табела вече съществува
    query = select(Car).where(Car.licensePlate == car.licensePlate)
    existing_car = await database.fetch_one(query)
    if existing_car:
        raise HTTPException(status_code=400, detail="Car with this license plate already exists")

    # Въведете новия автомобил в базата данни
    query = Car.__table__.insert().values(
        make=car.make,
        model=car.model,
        productionYear=car.productionYear,
        licensePlate=car.licensePlate,
    )
    car_id = await database.execute(query)

    # Регистрираме автомобила в гаражите
    for garage_id in car.garages:
        query = CarGarageAssociation.__table__.insert().values(car_id=car_id, garage_id=garage_id)
        await database.execute(query)

    return {**car.dict(), "id": car_id}

# Извличане на автомобили с филтри по марка и диапазон от години на производство
@app.get("/cars/")
async def read_cars(make: Optional[str] = None, year_from: Optional[int] = None, year_to: Optional[int] = None):
    query = select(Car)

    if make:
        query = query.where(Car.make == make)
    if year_from:
        query = query.where(Car.productionYear >= year_from)
    if year_to:
        query = query.where(Car.productionYear <= year_to)

    cars_list = await database.fetch_all(query)
    return cars_list

# Извличане на конкретен автомобил по ID
@app.get("/cars/{car_id}")
async def read_car(car_id: int):
    query = select(Car).where(Car.id == car_id)
    car = await database.fetch_one(query)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return car

# Обновяване на автомобил
@app.put("/cars/{car_id}")
async def update_car(car_id: int, car: CarCreate):
    query = select(Car).where(Car.id == car_id)
    existing_car = await database.fetch_one(query)
    if not existing_car:
        raise HTTPException(status_code=404, detail="Car not found")

    update_query = Car.__table__.update().where(Car.id == car_id).values(
        make=car.make, model=car.model, productionYear=car.productionYear, licensePlate=car.licensePlate
    )
    await database.execute(update_query)

    # Обновяваме също и връзката с гаражите
    delete_query = CarGarageAssociation.__table__.delete().where(CarGarageAssociation.car_id == car_id)
    await database.execute(delete_query)

    for garage_id in car.garages:
        query = CarGarageAssociation.__table__.insert().values(car_id=car_id, garage_id=garage_id)
        await database.execute(query)

    return {"id": car_id, **car.dict()}

# Изтриване на автомобил
@app.delete("/cars/{car_id}", status_code=204)
async def delete_car(car_id: int):
    query = select(Car).where(Car.id == car_id)
    existing_car = await database.fetch_one(query)
    if not existing_car:
        raise HTTPException(status_code=404, detail="Car not found")

    delete_query = Car.__table__.delete().where(Car.id == car_id)
    await database.execute(delete_query)

    # Изтриваме връзката на автомобила с гаражите
    delete_association_query = CarGarageAssociation.__table__.delete().where(CarGarageAssociation.car_id == car_id)
    await database.execute(delete_association_query)

    return {"message": "Car deleted"}

# ---------------------------- Заявки за поддръжка ----------------------------

# Pydantic модел за създаване на заявка за поддръжка
class ServiceRequestCreate(BaseModel):
    car_id: int  # ID на колата
    garage_id: int  # ID на гаража
    service_date: date  # Дата на заявката

    class Config:
        orm_mode = True

# Създаване на заявка за поддръжка
@app.post("/service_requests/", status_code=201)
async def create_service_request(request: ServiceRequestCreate):
    # Проверка дали има свободни места за избраната дата
    query = select([func.count()]).where(
        service_requests.c.garage_id == request.garage_id,
        service_requests.c.service_date == request.service_date
    )
    existing_requests = await database.fetch_one(query)
    
    # Максимален капацитет на сервиза
    max_capacity_query = select([garages.c.capacity]).where(garages.c.id == request.garage_id)
    max_capacity = await database.fetch_one(max_capacity_query)
    
    if existing_requests[0] >= max_capacity[0]:
        raise HTTPException(status_code=400, detail="No available slots for the selected date")

    # Въвеждаме новата заявка
    insert_query = service_requests.insert().values(
        car_id=request.car_id,
        garage_id=request.garage_id,
        service_date=request.service_date
    )
    service_request_id = await database.execute(insert_query)

    return {"id": service_request_id, **request.dict()}
