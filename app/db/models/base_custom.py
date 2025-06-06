from app.db.database import Base
from sqlalchemy import Column, Integer, DateTime, func

class BaseCustom(Base):
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Timestamps
    created = Column(DateTime(timezone=True), esrver_default=func.now())
    updated = Column(DateTime(timezone=True), onupdate=func.now())