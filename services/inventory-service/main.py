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