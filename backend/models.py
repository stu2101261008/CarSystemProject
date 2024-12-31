from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

# Основна база
Base = declarative_base()

# Клас за Гараж
class Garage(Base):
    __tablename__ = "garages"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    location = Column(String)
    city = Column(String)
    capacity = Column(Integer)
    
    # Отношение към автомобили
    cars = relationship("Car", secondary="car_garage_association")

# Клас за Автомобил
class Car(Base):
    __tablename__ = "cars"
    id = Column(Integer, primary_key=True, index=True)
    make = Column(String)
    model = Column(String)
    productionYear = Column(Integer)
    licensePlate = Column(String, unique=True)
    
    # Отношение към гаражи
    garages = relationship("Garage", secondary="car_garage_association")

# Клас за Заявка за поддръжка
class ServiceRequest(Base):
    __tablename__ = "service_requests"
    id = Column(Integer, primary_key=True, index=True)
    car_id = Column(Integer, ForeignKey("cars.id"))
    garage_id = Column(Integer, ForeignKey("garages.id"))
    service_date = Column(Date)

    car = relationship("Car")
    garage = relationship("Garage")
    
# Таблица за асоциации между автомобил и гараж
class CarGarageAssociation(Base):
    __tablename__ = "car_garage_association"
    car_id = Column(Integer, ForeignKey("cars.id"), primary_key=True)
    garage_id = Column(Integer, ForeignKey("garages.id"), primary_key=True)
