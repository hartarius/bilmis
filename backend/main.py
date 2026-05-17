"""
BİLMİŞ API — FastAPI backend
Tahmin oyunu için REST API endpoint'leri.
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from game import GameEngine

# ── FastAPI App ──────────────────────────────────────────────────────────

app = FastAPI(
    title="BİLMİŞ API",
    description="Her şeyi bilen tahmin oyunu — Gemini destekli backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Session Store ────────────────────────────────────────────────────────

@dataclass
class GameSession:
    session_id: str
    secret: str
    history: list = field(default_factory=list)
    question_count: int = 0
    status: str = "asking"  # "asking" | "revealed"
    created_at: float = field(default_factory=time.time)


sessions: dict[str, GameSession] = {}

SESSION_TTL = 3600  # 1 saat


# ── Request/Response Models ──────────────────────────────────────────────

class NewGameRequest(BaseModel):
    secret: str = Field(..., min_length=1, max_length=100)


class AnswerRequest(BaseModel):
    session_id: str
    answer: str


class GameResponse(BaseModel):
    session_id: str
    question: str
    question_number: int
    is_final: bool = False


class ErrorResponse(BaseModel):
    error: str


# ── Helpers ──────────────────────────────────────────────────────────────

def normalize_answer(raw: str) -> str:
    """Türkçe/İngilizce cevap varyasyonlarını normalize et."""
    raw = raw.strip().lower()
    if raw in ("evet", "e", "yes", "y", "doğru", "aynen", "tabii", "kesinlikle"):
        return "evet"
    elif raw in ("hayır", "hayir", "h", "no", "n", "değil", "degil", "yok"):
        return "hayır"
    else:
        return "bilmiyorum"


# ── Endpoints ────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "game": "BİLMİŞ",
        "active_sessions": len(sessions),
    }


@app.post("/api/new-game", response_model=GameResponse)
async def new_game(req: NewGameRequest):
    try:
        engine = GameEngine()
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=500)

    session = GameSession(
        session_id=str(uuid.uuid4()),
        secret=req.secret.strip(),
    )

    try:
        question = engine.start_game(session.secret)
    except Exception as e:
        return JSONResponse({"error": f"AI hatası: {e}"}, status_code=500)

    session.history.append({"role": "assistant", "content": question})
    session.question_count = 1
    sessions[session.session_id] = session

    return GameResponse(
        session_id=session.session_id,
        question=question,
        question_number=1,
        is_final=False,
    )


@app.post("/api/answer", response_model=GameResponse)
async def answer(req: AnswerRequest):
    session = sessions.get(req.session_id)
    if not session:
        return JSONResponse({"error": "Oyun oturumu bulunamadı"}, status_code=404)

    if session.status == "revealed":
        return JSONResponse({"error": "Bu oyun zaten tamamlandı"}, status_code=400)

    # Cevabı normalize et ve geçmişe ekle
    normalized = normalize_answer(req.answer)
    session.history.append({"role": "user", "content": normalized})

    try:
        engine = GameEngine()
        response, is_final = engine.ask_next(
            session.secret, session.history, session.question_count
        )
    except Exception as e:
        return JSONResponse({"error": f"AI hatası: {e}"}, status_code=500)

    session.history.append({"role": "assistant", "content": response})
    session.question_count += 1

    if is_final:
        session.status = "revealed"

    return GameResponse(
        session_id=session.session_id,
        question=response,
        question_number=session.question_count,
        is_final=is_final,
    )


# ── Session Cleanup ──────────────────────────────────────────────────────

async def cleanup_sessions():
    """Periyodik olarak süresi dolmuş session'ları temizle."""
    while True:
        await asyncio.sleep(300)  # 5 dakikada bir
        now = time.time()
        expired = [
            sid
            for sid, s in sessions.items()
            if now - s.created_at > SESSION_TTL
        ]
        for sid in expired:
            del sessions[sid]
        if expired:
            print(f"🧹 {len(expired)} expired session temizlendi")


@app.on_event("startup")
async def startup():
    asyncio.create_task(cleanup_sessions())
    print("🔮 BİLMİŞ API hazır — http://localhost:8000")
    print("📋 /api/health — durum kontrolü")
    print("🆕 POST /api/new-game — yeni oyun başlat")
    print("❓ POST /api/answer — soruya cevap ver")


# ── Run ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
