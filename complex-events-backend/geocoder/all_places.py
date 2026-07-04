from pymongo import MongoClient
client = MongoClient('localhost', 27017)
db = client['complex_events']
collection = db.extract_results
collection_lng_lat_result = db['places_lng_lat']

for extract in collection.find():
    print(extract)



