from fastapi import FastAPI

app = FastAPI(title="RAG Enterprise Lab", version="0.1.0")

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "rag-enterprise-lab"}
