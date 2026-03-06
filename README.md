# RAG Video Script Generator

An AI-powered backend that transforms uploaded documents (PDF, DOCX, PPTX, TXT) into structured, narration-ready educational video scripts using a **RAG pipeline** + **Groq LLM**.

---

## Architecture

```
┌──────────┐     ┌──────────┐     ┌──────────────┐     ┌───────────┐     ┌──────────────┐
│  Upload  │────▶│  Parse   │────▶│   Chunk      │────▶│  Embed    │────▶│ FAISS Index  │
│  (API)   │     │  (PyMuPDF│     │ (section-    │     │ (Sentence │     │ (IndexFlatIP)│
│          │     │  docx,   │     │  aware +     │     │  Trans-   │     │              │
│          │     │  pptx)   │     │  overlap)    │     │  formers) │     │              │
└──────────┘     └──────────┘     └──────────────┘     └───────────┘     └──────┬───────┘
                                                                               │
                                                                               ▼
                                                        ┌──────────────────────────────┐
                                                        │  Retriever (top-k + MMR)     │
                                                        │  Multi-query · Deduplication  │
                                                        └──────────────┬───────────────┘
                                                                       │
                                                                       ▼
                                                        ┌──────────────────────────────┐
                                                        │  Groq LLM (llama-3.3-70b)   │
                                                        │  Prompt templates · Retry    │
                                                        │  Token-safe truncation       │
                                                        └──────────────┬───────────────┘
                                                                       │
                                                                       ▼
                                                        ┌──────────────────────────────┐
                                                        │  Structured Script JSON      │
                                                        │  (hook, sections, visuals…)  │
                                                        └──────────────────────────────┘
```

## Data Flow

1. **Upload** → file saved + document ID assigned
2. **Build Index** → parse → chunk → embed → FAISS index saved to disk
3. **Generate Script** → retrieve top-k chunks with MMR → construct prompt → Groq generates structured JSON script

---

## Quick Start

### 1. Clone & install

```bash
cd RAG_HackaMined
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and set GROQ_API_KEY
```

### 3. Run server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000/docs** for the interactive Swagger UI.

---

## API Usage (curl examples)

### Health check
```bash
curl http://localhost:8000/health
```

### Upload a document
```bash
curl -X POST http://localhost:8000/upload-document \
  -F "file=@my_paper.pdf"
```

### Build index
```bash
curl -X POST http://localhost:8000/build-index/{DOCUMENT_ID}
```

### Generate script
```bash
curl -X POST http://localhost:8000/generate-script/{DOCUMENT_ID} \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Generate a 3-minute beginner-friendly video script",
    "target_audience": "college students",
    "tone": "youtube-explainer",
    "duration_minutes": 3,
    "include_analogies": true,
    "include_visual_cues": true
  }'
```

### Fetch the generated script
```bash
curl http://localhost:8000/document/{DOCUMENT_ID}/script
```

### Check document status
```bash
curl http://localhost:8000/document/{DOCUMENT_ID}/status
```

### Similarity search
```bash
curl -X POST http://localhost:8000/search/{DOCUMENT_ID} \
  -H "Content-Type: application/json" \
  -d '{"query": "what is the main contribution?", "top_k": 5}'
```

### Delete document
```bash
curl -X DELETE http://localhost:8000/document/{DOCUMENT_ID}
```

---

## How FAISS Indexing Works

1. Document text is split into overlapping chunks (~512 chars with 64-char overlap).
2. Each chunk is embedded using **SentenceTransformers** (`all-MiniLM-L6-v2`) into a 384-dim vector, L2-normalised.
3. Vectors are added to a **FAISS IndexFlatIP** (inner-product = cosine similarity with normalised vectors).
4. A JSON sidecar stores chunk texts + metadata (page, heading, source file).
5. The index is saved to disk and can be reloaded without recomputing embeddings.

## How the RAG Prompt Is Constructed

1. **Retrieval**: Top-k chunks retrieved via FAISS, re-ranked using **MMR** for diversity.
2. **Context Block**: Chunks are formatted with IDs, source metadata, and relevance scores.
3. **Token Safety**: Context is truncated if it exceeds ~24k tokens to stay within model limits.
4. **System Prompt**: Instructs the LLM to act as an educational scriptwriter with strict grounding rules.
5. **User Prompt**: Contains the context block + all user controls (tone, audience, duration, focus areas).
6. **Output Parsing**: JSON response is parsed into a typed `ScriptResponse` with fallback for malformed output.

---

## Configuration

All settings are in `.env` — see `.env.example` for the full list:

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | — | Your Groq API key |
| `GROQ_MODEL_NAME` | `llama-3.3-70b-versatile` | Groq model to use |
| `EMBEDDING_MODEL_NAME` | `all-MiniLM-L6-v2` | SentenceTransformers model |
| `CHUNK_SIZE` | `512` | Characters per chunk |
| `CHUNK_OVERLAP` | `64` | Overlap between chunks |
| `TOP_K` | `10` | Chunks retrieved per query |
| `MAX_UPLOAD_SIZE_MB` | `50` | Max upload file size |

---

## Future Improvements

- [ ] **TTS Integration** — plug in Eleven Labs / Bark for voice generation
- [ ] **Image Generation** — DALL-E / Stable Diffusion for visual assets per section
- [ ] **Video Assembly** — FFmpeg pipeline combining narration + visuals
- [ ] **PostgreSQL** — replace in-memory registry with a database
- [ ] **Celery/Redis** — background task queue for large documents
- [ ] **React Frontend** — upload UI, script viewer, regeneration controls
- [ ] **Authentication** — API key or OAuth
- [ ] **Streaming** — stream script generation via SSE
- [ ] **Multi-document** — cross-reference multiple documents in one script

---

## Project Structure

```
RAG_HackaMined/
├── app/
│   ├── api/
│   │   └── routes.py          # All FastAPI endpoints
│   ├── core/
│   │   ├── config.py          # Pydantic settings
│   │   └── logger.py          # Structured logging
│   ├── models/
│   │   └── schemas.py         # Request/response Pydantic models
│   ├── prompts/
│   │   ├── system_prompt.py   # System prompt template
│   │   └── user_prompt.py     # User prompt builder
│   ├── rag/
│   │   ├── embedder.py        # SentenceTransformers wrapper
│   │   ├── faiss_index.py     # FAISS index + metadata sidecar
│   │   ├── retriever.py       # Top-k + MMR + dedup retriever
│   │   └── script_generator.py # Groq LLM integration
│   ├── services/
│   │   ├── parsers.py         # PDF / DOCX / PPTX / TXT parsers
│   │   └── chunker.py         # Intelligent document chunking
│   ├── storage/               # Runtime data (uploads, indices, scripts)
│   ├── utils/
│   │   └── helpers.py         # File validation, text cleaning, etc.
│   └── main.py                # FastAPI app entry point
├── .env.example
├── requirements.txt
└── README.md
```

---

## License

MIT
