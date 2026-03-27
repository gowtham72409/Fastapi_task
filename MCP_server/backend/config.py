import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_URL= os.getenv("DATABASE_URL")
REDIS_URL= os.getenv("REDIS_URL")
HUBSPOT_ACCESS_TOKEN= os.getenv("HUBSPOT_ACCESS_TOKEN")