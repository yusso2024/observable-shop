## 🎯 Objective

Students will deploy Traefik as an API gateway and load balancer, configure routes, and observe traffic flow into microservices.

## 🧩 Student Workbook

### Step 1 — Setup Traefik

- Add Traefik to `docker-compose.yml`:
    ```yaml
    services:
      traefik:
        image: traefik:v2.10
        command:
          - "--api.insecure=true"
          - "--providers.docker=true"
          - "--entrypoints.web.address=:80"
        ports:
          - "80:80"
          - "8080:8080"
        volumes:
          - /var/run/docker.sock:/var/run/docker.sock
    ```
    

✅ **Checkpoint:** Visit `http://localhost:8080` → Traefik dashboard should load.

### Step 2 — Configure Routes

- Create `gateway/dynamic/routes.yml`:

    ```yaml
    http:
      routers:
        api:
          rule: "PathPrefix(`/api`)"
          service: api-service
          entryPoints:
            - web
      services:
        api-service:
          loadBalancer:
            servers:
              - url: "http://api:8000"
    ```
    

✅ **Checkpoint:** Requests to `/api/items` should route to API service.

### Step 3 — Add Middleware

- Extend `routes.yml` with rate limiting:
```yaml
        http:
      middlewares:
        ratelimit:
          rateLimit:
            average: 100
            burst: 50
      routers:
        api:
          rule: "PathPrefix(`/api`)"
          service: api-service
          entryPoints:
            - web
          middlewares:
            - ratelimit
    ```
```

✅ **Checkpoint:** Excessive requests should be throttled.

### Step 4 — Observe Traffic

- Send requests with `curl` or Postman.
    
- Watch Traefik dashboard for routing activity.
    
- Note how requests are balanced across replicas.
    

## 🧠 Reflection Questions

1. What happens if Traefik is removed from the stack?
    
2. How does middleware improve reliability?
    
3. How would you extend this config for HTTPS?
    

## 📗 Teacher’s Answer Key

- **Step 1:** Traefik dashboard confirms gateway is running.
    
- **Step 2:** `/api/items` routes correctly to API service.
    
- **Step 3:** Rate limiting middleware throttles requests beyond 100/s average.
    
- **Step 4:** Traefik dashboard shows load balancing across replicas.
    
- **Reflection:**
    
    1. Without Traefik, services must be exposed individually → less scalable.
        
    2. Middleware adds resilience (rate limiting, retries, circuit breakers).
        
    3. HTTPS requires certs via Let’s Encrypt or manual TLS config.

# ✅ **UPDATED LAB 1 — Traefik Gateway**

_(Aligned with final repo structure)_

### 📂 Files go in:

Código

```
observable-shop/gateway/
observable-shop/gateway/dynamic/
observable-shop/docker-compose.yml
```

### 📘 Student Workbook (updated)

**docker-compose.yml**


```yaml
services:
  traefik:
    image: traefik:v2.10
    container_name: traefik
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
    ports:
      - "80:80"
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock

  api:
    build: ./services/api-service
    container_name: api-service
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=PathPrefix(`/api`)"
      - "traefik.http.services.api.loadbalancer.server.port=8000"
```

**gateway/dynamic/routes.yml** _(Optional for advanced routing)_

Everything now lives in the correct folders.


---
> [!CAUTION] Some files needed to change!
### Fixed files due to versions and port issues
The Traefik files that work with your Docker 29.x:

### `docker-compose.yml`

```yml
services:
  api-service:
    build: ./services/api-service
    ports:
      - "8200:8000"

  traefik:
    image: traefik:v2.10
    command:
      - "--api.insecure=true"
      - "--providers.file.filename=/etc/traefik/routes.yml"
      - "--providers.file.watch=true"
      - "--entrypoints.web.address=:80"
    ports:
      - "8180:80"
      - "8280:8080"
    [^1]volumes:
      - ./gateway/dynamic/routes.yml:/etc/traefik/routes.yml:ro
```

### `gateway/dynamic/routes.yml`

```yml
http:
  middlewares:
    ratelimit:
      rateLimit:
        average: 5
        burst: 10

  routers:
    api:
      rule: "PathPrefix(`/`)"
      entryPoints:
        - web
      service: api-service
      middlewares:
        - ratelimit

  services:
    api-service:
      loadBalancer:
        servers:
          - url: "http://api-service:8000"
```

Key things already fixed:

- **File provider** instead of Docker provider (avoids API version error)
- **Ports 8180/8280** instead of 80/8080 (avoid Caddy and Terraform conflicts)
- **Rate limit at 5/10** for easy testing (change to 100/50 for production)

Paste both, rebuild with `docker compose up --build -d`, then test.


---
#### Explanation of how Traefik routes.yml file works:

```
http:                          # All rules are for HTTP traffic

  middlewares:                 # Plugins that modify requests BEFORE they reach your service
    ratelimit:                 # Name of this middleware (you reference it below)
      rateLimit:               # Type: rate limiter
        average: 5             # Allow 5 requests per second sustained
        burst: 10              # Allow up to 10 requests at once before throttling

  routers:                     # Rules that decide WHERE traffic goes
    api:                       # Name of this router
      rule: "PathPrefix(`/`)"  # Match ANY request (everything starts with /)
      entryPoints:
        - web                  # Only listen on the "web" entrypoint (port 80)
      service: api-service     # Send matched traffic to this service (defined below)
      middlewares:
        - ratelimit            # Apply the ratelimit middleware before forwarding

  services:                    # Backend targets (where traffic actually goes)
    api-service:               # Name (must match what the router references)
      loadBalancer:            # Traefik can balance across multiple instances
        servers:
          - url: "http://api-service:8000"  # Container name + internal port
```

The flow for every request:

```
Client request
    │
    ▼
Router: does the path match "PathPrefix(`/`)"?
    │ yes
    ▼
Middleware: is this request within the rate limit?
    │ yes → continue     │ no → return 429
    ▼
Service: forward to http://api-service:8000
    │
    ▼
Your FastAPI app responds
```

```
To test:

# API direct
curl http://localhost:8200/items

# Through Traefik
curl http://localhost:8180/items


# Traefik dashboard
# Open in browser: http://10.208.0.162:8280

  
# Test rate limiting
for i in $(seq 1 15); do
  echo -n "Request $i: "
  curl -s -o /dev/null -w "%{http_code}" http://localhost:8180/items
  echo
done
```
---
#### Traefik Dashboard elements
HTTP Services are the **backend targets** — where Traefik sends traffic after routing.

What you see on the dashboard:

|Service|What it is|
|---|---|
|**api-service@file**|Yours — points to [`http://api-service:8000`](http://api-service:8000/). The `@file` means it came from your `routes.yml`. Servers=1 means one backend instance.|
|**api@internal**|Traefik's own API endpoint (powers the dashboard data)|
|**dashboard@internal**|Traefik's dashboard UI (the page you're looking at)|
|**noop@internal**|Built-in no-op service (does nothing, used internally)|

The `@internal` ones are Traefik's own. You didn't create them — they exist automatically. The only one you defined is `api-service@file`.

If you scaled your API to 3 instances, `api-service@file` would show **Servers: 3** and Traefik would load-balance across them.
[^1]: `ro` = **read-only**.
	
	The container can read the file but cannot modify it. If Traefik had a bug that tried to overwrite its own config, the write would fail.
	
	Without `:ro`, the container could write back to your VM's file. You don't want that — your config files are source-controlled. Only you should change them.
	
	```
	:ro  = read-only  (container can read, not write)
	:rw  = read-write (default if you omit it)
	```