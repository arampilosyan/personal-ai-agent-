from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from app.agent import AgentError, PersonalAgent
from app.config import settings
from app.document_reader import DocumentError, extract_text
from database.db import Database

settings.ensure_data_dir()
db = Database(settings.database_path)
agent = PersonalAgent(db)

app = FastAPI(title="Personal AI Agent API", description="Document Q&A, conversation memory, and safe local task tools.", version="1.0.0")

class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=20_000)

class ChatResponse(BaseModel):
    session_id: str
    answer: str

@app.get("/health")
def health():
    return {"status": "ok", "provider_configured": bool(settings.openai_api_key)}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        answer = agent.chat(request.session_id, request.message)
        return ChatResponse(session_id=request.session_id, answer=answer)
    except AgentError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/documents")
async def upload_document(session_id: str = Form(..., min_length=1, max_length=100), file: UploadFile = File(...)):
    content = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds upload size limit.")
    try:
        text = extract_text(file.filename or "upload.txt", content, settings.max_document_chars)
        summary = agent.summarize_document(session_id, file.filename or "upload", text)
        return {"session_id": session_id, "filename": file.filename, "char_count": len(text), "summary": summary}
    except DocumentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except AgentError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

@app.get("/tasks/{session_id}")
def list_tasks(session_id: str):
    if len(session_id) > 100:
        raise HTTPException(status_code=400, detail="Invalid session ID.")
    return {"tasks": db.list_tasks(session_id)}

@app.get("/history/{session_id}")
def history(session_id: str, limit: int = 30):
    if len(session_id) > 100:
        raise HTTPException(status_code=400, detail="Invalid session ID.")
    return {"messages": db.get_messages(session_id, limit)}
