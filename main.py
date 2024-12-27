from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hi, How are you?"}


@app.get("/greeting/{name}")
def read_item(name: str):
    return {"item": f'Nice to you, {name}!'}
