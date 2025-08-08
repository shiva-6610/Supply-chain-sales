from pymongo import MongoClient
import pandas as pd

def init_mongo_db(db_name, collection_name):
    client = MongoClient("mongodb://localhost:27017/")
    db = client[db_name]
    collection = db[collection_name]
    return collection

def insert_data_from_csv_to_mongo(db_name, collection_name, csv_path):
    df = pd.read_csv(csv_path)
    records = df.to_dict(orient='records')

    client = MongoClient("mongodb://localhost:27017/")
    db = client[db_name]
    collection = db[collection_name]

    if records:
        collection.insert_many(records)
        print(f"{len(records)} records inserted into '{collection_name}' collection.")
    else:
        print("No records to insert.")
