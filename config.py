import os
from typing import List

API_ID = os.environ.get("API_ID", "21388641")
API_HASH = os.environ.get("API_HASH", "16f909bd213b2222a620d7641036834e")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7687664954:AAHmT5ljOC4W571RebEKQldi5gBzW5QDQEk")

ADMIN = int(os.environ.get("ADMIN", "6221939103 1078638766"))
PICS = (os.environ.get("PICS", "https://envs.sh/FT5.jpg")).split()

LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "-1002884841659"))

DB_URI = os.environ.get("DB_URI", "mongodb+srv://riyazahamed1806:d3corXDVXjrfS8NJ@cluster0.emcu0y2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = os.environ.get("DB_NAME", "Shortlinks")

IS_FSUB = os.environ.get("IS_FSUB", "True").lower() == "true"  # Set "True" For Enable Force Subscribe
AUTH_CHANNELS = list(map(int, os.environ.get("AUTH_CHANNEL", "-1001957183140").split())) # Add Multiple channel ids
