from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel
import os

app = FastAPI()

# ✅ CORS setup — allows frontend (Vercel) to call backend (Render)
allowed_origins = [
    "https://lightsignal-frontend.vercel.app",
    "https://*.vercel.app",
    "http://localhost:3000"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ API Key and Project ID (keep these secret in Render env vars)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_PROJECT = os.getenv("OPENAI_PROJECT")

client = OpenAI(api_key=OPENAI_API_KEY, project=OPENAI_PROJECT)

class PromptRequest(BaseModel):
    prompt: str

@app.get("/health")
async def health():
    return {"ok": True, "project": OPENAI_PROJECT}

@app.post("/api/orchestrator")
async def orchestrator(request: PromptRequest):
    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are the LightSignal Orchestrator assistant."},
                {"role": "user", "content": request.prompt}
            ],
            response_format={"type": "json_object"}
        )
        return response.choices[0].message
    except Exception as e:
        return {"error": str(e)}
