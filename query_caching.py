from fastapi import FastAPI
import json
from pydantic import BaseModel
import redis
from azure.cosmos import CosmosClient, PartitionKey
from typing import List
import uuid
from secret import __default_config, COSMOS_SECRET

client = CosmosClient("https://maheshdb.documents.azure.com:443/",COSMOS_SECRET)


books_db = client.create_database_if_not_exists(id="books")
books_container = books_db.create_container_if_not_exists(id="books", partition_key=PartitionKey(path="/id"))

redis = redis.Redis(**__default_config)

app = FastAPI()


class BookRequest(BaseModel):
    name: str
    price: float

class Book(BookRequest):
    id: str

@app.get("/", response_model=List[Book])
def get_all_items():
    query = "SELECT * from books"
    if books := redis.get(query):
        data = json.loads(books)
        return data
    books = []
    for i in books_container.query_items(query, enable_cross_partition_query=True):
        books.append(i)
    redis.set(query, json.dumps(books), ex=5)
    return books

@app.post("/", response_model=Book)
def add_item(reqBook: BookRequest):
    id = str(uuid.uuid4())
    book = Book(**reqBook.__dict__, id=id)
    books_container.create_item(body=book.__dict__)
    return book
    
@app.get("/{id}", response_model=Book)
def get_item(id: str):
    query = f"SELECT * from books b WHERE b.id='{id}'"
    if book := redis.get(query):
        data = json.loads(book)
        return data
    book = None
    for i in books_container.query_items(query, enable_cross_partition_query=True):
        book = i
    if book:
        redis.set(query, json.dumps(book), ex=250)
    return book


