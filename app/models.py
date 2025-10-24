from sqlalchemy import Column, Integer, String, Float, DateTime, func
from sqlalchemy.sql import expression
from sqlalchemy import null
from sqlalchemy.orm import relationship
from app.database import Base


class Country(Base):
    __tablename__ = 'countries'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True, index=True)
    capital = Column(String(200), nullable=True)
    region = Column(String(100), nullable=True)
    population = Column(Integer, nullable=False)
    currency_code = Column(String(10), nullable=True)
    exchange_rate = Column(Float, nullable=True)
    estimated_gdp = Column(Float, nullable=True)
    flag_url = Column(String(500), nullable=True)
    last_refreshed_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Meta(Base):
    __tablename__ = 'meta'

    key = Column(String(50), primary_key=True)
    value = Column(String(200), nullable=True)