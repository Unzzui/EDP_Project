from dotenv import load_dotenv
import os
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
    SHEET_ID = os.getenv("SHEET_ID")