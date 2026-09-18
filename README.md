# My Part — LLM/Inference (M2) + Multimodal AI (M4)

Two independent FastAPI services:

- `inference_service/` — wraps Ollama, exposes the Inference API contract
  (`model_id + messages/images + config -> response + usage`)
- `multimodal_service/` — OCR (PaddleOCR) + VLM structuring, exposes the
  OCR/Vision API contract (`file/page/image -> text + structured fields + confidence + page refs`)

`multimodal_service` calls `inference_service` over HTTP — that's the same
pattern the Agent (M1) and RAG (M3) will use to call your models, so this
also proves your interface works end-to-end.

---

## Day 1 — get both services running locally

```bash
# 1. Install Ollama (one-time)
curl -fsSL https://ollama.com/install.sh | sh    # Linux
# or download from https://ollama.com/download   # Windows/Mac

# 2. Pull models (pick sizes that fit your machine — you have no GPU,
#    so start small and confirm speed before going bigger)
ollama pull qwen3:4b          # reasoning
ollama pull gemma3:4b         # vision-language (multimodal)
# optional, add once qwen3:4b speed is acceptable:
# ollama pull qwen3-coder:7b  # coding

# 3. Set up the inference service
cd inference_service
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001

# 4. In a second terminal, test it
curl -X POST http://localhost:8001/generate \
  -H "Content-Type: application/json" \
  -d '{"model_id": "qwen3:4b", "messages": [{"role": "user", "content": "Reply with one word: ready?"}]}'
```

If that returns a JSON response with `"response": "..."`, M2's part is working.

```bash
# 5. Set up the multimodal service (separate terminal)
cd multimodal_service
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8002

# 6. Test with any scanned document / photo of text you have
curl -X POST http://localhost:8002/analyze \
  -F "file=@/path/to/any_scanned_image.jpg"
```

**Day 1 exit goal:** both curl tests return real output. Commit + push now —
don't wait until everything is perfect.

```bash
git add inference_service multimodal_service
git commit -m "M2+M4: inference API + OCR/VLM pipeline, basic services running"
git push
```

---

## Day 2 — make it demo-ready

1. **Get a real sample scanned inspection report/photo** (even a phone photo
   of a printed page works) and drop it in `sample_data/`. Run it through
   `/analyze` and check the structured fields actually make sense — tune the
   prompt in `multimodal_service/main.py` if the VLM output is messy.
2. **Time it.** If `qwen3:4b` or `gemma3:4b` is too slow on your CPU, that's
   the moment to move to whichever teammate has a GPU, or fall back to an
   even smaller model (`qwen3:1.7b` / `gemma3:1b`) purely to keep the live
   demo responsive — quality can be lower, speed matters more on stage.
3. **Hand off the contract to M1 (Agent)** — they just need to know:
   - `POST http://localhost:8001/generate` for any reasoning/coding call
   - `POST http://localhost:8002/analyze` for any scanned doc/image
   Share this README + the two `main.py` files so they can wire it into
   the agent's tool calls.
4. **Sanity-check offline.** Turn off WiFi and re-run both curl tests — if
   they still work (models are local, no external API calls), that's your
   sovereignty proof for this half of the system.
5. Push again with a final commit before the demo.

---

## What to say if a judge asks about your part

- "We wrap Ollama behind a stable REST API so the rest of the team never
  has to care which model is actually running — we can swap in a bigger
  model on better hardware without touching any other module."
- "OCR runs fully offline via PaddleOCR; the vision-language model then
  turns raw OCR text plus the image itself into structured fields — so
  even messy scans get cross-checked visually, not just character-matched."