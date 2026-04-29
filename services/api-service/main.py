from fastapi import FastAPI
app = FastAPI()
import redis, json, time, os

app = FastAPI()

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=6379,
    decode_responses=True
)

@app.get("/items")
def get_items():
    cached = r.get("items")
    if cached:
        return {"source": "cache", "items": json.loads(cached)}

    time.sleep(1)
    items = ["apple", "banana", "carrot"]

    r.set("items", json.dumps(items), ex=30)

    return {"source": "db", "items": items}
