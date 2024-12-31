from sqlalchemy import create_engine, MetaData

# Път към базата данни
DATABASE_URL = "sqlite:///./car_management.db"

# Инициализиране на SQLAlchemy Engine и MetaData
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
metadata = MetaData()
