
import os
import firebase_admin
from firebase_admin import credentials, storage
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
load_dotenv()

BUCKET_NAME = os.getenv("BUCKET_NAME")

# === 今日日期資訊 ===
TIMEZONE = "Asia/Taipei"
now = datetime.now(ZoneInfo(TIMEZONE))
TODAY = now.strftime("%Y-%m-%d")
year = TODAY[:4]
month = TODAY[5:7]
year_month = TODAY[:7]

# 初始化一次即可
def initialize_firebase():
    Firebase_API_KEY = os.getenv("Firebase_Admin_SDK")
    if not firebase_admin._apps:
        cred = credentials.Certificate(Firebase_API_KEY)
        firebase_admin.initialize_app(cred, {"storageBucket": BUCKET_NAME})

def get_bucket():
    initialize_firebase()
    return storage.bucket()

# === Firsbase檔案與日誌工具 ===
def read_txt_from_firebase(path: str) -> str:
    bucket = storage.bucket(BUCKET_NAME)
    blob = bucket.blob(str(path))
    if not blob.exists():
        raise FileNotFoundError(f"Firebase 檔案不存在：{path}")
    return blob.download_as_text(encoding="utf-8")
def write_txt_to_firebase(path: str, content: str):
    bucket = storage.bucket(BUCKET_NAME)
    blob = bucket.blob(str(path))
    blob.upload_from_string(content, content_type="text/plain")

# === Firsbase路徑管理 ===
def get_theme_path(year: int, week_num: str) -> str:
    return f"themes/{year}/{month}_{week_num}_theme.json"
def get_story_txt_path(character_id: str, year: int, week_num: str) -> str:
    return f"characters/{character_id}/{year}/2025_{week_num}.txt"
def get_log_json_path(character_id: str, date: str, topic_slug: str) -> str:
    return f"logs/characters/{character_id}/{date}_{topic_slug}_log.json"
def get_error_log_path(date: str) -> str:
    return f"logs/errors/{date}_error.json"
def get_memory_summary_path(character_id: str, week_num: str) -> str:
    return f"memory/{character_id}/summary_week_{week_num}.txt"
def get_memory_items_path(character_id: str, year_month: str) -> str:
    return f"memory/{character_id}/memory_{year_month}.json"
