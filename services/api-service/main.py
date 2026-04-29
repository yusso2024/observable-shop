from fastapi import FastAPI
import redis, json, os, grpc
from kafka import KafkaProducer
import inventory_pb2
import inventory_pb2_grpc
from consul_register import register_with_consul, discover, get_kv

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

# --- Lab 6: Register with Consul on startup ---
@app.on_event("startup")
def startup():
    register_with_consul("api-service", 8000)

# --- Health endpoint (Consul checks this) ---
@app.get("/health")
def health():
    return {"status": "healthy"}

# --- Lab 3+6: gRPC client with Consul discovery ---
def get_items_from_grpc():
    target = discover("inventory-service")
    if target is None:
        target = "inventory-service:50051"
        print(f"Consul unavailable, using fallback: {target}")

    channel = grpc.insecure_channel(target)
    stub = inventory_pb2_grpc.InventoryServiceStub(channel)
    response = stub.GetItems(inventory_pb2.Empty())
    return list(response.items)

# --- Labs 2+3+6: Items with cache + gRPC + dynamic TTL ---
@app.get("/items")
def get_items():
    ttl = int(get_kv("cache_ttl", "30"))

    cached = r.get("items")
    if cached:
        return {"source": "cache", "items": json.loads(cached), "ttl": ttl}

    items = get_items_from_grpc()
    r.set("items", json.dumps(items), ex=ttl)
    return {"source": "grpc", "items": items, "ttl": ttl}

# --- Lab 5: Create order via Kafka ---
@app.post("/order")
def create_order(order: dict):
    if producer is None:
        return {"status": "error", "message": "Kafka not available"}
    producer.send("orders", order)
    producer.flush()
    return {"status": "queued", "order": order}