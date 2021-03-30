import sys
import uuid
from random import uniform

from azure.cosmos import CosmosClient, PartitionKey
from faker import Faker

from secret import COSMOS_SECRET

faker = Faker()

client = CosmosClient("https://maheshdb.documents.azure.com:443/", COSMOS_SECRET)


books_db = client.create_database_if_not_exists(id="books")
books_container = books_db.create_container_if_not_exists(
    id="books", partition_key=PartitionKey(path="/id"))


for i in range(int(sys.argv[1])):
    item = {}
    item['id'] = str(uuid.uuid4())
    item['name'] = faker.name()
    item['price'] = round(uniform(50,2500), 2)

    books_container.create_item(item)
    print(item)
    print("-" * 30)
