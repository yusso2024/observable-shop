from fastapi import FastAPI
import redis, json, os, grpc
from kafka import KafkaProducer
import inventory_pb2
import inventory_pb2_grpc

app = FastAPI()

# --- Lab 2: Redis cache ---
r = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=6379,
    decode_responses=True
)

# --- Lab 5: Kafka producer ---
producer = None
try:
    producer = KafkaProducer(
        bootstrap_servers=["kafka:9092"],
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        retries=5
    )
    print("Kafka producer connected")
except Exception as e:
    print(f"WARNING: Kafka not available: {e}")

# --- Lab 3: gRPC client ---
def get_items_from_grpc():
    channel = grpc.insecure_channel("inventory:50051")
    stub = inventory_pb2_grpc.InventoryServiceStub(channel)
    response = stub.GetItems(inventory_pb2.Empty())
    return list(response.items)

# --- Lab 1: Health endpoint ---
@app.get("/health")
def health():
    return {"status": "healthy"}

# --- Labs 2+3: Items with cache + gRPC ---
@app.get("/items")
def get_items():
    cached = r.get("items")
    if cached:
        return {"source": "cache", "items": json.loads(cached)}

    items = get_items_from_grpc()
    r.set("items", json.dumps(items), ex=30)
    return {"source": "grpc", "items": items}

# --- Lab 5: Create order via Kafka ---
@app.post("/order")
def create_order(order: dict):
    if producer is None:
        return {"status": "error", "message": "Kafka not available"}
    producer.send("orders", order)
    producer.flush()
    return {"status": "queued", "order": order}