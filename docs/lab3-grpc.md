### Transform the API service into a gRPC server and create a new microservice that consumes it._

# 🎯 **Objective**

Students will:

- Create a `.proto` contract
    
- Generate Python gRPC stubs
    
- Implement a gRPC server (Inventory Service)
    
- Implement a gRPC client (API Service)
    
- Replace internal HTTP calls with gRPC
    
- Prepare for observability (Jaeger + Prometheus in later labs)
    

# 🧩 **Student Workbook**

## Step 1 — Create the `.proto` Contract

📂 Location:

Código

```
observable-shop/proto/inventory.proto
```


```proto
syntax = "proto3";
package inventory;
service InventoryService {
  rpc GetItems (Empty) returns (ItemList);
}
message Empty {}
message ItemList {
  repeated string items = 1;
}
```

## Step 2 — Generate gRPC Stubs

From the repo root:
Two steps:

**Step 1 — Generate** from the `.proto` file:

```python
python -m grpc_tools.protoc \
  -I proto \
  --python_out=services/inventory-service \
  --grpc_python_out=services/inventory-service \
  proto/inventory.proto
```

This reads `inventory.proto` and generates two files in `services/inventory-service/`:

- `inventory_pb2.py` — message classes (Empty, ItemList)
- `inventory_pb2_grpc.py` — server/client stubs (InventoryServiceServicer, InventoryServiceStub)

**Step 2 — Copy** to api-service (it needs the same stubs to be a client):

```bash
cp services/inventory-service/inventory_pb2.py services/api-service/
cp services/inventory-service/inventory_pb2_grpc.py services/api-service/
```

The flags:

- `-I proto` — look for `.proto` files in the `proto/` directory
- `--python_out=` — where to write the message classes
- `--grpc_python_out=` — where to write the server/client stubs

Every time you change `inventory.proto`, you re-run both steps.
## Step 3 — Implement the gRPC Server

📂 Location:

Código

```
observable-shop/services/inventory-service/main.py
```


```python
import grpc
from concurrent import futures
import time

import inventory_pb2
import inventory_pb2_grpc

class InventoryService(inventory_pb2_grpc.InventoryServiceServicer):
    def GetItems(self, request, context):
        items = ["apple", "banana", "carrot"]
        return inventory_pb2.ItemList(items=items)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    inventory_pb2_grpc.add_InventoryServiceServicer_to_server(InventoryService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("Inventory gRPC server running on port 50051")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
```

#### Code Explanation
```python
import grpc                        # gRPC framework
from concurrent import futures     # Thread pool for handling multiple requests
import time

import inventory_pb2               # Generated from your .proto file — message definitions
import inventory_pb2_grpc          # Generated from your .proto file — server/client stubs

# This class implements the InventoryService defined in your .proto:
#   service InventoryService {
#     rpc GetItems (Empty) returns (ItemList);
#   }
class InventoryService(inventory_pb2_grpc.InventoryServiceServicer):

    # This method runs when a client calls GetItems()
    # "request" = the Empty message from the client
    # "context" = gRPC metadata (deadlines, cancellation, etc.)
    def GetItems(self, request, context):
        items = ["apple", "banana", "carrot"]
        # Return an ItemList message (defined in .proto)
        return inventory_pb2.ItemList(items=items)

def serve():
    # Create a gRPC server with 10 worker threads
    # Each thread handles one request — 10 concurrent requests max
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Register our InventoryService class as the handler
    inventory_pb2_grpc.add_InventoryServiceServicer_to_server(InventoryService(), server)

    # Listen on port 50051 (gRPC standard port)
    # [::] means all interfaces (IPv4 + IPv6)
    server.add_insecure_port("[::]:50051")

    # Start accepting requests
    server.start()
    print("Inventory gRPC server running on port 50051")

    # Block forever — keep the server running until killed
    # Without this, the script would exit immediately
    server.wait_for_termination()

# Python entry point — only runs when executed directly, not when imported
if __name__ == "__main__":
    serve()
## Step 4 — Update `docker-compose.yml`

```

The connection to your `.proto` file:

```
.proto defines:                     Python implements:
─────────────────                   ──────────────────
service InventoryService {    →     class InventoryService(Servicer):
  rpc GetItems(Empty)         →       def GetItems(self, request, context):
    returns (ItemList);       →         return ItemList(items=[...])
}
```

The `.proto` is the contract. This file is the implementation. The generated `_pb2` files are the glue between them.
Add the new service:

```yml
services:
  inventory:
    build: ./services/inventory-service
    container_name: inventory-service
    ports:
      - "50051:50051"
```

## Step 5 — Modify API Service to Call gRPC Instead of Local Logic

📂 Location:

Código

```
observable-shop/services/api-service/main.py
```


```python
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
```

This is the cumulative approach — each lab adds to the previous one:

- **Lab 1**: FastAPI + Traefik → still there (docker-compose, gateway)
- **Lab 2**: Redis caching → still there (cache check before gRPC)
- **Lab 3**: gRPC → replaces the hardcoded `["apple", "banana", "carrot"]` with a call to inventory service

For each service:

**`services/api-service/requirements.txt`**

```
fastapi
uvicorn[standard]
redis
grpcio
grpcio-tools
protobuf
```

**`services/inventory-service/requirements.txt`**

```
grpcio
grpcio-tools
protobuf
```

Each service only lists what it needs — api-service needs FastAPI, Redis, and gRPC. Inventory service only needs gRPC.


---

## Step 6 — Rebuild and Test


```bash
docker-compose up --build
```

Test:


```bash
docker exec -it redis redis-cli DEL items
curl http://localhost:8200/items
curl http://localhost:8200/items
```

Expected:

```

```bash
(integer) 0
{"source":"grpc","items":["apple","banana","carrot"]}{"source":"cache","items":["apple","banana","carrot"]}
```

## Step 7— Add in ci.yml for the pipelines
```yml
  build-services:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [api-service, inventory-service]
```
# 🧠 **Reflection Questions**

1. Why is gRPC faster than REST?
    
2. What role does the `.proto` file play?
    
3. How does gRPC enforce strong typing?
    
4. How would you add a new RPC method?
    

# 📗 **Teacher’s Answer Key**

### ✔ Step 1

Students should understand `.proto` as the **contract** between services.

### ✔ Step 2

Stub files appear in `services/inventory-service/`.

### ✔ Step 3

gRPC server prints:

Código

```
Inventory gRPC server running on port 50051
```

### ✔ Step 4

`docker-compose` now includes the inventory service.

### ✔ Step 5

API service successfully calls the gRPC server.

### ✔ Reflection Answers

1. gRPC uses HTTP/2 + Protobuf → smaller, faster messages.
    
2. `.proto` defines messages + RPC methods.
    
3. Protobuf enforces schemas → no mismatched fields.
    
4. Add method to `.proto`, regenerate stubs, implement server + client.
    

# 🎓 **Why Lab 3 Matters**

Students now understand:

- RPC communication
    
- Protobuf schemas
    
- Service‑to‑service communication
    
- How microservices talk internally
    
- How to structure multi‑service architectures
    

This prepares them for:

- **Lab 4: Batfish** (network validation)
    
- **Lab 5: Kafka** (event‑driven architecture)
    
- **Lab 6: Consul** (service discovery)
    
- **Lab 7: Kubernetes** (orchestration)
    
- **Lab 8: Vault** (secrets)
    
- **Lab 9: Chaos** (resilience)