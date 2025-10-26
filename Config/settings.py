import os 

SECRET_KEY = os.getenv("SECRET_KEY")
MONGODB_URI = os.getenv("MONGODB_URI")
PREFIX_SERVER_PATH = '/api/v1'