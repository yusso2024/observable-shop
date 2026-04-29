### _Introduce asynchronous messaging with Kafka and build the Order Service._

# 🎯 **Objective**

Students will:

- Deploy Kafka + Zookeeper
    
- Create a topic (`orders`)
    
- Build a new microservice: **Order Service**
    
- Produce events from API Service
    
- Consume events in Order Service
    
- Understand async communication patterns
    
- Prepare for later labs (Consul, Kubernetes, Vault)
    

# 🧩 **Student Workbook**

## Step 1 — Add Kafka to the Repo Structure

📂 Location:

Código

```
observable-shop/messaging/kafka/
├── docker-compose.override.yml
└── topics-init.sh
```

## Step 2 — Add Kafka Services to `docker-compose.yml`

Append:

```yml
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
    ports:
      - "2181:2181"

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
```

## Step 3 — Create the `orders` Topic

📂 `messaging/kafka/topics-init.sh`


```bash
#!/bin/bash
kafka-topics --create \
  --topic orders \
  --bootstrap-server kafka:9092 \
  --partitions 1 \
  --replication-factor 1
```

Run:

bash

```
docker exec -it kafka bash /topics-init.sh
```

## Step 4 — Create the Order Service

📂 Location:

```
observable-shop/services/order-service/
```

### `requirements.txt`


```
kafka-python
fastapi
uvicorn[standard]
```

### `main.py`


```python
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
```

Also the requirements updated:
```
fastapi
uvicorn[standard]
redis
grpcio
grpcio-tools
protobuf
kafka-python-ng
```
## Step 5 — Add Order Service to `docker-compose.yml`


```yml
services:
  order:
    build: ./services/order-service
    container_name: order-service
    depends_on:
      - kafka
```

## Step 6 — Modify API Service to Produce Kafka Events

📂 `services/api-service/main.py`

Add:

python

```python
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers=["kafka:9092"],
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

@app.post("/order")
def create_order(order: dict):
    producer.send("orders", order)
    producer.flush()
    return {"status": "queued", "order": order}
```

## Step 7 — Test the Flow

Start everything:

bash

```
docker-compose up --build
```

Send an order:

bash

```
curl -X POST http://localhost:8200/order \
  -H "Content-Type: application/json" \
  -d '{"item": "apple", "qty": 3}'
```

Expected:

### API Service output:

Código

```
{"status": "queued", "order": {"item": "apple", "qty": 3}}
```

### Order Service logs:

Código

```
Processing order: {'item': 'apple', 'qty': 3}
```

# 🧠 **Reflection Questions**

1. Why is asynchronous messaging useful in microservices?
    
2. What happens if the Order Service is down when events are produced?
    
3. How would you scale the Order Service horizontally?
    
4. How would you add a second topic (e.g., `payments`)?
    

# 📗 **Teacher’s Answer Key**

### ✔ Step 1

Kafka folder created under `messaging/`.

### ✔ Step 2

Kafka + Zookeeper containers run successfully.

### ✔ Step 3

Topic `orders` appears in:

Código

```
kafka-topics --list --bootstrap-server kafka:9092
```

### ✔ Step 4

Order Service prints:

Código

```
Order Service listening for events...
```

### ✔ Step 5

Order Service container starts without errors.

### ✔ Step 6

API Service produces events to Kafka.

### ✔ Step 7

Order Service consumes events and prints them.

### ✔ Reflection Answers

1. Decouples services, improves resilience, smooths traffic spikes.
    
2. Kafka stores events until consumers come back online.
    
3. Kafka partitions + consumer groups.
    
4. Create new topic + new producer/consumer logic.
    

# 🎓 **Why Lab 5 Matters**

Students now understand:

- Event‑driven architecture
    
- Asynchronous communication
    
- Kafka topics, producers, consumers
    
- Decoupling microservices
    
- Building resilient pipelines
    

This prepares them for:

- **Lab 6 — Consul (Service Discovery)**
    
- **Lab 7 — Kubernetes (Orchestration)**
    
- **Lab 8 — Vault (Secrets)**
    
- **Lab 9 — Chaos Engineering**
    
- **Capstone: Observable Shop**
    

If you want, I can now generate **Lab 6 — Consul**, where students add service discovery and dynamic configuration to the architecture.
