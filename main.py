"""
NOT DEFTERİ API


Özellikler:
- Kullanıcı bazlı not sistemi
- Çoklu etiket desteği
- Etiket otomatik oluşturma
- Etikete göre filtreleme
- Aggregation ile etiket not sayısı
- MongoDB index optimizasyonu
"""

from fastapi import FastAPI, Query, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import os
from dotenv import load_dotenv

# --------------------------------------------------
# ENV AYARLARI
# --------------------------------------------------

load_dotenv(dotenv_path=".env")


MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

if not MONGO_URI:
    raise ValueError("MONGO_URI .env dosyasında tanımlı değil!")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

notes_collection = db["notes"]
labels_collection = db["labels"]

app = FastAPI(title="Not Defteri API - Professional")

# --------------------------------------------------
# INDEXLER (Production Mantığı)
# --------------------------------------------------

labels_collection.create_index("name", unique=True)
notes_collection.create_index("userId")
notes_collection.create_index("createdAt")
notes_collection.create_index("labels")

# --------------------------------------------------
# HELPER FONKSİYONLAR
# --------------------------------------------------

def serialize_note(note):
    note["_id"] = str(note["_id"])
    note["userId"] = str(note["userId"])
    note["createdAt"] = note["createdAt"].isoformat()
    return note


def get_or_create_labels(label_names: List[str]) -> List[ObjectId]:
    """
    Label varsa alır, yoksa oluşturur.
    Küçük harfe çevirerek duplicate engeller.
    """

    label_ids = []

    for name in label_names:
        normalized = name.strip().lower()

        label = labels_collection.find_one({"name": normalized})

        if label:
            label_ids.append(label["_id"])
        else:
            new_label = {
                "name": normalized,
                "createdAt": datetime.utcnow()
            }
            result = labels_collection.insert_one(new_label)
            label_ids.append(result.inserted_id)

    return label_ids


# --------------------------------------------------
# SCHEMA
# --------------------------------------------------

class NoteCreate(BaseModel):
    title: str = Field(..., example="Yatırım Planı")
    content: str = Field(..., example="Uzun vadeli yatırım stratejisi")
    userId: str = Field(..., example="ObjectId string")
    labels: List[str] = Field(default=[])


# --------------------------------------------------
# POST /notes
# --------------------------------------------------

@app.post("/notes")
def create_note(note: NoteCreate):
    """
    Yeni not oluşturur.
    Etiketler varsa kullanır, yoksa otomatik oluşturur.
    """

    try:
        user_object_id = ObjectId(note.userId)
    except:
        raise HTTPException(status_code=400, detail="Geçersiz userId")

    label_ids = get_or_create_labels(note.labels)

    new_note = {
        "title": note.title,
        "content": note.content,
        "userId": user_object_id,
        "labels": label_ids,
        "createdAt": datetime.utcnow()
    }

    result = notes_collection.insert_one(new_note)

    return {
        "message": "Not başarıyla oluşturuldu",
        "noteId": str(result.inserted_id)
    }


# --------------------------------------------------
# GET /notes
# Filtreleme: userId ve/veya label
# --------------------------------------------------

@app.get("/notes")
def get_notes(
    userId: Optional[str] = None,
    label: Optional[str] = Query(None)
):
    """
    Notları getirir.
    - userId ile filtreleme
    - label ile filtreleme
    """

    query = {}

    if userId:
        try:
            query["userId"] = ObjectId(userId)
        except:
            raise HTTPException(status_code=400, detail="Geçersiz userId")

    if label:
        label_obj = labels_collection.find_one({"name": label.strip().lower()})
        if not label_obj:
            return []
        query["labels"] = label_obj["_id"]

    # Aggregation ile label isimlerini join ediyoruz
    pipeline = [
        {"$match": query},
        {
            "$lookup": {
                "from": "labels",
                "localField": "labels",
                "foreignField": "_id",
                "as": "labelDetails"
            }
        },
        {
            "$project": {
                "title": 1,
                "content": 1,
                "userId": 1,
                "createdAt": 1,
                "labels": "$labelDetails.name"
            }
        }
    ]

    notes = list(notes_collection.aggregate(pipeline))

    for note in notes:
        note["_id"] = str(note["_id"])
        note["userId"] = str(note["userId"])
        note["createdAt"] = note["createdAt"].isoformat()

    return notes


# --------------------------------------------------
# GET /labels
# Aggregation ile her label'ın not sayısını getirir
# --------------------------------------------------

@app.get("/labels")
def get_labels():
    """
    Tüm etiketleri ve kaç notta kullanıldığını getirir.
    """

    pipeline = [
        {
            "$lookup": {
                "from": "notes",
                "localField": "_id",
                "foreignField": "labels",
                "as": "relatedNotes"
            }
        },
        {
            "$project": {
                "name": 1,
                "noteCount": {"$size": "$relatedNotes"}
            }
        },
        {
            "$sort": {"noteCount": -1}
        }
    ]

    labels = list(labels_collection.aggregate(pipeline))

    for label in labels:
        label["_id"] = str(label["_id"])

    return labels
