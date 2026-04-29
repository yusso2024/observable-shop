### _Enable microservices to discover each other dynamically and store configuration centrally._

# 🎯 **Objective**

Students will:

- Deploy Consul as a service discovery platform
    
- Register microservices automatically
    
- Query Consul for service locations
    
- Use Consul KV store for dynamic configuration
    
- Prepare the architecture for Kubernetes + Vault
    

# 🧩 **Student Workbook**

| File                                          | Action    | What                                   |
| --------------------------------------------- | --------- | -------------------------------------- |
| `discovery/consul/server.json`                | Write     | Consul config                          |
| `docker-compose.yml`                          | Update    | Add consul service                     |
| `services/api-service/requirements.txt`       | Update    | Add `requests`                         |
| `services/api-service/consul_register.py`     | Create    | Helper: register, discover, get_kv     |
| `services/api-service/main.py`                | Update    | Add Consul registration, discovery, KV |
| `services/inventory-service/requirements.txt` | Update    | Add `requests`                         |
| `services/inventory-service/main.py`          | Update    | Add self-registration to Consul        |
| `.github/workflows/ci.yml`                    | No change | No new services                        |
## Step 1 — Create the Consul Folder Structure

📂 Location:

Código

```
observable-shop/discovery/consul/
└── server.json
```

### `server.json`

json

```json
{
  "datacenter": "dc1",
  "server": true,
  "bootstrap_expect": 1,
  "ui": true,
  "client_addr": "0.0.0.0"
}
```

## Step 2 — Add Consul to `docker-compose.yml`


```yaml
services:
  consul:
    image: consul:1.17
    container_name: consul
    ports:
      - "8500:8500"
      - "8600:8600/udp"
    volumes:
      - ./discovery/consul/server.json:/consul/config/server.json
```

Start it:

bash

```bash
docker-compose up -d consul
```

Open UI:

Código

```
http://localhost:8500
```

## Step 3 — Register Services Automatically (API, Inventory, Order)

Add labels to each service in `docker-compose.yml`:

### API Service

yaml

```yaml
  api:
    build: ./services/api-service
    container_name: api-service
    labels:
      - "consul.enable=true"
      - "consul.service.name=api"
      - "consul.service.port=8000"
```

### Inventory Service

yaml

```
  inventory:
    build: ./services/inventory-service
    container_name: inventory-service
    labels:
      - "consul.enable=true"
      - "consul.service.name=inventory"
      - "consul.service.port=50051"
```

### Order Service

yaml

```
  order:
    build: ./services/order-service
    container_name: order-service
    labels:
      - "consul.enable=true"
      - "consul.service.name=order"
      - "consul.service.port=9000"
```

> **Nota:** Para que esto funcione, usamos un sidecar ligero llamado **registrator**.

## Step 4 — Add Registrator (Auto‑Registration)

Append to `docker-compose.yml`:

yaml

```
  registrator:
    image: gliderlabs/registrator:latest
    container_name: registrator
    command: ["consul://consul:8500"]
    volumes:
      - /var/run/docker.sock:/tmp/docker.sock
    depends_on:
      - consul
```

Registrator detecta contenedores y los registra automáticamente en Consul.

## Step 5 — Verify Service Registration

Open:

Código

```
http://localhost:8500/ui/dc1/services
```

You should see:

- api
    
- inventory
    
- order
    
- consul
    

## Step 6 — Query Consul from API Service

Modify `services/api-service/main.py`:

python

```
import requests

def discover(service):
    url = f"http://consul:8500/v1/catalog/service/{service}"
    res = requests.get(url).json()
    if not res:
        return None
    svc = res[0]
    return f"{svc['ServiceAddress']}:{svc['ServicePort']}"
```

Use it in gRPC client:

python

```
def get_items_from_grpc():
    target = discover("inventory")
    channel = grpc.insecure_channel(target)
    stub = inventory_pb2_grpc.InventoryServiceStub(channel)
    response = stub.GetItems(inventory_pb2.Empty())
    return response.items
```

Now API Service dynamically discovers Inventory Service.

## Step 7 — Use Consul KV Store for Dynamic Config

Set a value:

Código

```
curl -X PUT -d "30" http://localhost:8500/v1/kv/cache_ttl
```

Read it from API Service:

python

```
def get_cache_ttl():
    res = requests.get("http://consul:8500/v1/kv/cache_ttl?raw=true")
    return int(res.text)
```

Use it in Redis caching logic:

python

```
ttl = get_cache_ttl()
r.set("items", json.dumps(items), ex=ttl)
```

Now TTL is dynamic and centrally managed.

# 🧠 **Reflection Questions**

1. Why is service discovery important in microservices?
    
2. What happens if a service changes IP or port?
    
3. How does Consul KV differ from environment variables?
    
4. How would you use Consul for feature flags?
    

# 📗 **Teacher’s Answer Key**

### ✔ Step 1

Consul config loads correctly.

### ✔ Step 2

Consul UI accessible at port 8500.

### ✔ Step 3

Services appear automatically in Consul after adding Registrator.

### ✔ Step 4

Registrator logs show:

Código

```
Registering service api
Registering service inventory
Registering service order
```

### ✔ Step 5

Consul UI shows all services.

### ✔ Step 6

API Service successfully discovers Inventory Service dynamically.

### ✔ Step 7

TTL changes in Consul KV immediately affect Redis caching behavior.

### ✔ Reflection Answers

1. Avoids hardcoding IPs; supports scaling and dynamic environments.
    
2. Consul updates registry; clients discover new location automatically.
    
3. KV store is dynamic and centralized; env vars require redeploy.
    
4. Store flags in KV and read them at runtime.
    

# 🎓 **Why Lab 6 Matters**

Students now understand:

- Dynamic service discovery
    
- Auto‑registration
    
- Centralized configuration
    
- How microservices adapt to changing environments
    
- How Consul prepares the system for Kubernetes and Vault
    

This lab is a turning point: the architecture becomes **dynamic, scalable, and production‑ready**.