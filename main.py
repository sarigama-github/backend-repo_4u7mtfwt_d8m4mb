import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from schemas import Reservation
from database import create_document, get_documents, db

app = FastAPI(title="Divines API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
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
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

# -------------------- Reservations --------------------
@app.post("/api/reservations")
def create_reservation(payload: Reservation):
    try:
        inserted_id = create_document("reservation", payload)
        return {"ok": True, "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ReservationQuery(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None

@app.get("/api/reservations")
def list_reservations(email: Optional[str] = None, name: Optional[str] = None, limit: int = 50):
    try:
        filter_dict = {}
        if email:
            filter_dict["email"] = email
        if name:
            filter_dict["name"] = name
        docs = get_documents("reservation", filter_dict, limit)
        # Convert ObjectIds to strings for JSON serialization
        for d in docs:
            if "_id" in d:
                d["_id"] = str(d["_id"])
            if "created_at" in d:
                d["created_at"] = str(d["created_at"]) 
            if "updated_at" in d:
                d["updated_at"] = str(d["updated_at"]) 
        return {"ok": True, "items": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
