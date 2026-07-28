from app.core.database import engine
from app.models.base import Base

# load all models
from app.models import (
    User,
    Site,
    Url,
    Keyword,
    Audit,
    Report,
)

print("Creating database tables...")

Base.metadata.create_all(bind=engine)

print("Tables created successfully!")