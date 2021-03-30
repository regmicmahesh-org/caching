from fastapi import FastAPI, APIRouter
import json
from pydantic import BaseModel
from typing import Optional, List
import uuid

from azure.cosmos import CosmosClient, PartitionKey

import redis

from secret import COSMOS_SECRET, __default_config


def dev_client():
    return get_client(**__default_config)

def get_client(host, port, password):
    client = redis.Redis(host=host, port=port, password=password)
    return client


client = CosmosClient("https://maheshdb.documents.azure.com:443/", COSMOS_SECRET)

app = FastAPI(
    title="Todo Application",
    description="""
### Todo Application using Redis Caching

CRUD Application made to specifically operate with todos for very simple usecase. <br>
Every request you create are cached on redis and subsequently served from the redis server. <br>
Also, they're updated to sync with the database periodically.
    """)

cached_router = APIRouter(prefix="/todos")
db_router = APIRouter(prefix="/db")

todos_db = client.create_database_if_not_exists(id="todos")
todos_container = todos_db.create_container_if_not_exists(
    id="todos", partition_key=PartitionKey(path="/id"))
redis = dev_client()


class Todo(BaseModel):
    id: Optional[str] = None
    title: str
    description: str

class TodoRequest(BaseModel):
    title: str
    description: str

def add_to_db(todo: TodoRequest):
    new_todo = Todo(**todo.__dict__)
    new_todo.id = str(uuid.uuid4())
    todos_container.create_item(body=new_todo.__dict__)
    update_todo_cache(new_todo)
    return new_todo


def update_todo_cache(todo: Todo):
    redis.hset("todos", todo.id, json.dumps(todo.__dict__))


@app.get("/")
def homepage():
    return {"message" : "Ping Pong!"}

@cached_router.post("/", response_model=Todo)
def add_todo(todo: TodoRequest):
    added_data = add_to_db(todo)
    return added_data


@cached_router.get("/", response_model=List[Todo])
def get_all_todos():
    todos = redis.hvals("todos")
    dec = [json.loads(todo.decode('utf-8')) for todo in todos]
    return dec


@cached_router.delete("/{id}")
def delete_todo(id: str):
    print(id)
    todos_container.delete_item(id, partition_key=id)
    redis.hdel("todos", id)
    return {"message": "deleted"}

@cached_router.get("/{id}")
def get_todo(id: str):
    todo = json.loads(redis.hget("todos", id).decode('utf-8'))
    return todo
    
@db_router.get("/", response_model=List[Todo])
def get_all_from_database():
    items = []
    for i in todos_container.query_items("SELECT * from todos", enable_cross_partition_query=True):
        items.append(i)
    return items


app.include_router(db_router, tags=["db"])
app.include_router(cached_router, tags=["redis"])
