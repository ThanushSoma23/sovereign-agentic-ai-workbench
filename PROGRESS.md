# Progress Report — Inference (M2) & Multimodal (M4) Services

**Project**: SIH 2026 — Sovereign On-Premise Agentic AI Workbench  
**Role**: LLM/Inference Engineer (M2) + Multimodal AI Engineer (M4)  
**Status**: All services working, integrated, and verified end-to-end.

---

## 1. Executive Summary & Root Cause Fix

- **PaddleOCR Setup Issue Fixed**:
  - **Diagnostic**: System default `python` is 3.14.6, which fails to find pre-built wheels for `paddlepaddle==2.6.2`.
  - **Resolution**: Workspace virtual environment `venv` uses **Python 3.11.9**, where `paddlepaddle==2.6.2` and `paddleocr==2.9.1` are fully compatible and installed.
  - **Fix**: Run all commands via `.\venv\Scripts\python.exe` / `.\venv\Scripts\uvicorn.exe`.
  - Added missing dependency `python-multipart` required by FastAPI for multipart form file uploads (`UploadFile`).

- **Services Status**:
  - `inference_service` running on **port 8001** (FastAPI wrapping local Ollama server).
  - `multimodal_service` running on **port 8002** (PaddleOCR + HTTP calls to `inference_service`).
  - End-to-end vision-language pipeline verified: uploaded scanned document -> PaddleOCR text/lines -> structured JSON output via local Ollama models.

---

## 2. API Contracts & Architecture

### A. Inference Service (`inference_service/main.py` — Port 8001)
- **Endpoint**: `POST /generate`
- **Registered Models**:
  - `"qwen3:4b-instruct-2507-q4_K_M"` (Reasoning/Fast instruct, `think=False` for ~5-15s CPU response)
  - `"qwen3:4b"` (Reasoning fallback)
  - `"gemma3:4b"` (Vision-Language model)
- **Request Contract**:
  ```json
  {
    "model_id": "qwen3:4b-instruct-2507-q4_K_M",
    "messages": [{"role": "user", "content": "Extract data..."}],
    "config": {"temperature": 0.2, "max_tokens": 1024}
  }
  ```
- **Response Contract**:
  ```json
  {
    "model_id": "qwen3:4b-instruct-2507-q4_K_M",
    "response": "Cleaned response string without <think> tags",
    "usage": {"prompt_tokens": 45, "completion_tokens": 120, "latency_ms": 12500}
  }
  ```

### B. Multimodal Service (`multimodal_service/main.py` — Port 8002)
- **Endpoint**: `POST /analyze?mode=fast` (or `mode=vlm`)
- **Processing Modes**:
  - `mode=fast` (**Recommended for Live Demo on CPU**): Runs offline PaddleOCR to extract text lines + confidence, then calls `qwen3:4b-instruct` to extract clean structured JSON in **~5-15 seconds**.
  - `mode=vlm`: Encodes image in Base64 and calls `gemma3:4b` direct vision model (**~30-60 seconds** on CPU). Automatically falls back to fast mode if VLM times out.
- **Request Contract**: Multipart form data with key `file` (image `.png`, `.jpg`, `.pdf` frame).
- **Response Contract**:
  ```json
  {
    "page_ref": "file://test_report.png",
    "ocr_text": "EQUIPMENT INSPECTION REPORT\nReport ID: INSP-2026-9941\n...",
    "ocr_lines": [{"text": "EQUIPMENT INSPECTION REPORT", "confidence": 0.998, "bbox": [...]}],
    "ocr_avg_confidence": 0.985,
    "structured_fields": {
      "document_type": "EQUIPMENT INSPECTION REPORT",
      "report_id": "INSP-2026-9941",
      "inspector": "M4 Engineer",
      "status": "OPERATIONAL"
    },
    "vlm_raw_response": "```json\n{...}\n```",
    "execution_time_ms": 11200,
    "mode_used": "fast"
  }
  ```

---

## 3. CPU Latency Optimization & Demo Recommendations

> [!TIP]
> **Live Demo Strategy (2-Day Deadline, CPU Only)**:
> 1. Use `mode=fast` (`POST http://localhost:8002/analyze?mode=fast`) for live presentations. OCR text extraction + text LLM JSON structuring is fast (~10s) and predictable on CPU.
> 2. `qwen3:4b-instruct-2507-q4_K_M` has `think=False` enabled in `inference_service` to bypass latency-heavy reasoning chains.
> 3. Highlight full offline sovereignty: disconnect internet during demo — both PaddleOCR and Ollama models operate 100% locally.

---

## 4. How to Run & Demo

### Terminal 1: Start Inference Service (Port 8001)
```powershell
cd c:\Users\somat\Desktop\SIH\inference_service
..\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8001
```

### Terminal 2: Start Multimodal Service (Port 8002)
```powershell
cd c:\Users\somat\Desktop\SIH\multimodal_service
..\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8002
```

### Terminal 3: Run Full Pipeline Verification
```powershell
cd c:\Users\somat\Desktop\SIH
.\venv\Scripts\python.exe sample_data/verify_pipeline.py
```

### Demo CURL Commands

1. **Test Inference API**:
   ```bash
   curl -X POST http://localhost:8001/generate \
     -H "Content-Type: application/json" \
     -d '{"model_id": "qwen3:4b-instruct-2507-q4_K_M", "messages": [{"role": "user", "content": "Reply in 3 words: system state?"}]}'
   ```

2. **Test Document OCR + Structuring**:
   ```bash
   curl -X POST "http://localhost:8002/analyze?mode=fast" \
     -F "file=@sample_data/test_report.png"
   ```
