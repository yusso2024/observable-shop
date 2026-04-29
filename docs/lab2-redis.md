# ✅ **UPDATED LAB 2 — Redis Caching**

_(Aligned with final repo structure)_

### 📂 Files go in:

Código

```
observable-shop/cache/
observable-shop/services/api-service/
observable-shop/docker-compose.yml
```

### 📘 Student Workbook (updated)

**docker-compose.yml**

```yaml
services:
  redis:
    image: redis:7
    container_name: redis
    ports:
      - "6379:6379"

  api:
    build: ./services/api-service
    container_name: api-service
    depends_on:
      - redis
    environment:
      - REDIS_HOST=redis
```

**services/api-service/main.py**


```python
from fastapi import FastAPI
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
```

#### Code Explanations
```python
# 1. Ask Redis: "do you have a key called 'items'?"
cached = r.get("items")

# 2. If Redis has it → return immediately (fast, sub-millisecond)
if cached:
    #    cached is a JSON string: '["apple", "banana", "carrot"]'
    #    json.loads() converts it back to a Python list
    return {"source": "cache", "items": json.loads(cached)}

# 3. If Redis DOESN'T have it (cache miss) → we reach this code

# Simulate a slow database query (1 second delay)
# In real life, this would be an actual DB call
time.sleep(1)
items = ["apple", "banana", "carrot"]

# 4. Store the result in Redis for next time
#    json.dumps() converts the list to a string: '["apple", "banana", "carrot"]'
#    ex=30 means "expire after 30 seconds" (auto-delete)
r.set("items", json.dumps(items), ex=30)

# 5. Return the result
return {"source": "db", "items": items}
```

The flow:

```python
First call:   Redis empty → sleep 1s → get items → store in Redis → return "source: db"
Second call:  Redis has it → return instantly → "source: cache"
... 30 seconds later ...
Next call:    Redis expired the key → back to "source: db"
```

The `"source"` field tells you where the data came from — so you can see caching in action when you test with `curl`.
Everything now fits perfectly inside the final repo structure.

# 🎯 **You Now Have:**

- A **final, stable repo structure**
    
- A **Pre‑Lab** aligned with that structure
    
- **Lab 1 (Traefik)** aligned with that structure
    
- **Lab 2 (Redis)** aligned with that structure
    

Every future lab (gRPC, Kafka, Consul, Batfish, Kubernetes, Vault, Chaos, Capstone) will follow this same structure.


---
### Test
```bash
# First call — cache miss (slow, ~1 second)
curl http://localhost:8200/items
# Returns: {"source": "db", ...}

# Second call — cache hit (instant)
curl http://localhost:8200/items
# Returns: {"source": "cache", ...}

# Wait 30 seconds, then call again — cache expired
sleep 30 && curl http://localhost:8200/items
# Returns: {"source": "db", ...}

# Manually clear cache to force a miss
docker exec -it redis redis-cli DEL items
curl http://localhost:8200/items
# Returns: {"source": "db", ...}

# Check what's inside Redis
docker exec -it redis redis-cli GET items
# Returns: ["apple", "banana", "carrot"]

# Check TTL remaining
docker exec -it redis redis-cli TTL items
# Returns: seconds left before expiry
```