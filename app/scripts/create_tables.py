# create_tables.py

from app.core.database import engine
from app.models.incident import Base
import models.incident 
import models.auth      

Base.metadata.create_all(bind=engine)
print("Tables created")
