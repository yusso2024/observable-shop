from fastAPI import FastAPI
app = FastAPI()

@app.get("/items")
def get_items():
    return {"items": ["apple", "banana", "carrot"]}
    