from pymongo import MongoClient

uri = "mongodb+srv://karthikrishna465:HHzJWvpH9QMzNPek@backend.11lht.mongodb.net/?retryWrites=true&w=majority&appName=BACKEND"
client = MongoClient(uri, serverSelectionTimeoutMS=10000)

print(client.server_info())
print("Connected!")