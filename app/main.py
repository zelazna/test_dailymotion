from fastapi import FastAPI, status

app = FastAPI(title="User Registration API", version="1.0.0")


@app.get(
    "/status",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
async def status_check() -> dict:
    return {"status": "ok"}
