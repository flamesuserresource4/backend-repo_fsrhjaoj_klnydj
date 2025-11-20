"""
Database Schemas for Trucker App (RU)

Each Pydantic model corresponds to a MongoDB collection.
Collection name = lowercase of class name.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TruckerUser(BaseModel):
    handle: str = Field(..., description="Уникальный позывной/ник")
    name: str = Field(..., description="Имя и фамилия")
    region: Optional[str] = Field(None, description="Регион или база")
    truck_model: Optional[str] = Field(None, description="Модель грузовика")
    experience_years: Optional[int] = Field(0, ge=0, le=80, description="Стаж")
    bio: Optional[str] = Field(None, description="О себе")
    is_admin: bool = Field(False, description="Админ ли пользователь")

class Cafe(BaseModel):
    title: str = Field(..., description="Название кафе")
    highway: Optional[str] = Field(None, description="Трасса/участок")
    location: Optional[str] = Field(None, description="Координаты или населённый пункт")
    description: Optional[str] = Field(None, description="За что любят")
    rating: Optional[float] = Field(4.5, ge=0, le=5)
    added_by: Optional[str] = Field(None, description="Позывной добавившего")

class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_index: int = Field(..., ge=0, le=3)
    topic: Optional[str] = Field(None, description="Тема: ПДД, География, Знаки")
    difficulty: Optional[str] = Field("normal", description="easy/normal/hard")

class NewsItem(BaseModel):
    title: str
    summary: str
    source: Optional[str] = None
    url: Optional[str] = None
    date: Optional[datetime] = None

class GuideEntry(BaseModel):
    title: str
    content: str
    tag: Optional[str] = None

class TruckHistory(BaseModel):
    title: str
    era: Optional[str] = None
    content: str
    image: Optional[str] = None

class ChatMessage(BaseModel):
    handle: str
    message: str
