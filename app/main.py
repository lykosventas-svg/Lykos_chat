"""FastAPI main application for the RAG Chatbot."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import importlib.util

from app.config import load_config, save_config, AppConfig, MaaSConfig
from app.database import db_manager
from app.llm_service import llm_service


app = FastAPI(title="RAG Chatbot", version="1.0.0")


# ─── Load Seed Data on Startup ─────────────────────────────────────

@app.on_event("startup")
async def load_seed_data():
    """Load seed data from seed_data.py into ChromaDB on startup.
    
    Supports two formats:
    1. DOCUMENTS = [{"content": "...", "metadata": {...}}, ...]
    2. documentos = [...], metadatos = [...], ids = [...] (separate lists)
    
    Only adds documents with IDs that don't already exist in ChromaDB (incremental loading).
    """
    seed_path = Path(__file__).parent.parent / "seed_data.py"
    if not seed_path.exists():
        return

    # Import seed_data module dynamically
    spec = importlib.util.spec_from_file_location("seed_data", str(seed_path))
    seed_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seed_module)

    # Get existing IDs in ChromaDB to avoid duplicates
    existing_ids = set()
    if not db_manager.is_empty():
        existing_docs = db_manager.get_all_documents()
        existing_ids = set(existing_docs.get("ids", []))

    # Format 1: DOCUMENTS list with dicts
    documents = getattr(seed_module, "DOCUMENTS", [])
    if documents:
        contents = [doc["content"] for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]
        doc_ids = [doc.get("id", f"doc_{i}") for i, doc in enumerate(documents)]

        # Filter out documents that already exist
        new_items = [(c, m, i) for c, m, i in zip(contents, metadatas, doc_ids) if i not in existing_ids]
        if not new_items:
            return

        new_contents = [item[0] for item in new_items]
        new_metadatas = [item[1] for item in new_items]
        new_ids = [item[2] for item in new_items]

        db_manager.add_documents(
            documents=new_contents,
            metadatas=new_metadatas,
            ids=new_ids
        )
        print(f"[OK] Se cargaron {len(new_items)} documento(s) nuevo(s) desde seed_data.py (formato DOCUMENTS) a ChromaDB")
        return

    # Format 2: Separate lists (documentos, metadatos, ids)
    documentos = getattr(seed_module, "documentos", [])
    if not documentos:
        return

    metadatos = getattr(seed_module, "metadatos", None)
    ids = getattr(seed_module, "ids", None)

    # Auto-generate IDs if not provided
    if not ids or len(ids) != len(documentos):
        ids = [f"doc_{i}" for i in range(len(documentos))]

    # Validate metadatos length
    if metadatos and len(metadatos) != len(documentos):
        print(f"[WARN] Error: metadatos tiene {len(metadatos)} elementos pero documentos tiene {len(documentos)}")
        metadatos = None

    # Filter out documents that already exist by ID
    new_indices = [i for i, doc_id in enumerate(ids) if doc_id not in existing_ids]
    if not new_indices:
        return

    new_documentos = [documentos[i] for i in new_indices]
    new_metadatos = [metadatos[i] for i in new_indices] if metadatos else None
    new_ids = [ids[i] for i in new_indices]

    db_manager.add_documents(
        documents=new_documentos,
        metadatas=new_metadatos,
        ids=new_ids
    )
    print(f"[OK] Se cargaron {len(new_indices)} documento(s) nuevo(s) desde seed_data.py (formato listas separadas) a ChromaDB")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
STATIC_DIR = Path(__file__).parent.parent / "static"


# ─── Pydantic Models ───────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    sources: List[str] = []


class MaaSConfigRequest(BaseModel):
    url: str
    api_key: str
    model: str


# ─── Routes ────────────────────────────────────────────────────────

@app.get("/")
async def serve_frontend():
    """Serve the frontend HTML page."""
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat messages using RAG."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío")

    # Check if MaaS (LLM) is configured
    config = load_config()
    if not config.maas.url or not config.maas.api_key or not config.maas.model:
        return ChatResponse(
            response="⚠️ El chatbot no está conectado a un LLM. Por favor configure MaaS (URL, API Key y Modelo) haciendo clic en el botón ⚙️.",
            sources=[]
        )

    # Check if ChromaDB is empty
    if db_manager.is_empty():
        # Still call LLM so it can respond, but note there's no data
        response_text = llm_service.generate_response(
            query=request.message,
            context_documents=[]
        )
        return ChatResponse(
            response=response_text,
            sources=[]
        )

    # Query ChromaDB for relevant documents
    results = db_manager.query(request.message, n_results=5)
    context_documents = results.get("documents", [])

    if not context_documents:
        # No relevant results found — still call LLM with empty context
        response_text = llm_service.generate_response(
            query=request.message,
            context_documents=[]
        )
        return ChatResponse(
            response=response_text,
            sources=[]
        )

    # Generate response using LLM with RAG
    response_text = llm_service.generate_response(
        query=request.message,
        context_documents=context_documents
    )

    # Collect source metadata
    sources = []
    metadatas = results.get("metadatas", [])
    for meta in metadatas:
        if meta and "source" in meta:
            sources.append(meta["source"])

    return ChatResponse(
        response=response_text,
        sources=sources
    )


@app.get("/api/config")
async def get_config():
    """Get current MaaS configuration."""
    config = load_config()
    return {
        "url": config.maas.url,
        "api_key": config.maas.api_key,
        "model": config.maas.model,
        "is_configured": bool(config.maas.url and config.maas.api_key and config.maas.model)
    }


@app.post("/api/config")
async def update_config(request: MaaSConfigRequest):
    """Update MaaS configuration."""
    config = load_config()
    config.maas.url = request.url.strip()
    config.maas.api_key = request.api_key.strip()
    config.maas.model = request.model.strip()
    save_config(config)
    return {"message": "Configuración guardada exitosamente"}


@app.post("/api/config/test")
async def test_config():
    """Test the MaaS connection."""
    result = llm_service.test_connection()
    return result


@app.get("/api/stats")
async def get_stats():
    """Get database statistics."""
    return {
        "total_documents": db_manager.collection.count() if not db_manager.is_empty() else 0,
        "is_empty": db_manager.is_empty()
    }


# Mount static files last so API routes take precedence
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
