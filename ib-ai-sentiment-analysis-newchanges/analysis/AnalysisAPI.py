from fastapi import FastAPI
from pydantic import BaseModel
import threading
import time

from analysispipeline import run_analysis #ask_ai_about_call   # import both

app = FastAPI()

# ============================================================
# BACKGROUND WORKER
# ============================================================

def analysis_worker():

    print("🚀 Analysis worker started...")

    while True:
        try:
            run_analysis()
        except Exception as e:
            print("❌ Error in analysis worker:", e)

        time.sleep(10)  # check every 10 seconds


# ============================================================
# START WORKER WHEN API STARTS
# ============================================================

@app.on_event("startup")
def start_worker():

    thread = threading.Thread(target=analysis_worker)
    thread.daemon = True
    thread.start()


# ============================================================
# AI QUESTION MODEL
# ============================================================

class AskRequest(BaseModel):
    call_id: str
    question: str


# ============================================================
# AI QUESTION ENDPOINT
# ============================================================

'''@app.post("/ask_call_ai")
def ask_call(req: AskRequest):

    try:
        answer = ask_ai_about_call(req.call_id, req.question)

        return {
            "call_id": req.call_id,
            "question": req.question,
            "answer": answer
        }

    except Exception as e:
        return {
            "error": str(e)
        }'''


# ============================================================
# OPTIONAL API ENDPOINTS
# ============================================================

@app.get("/")
def home():
    return {"message": "Call Analysis API running"}

@app.get("/health")
def health():
    return {"status": "OK"}