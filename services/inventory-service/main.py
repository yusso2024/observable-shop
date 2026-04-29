import grpc
from concurrent import futures
import requests
import os
import time
import socket
import threading

import inventory_pb2
import inventory_pb2_grpc

class InventoryService(inventory_pb2_grpc.InventoryServiceServicer):
    def GetItems(self, request, context):
        items = ["apple", "banana", "carrot"]
        return inventory_pb2.ItemList(items=items)

def register_with_consul():
    consul_host = os.getenv("CONSUL_HOST", "consul")
    service_name = "inventory-service"
    service_port = 50051
    service_id = f"{service_name}-{socket.gethostname()}"

    payload = {
        "ID": service_id,
        "Name": service_name,
        "Address": service_name,
        "Port": service_port,
        "Check": {
            "TCP": f"{service_name}:{service_port}",
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
                print(f"Registered with Consul (ID: {service_id})")
                return
        except Exception as e:
            print(f"Waiting for Consul (attempt {attempt+1}/10): {e}")
        time.sleep(3)
    print("WARNING: Could not register with Consul")

def serve():
    threading.Thread(target=register_with_consul, daemon=True).start()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    inventory_pb2_grpc.add_InventoryServiceServicer_to_server(InventoryService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("Inventory gRPC server running on port 50051")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()