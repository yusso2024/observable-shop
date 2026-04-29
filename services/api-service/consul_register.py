import requests
import os
import time
import socket

def register_with_consul(service_name, service_port):
    consul_host = os.getenv("CONSUL_HOST", "consul")
    service_id = f"{service_name}-{socket.gethostname()}"

    payload = {
        "ID": service_id,
        "Name": service_name,
        "Address": service_name,
        "Port": int(service_port),
        "Check": {
            "HTTP": f"http://{service_name}:{service_port}/health",
            "Interval": "10s",
            "Timeout": "3s"
        }
    }

    for attempt in range(10):
        try:
            res = requests.put(
                f"http://{consul_host}:8500/v1/agent/service/register",
                json=payload
            )
            if res.status_code == 200:
                print(f"Registered '{service_name}' with Consul (ID: {service_id})")
                return True
        except Exception as e:
            print(f"Waiting for Consul (attempt {attempt+1}/10): {e}")
        time.sleep(3)

    print("WARNING: Could not register with Consul")
    return False

def discover(service_name):
    consul_host = os.getenv("CONSUL_HOST", "consul")
    try:
        res = requests.get(f"http://{consul_host}:8500/v1/catalog/service/{service_name}")
        services = res.json()
        if not services:
            return None
        svc = services[0]
        addr = svc["ServiceAddress"] or svc["Address"]
        port = svc["ServicePort"]
        return f"{addr}:{port}"
    except Exception as e:
        print(f"Consul discovery failed for {service_name}: {e}")
        return None

def get_kv(key, default=None):
    consul_host = os.getenv("CONSUL_HOST", "consul")
    try:
        res = requests.get(f"http://{consul_host}:8500/v1/kv/{key}?raw=true")
        if res.status_code == 200:
            return res.text
        return default
    except:
        return default