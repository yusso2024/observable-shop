from fastapi import FastAPI
import redis, json, os, grpc
import inventory_pb2
import inventory_pb2_grpc

app = FastAPI()

# Lab 2 — Redis cache
r = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=6379,
    decode_responses=True
)

# Lab 3 — gRPC client
def get_items_from_grpc():
    channel = grpc.insecure_channel("inventory:50051")
    stub = inventory_pb2_grpc.InventoryServiceStub(channel)
    response = stub.GetItems(inventory_pb2.Empty())
    return list(response.items)

@app.get("/items")
def get_items():
    # Check cache first (Lab 2)
    cached = r.get("items")
    if cached:
        return {"source": "cache", "items": json.loads(cached)}

    # Cache miss — call gRPC (Lab 3, replaces hardcoded list)
    items = get_items_from_grpc()
    r.set("items", json.dumps(items), ex=30)
    return {"source": "grpc", "items": items}