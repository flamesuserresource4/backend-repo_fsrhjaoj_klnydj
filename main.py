import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId
from datetime import datetime, timezone

from database import db, create_document, get_documents

app = FastAPI(title="Trucker RU Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"app": "Trucker RU", "status": "ok"}


# Schemas mirror (for /schema viewer)
from schemas import (
    TruckerUser, Cafe, QuizQuestion, NewsItem, GuideEntry, TruckHistory, ChatMessage
)

@app.get("/schema")
def get_schema():
    # expose schema class names for the database viewer
    return {
        "models": [
            "TruckerUser", "Cafe", "QuizQuestion", "NewsItem", "GuideEntry", "TruckHistory", "ChatMessage"
        ]
    }


# Utility

def collection(name: str):
    if db is None:
        raise HTTPException(500, "Database not configured")
    return db[name]


# Auth/Profile - simple profile create/list by handle
class ProfileIn(BaseModel):
    handle: str
    name: str
    region: Optional[str] = None
    truck_model: Optional[str] = None
    experience_years: Optional[int] = 0
    bio: Optional[str] = None

@app.post("/api/profile")
def create_profile(p: ProfileIn):
    # upsert by handle
    col = collection("truckeruser")
    existing = col.find_one({"handle": p.handle})
    data = p.model_dump()
    data["updated_at"] = datetime.now(timezone.utc)
    if existing:
        col.update_one({"_id": existing["_id"]}, {"$set": data})
        oid = existing["_id"]
    else:
        data["created_at"] = datetime.now(timezone.utc)
        oid = col.insert_one(data).inserted_id
    return {"id": str(oid)}

@app.get("/api/profile/{handle}")
def get_profile(handle: str):
    doc = collection("truckeruser").find_one({"handle": handle})
    if not doc:
        raise HTTPException(404, "Profile not found")
    doc["id"] = str(doc.pop("_id"))
    return doc


# Quiz endpoints
class AnswerPayload(BaseModel):
    question_id: str
    answer_index: int

@app.get("/api/quiz/questions")
def quiz_questions(limit: int = 10):
    items = get_documents("quizquestion", {}, limit)
    # seed if empty
    if not items:
        seed = [
            {
                "question": "На каком расстоянии до железнодорожного переезда устанавливается предупреждающий знак?",
                "options": ["50 м", "150-300 м", "500 м", "1 км"],
                "correct_index": 1,
                "topic": "ПДД"
            },
            {
                "question": "Какая федеральная трасса соединяет Москву и Санкт-Петербург?",
                "options": ["М7", "М10/М11", "Р23", "А108"],
                "correct_index": 1,
                "topic": "География"
            },
            {
                "question": "Что означает сплошная желтая линия у бордюра?",
                "options": ["Стоянка запрещена", "Остановка запрещена", "Дорога с односторонним движением", "Обочина"],
                "correct_index": 1,
                "topic": "ПДД"
            }
        ]
        for q in seed:
            create_document("quizquestion", q)
        items = get_documents("quizquestion", {}, limit)
    # normalize
    out = []
    for d in items:
        d["id"] = str(d.pop("_id"))
        out.append(d)
    return out

@app.post("/api/quiz/answer")
def quiz_answer(payload: AnswerPayload):
    q = collection("quizquestion").find_one({"_id": ObjectId(payload.question_id)})
    if not q:
        raise HTTPException(404, "Question not found")
    correct = int(q.get("correct_index", -1)) == int(payload.answer_index)
    return {"correct": correct}


# Cafes (admin add, public list)
class CafeIn(BaseModel):
    title: str
    highway: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    rating: Optional[float] = 4.5
    added_by: Optional[str] = None

@app.post("/api/cafes")
def add_cafe(c: CafeIn):
    cafe_id = create_document("cafe", c.model_dump())
    return {"id": cafe_id}

@app.get("/api/cafes")
def list_cafes(limit: int = 30):
    items = get_documents("cafe", {}, limit)
    for d in items:
        d["id"] = str(d.pop("_id"))
    return items


# Truck history
@app.get("/api/history")
def truck_history(limit: int = 20):
    items = get_documents("truckhistory", {}, limit)
    if not items:
        seed = [
            {"title": "КамАЗ: легенда отечественных дорог", "era": "1970-е", "content": "История становления КамАЗа и ралли «Дакар»."},
            {"title": "МАЗ и дальние рейсы СССР", "era": "1960-80", "content": "Как строилась логистика по Союзу и культ дальнобоя."}
        ]
        for h in seed:
            create_document("truckhistory", h)
        items = get_documents("truckhistory", {}, limit)
    for d in items:
        d["id"] = str(d.pop("_id"))
    return items


# News and Guide
@app.get("/api/news")
def get_news(limit: int = 10):
    items = get_documents("newsitem", {}, limit)
    for d in items:
        d["id"] = str(d.pop("_id"))
    # If empty, provide some starter news
    if not items:
        items = [
            {"id": "seed1", "title": "Ремонт на М5", "summary": "Ночные перекрытия на 120-125 км", "source": "rosavtodor"},
            {"id": "seed2", "title": "Погода на трассах", "summary": "Гололёд на Урале, соблюдайте дистанцию"}
        ]
    return items

@app.get("/api/guide")
def get_guide():
    items = get_documents("guideentry", {}, 50)
    if not items:
        seed = [
            {"title": "Подготовка к рейсу", "content": "Чек-лист: резина, огнетушитель, аптечка, инструменты."},
            {"title": "Экономия топлива", "content": "Поддерживайте обороты в зелёной зоне, планируйте остановки."},
            {"title": "Парковки и стоянки", "content": "Список безопасных стоянок вдоль М4 и М7."}
        ]
        for g in seed:
            create_document("guideentry", g)
        items = get_documents("guideentry", {}, 50)
    for d in items:
        d["id"] = str(d.pop("_id"))
    return items


# Radio chat (simple global room)
class ChatIn(BaseModel):
    handle: str
    message: str

@app.post("/api/chat")
def send_chat(msg: ChatIn):
    mid = create_document("chatmessage", {"handle": msg.handle, "message": msg.message})
    return {"id": mid}

@app.get("/api/chat")
def get_chat(limit: int = 25):
    items = get_documents("chatmessage", {}, limit)
    # sort by created_at if present
    items.sort(key=lambda d: d.get("created_at"), reverse=True)
    for d in items:
        d["id"] = str(d.pop("_id"))
    return items


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
