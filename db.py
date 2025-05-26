from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

DB_URI = "postgresql+psycopg2://postgres:1234@localhost:5432/postgres?options=-csearch_path=Проект2"

engine = create_engine(DB_URI)

try:
    with engine.connect() as connection:
        print("Успех!")
except Exception as e:
    print (f"Ошибка подключения: {e}")

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
