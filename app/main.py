from fastapi import FastAPI

app = FastAPI(title="App")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
