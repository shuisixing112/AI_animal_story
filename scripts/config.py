# config.py

from pathlib import Path
from zoneinfo import ZoneInfo
from datetime import datetime
from utils import get_today_paths
from datetime import date


# === 今日日期資訊 ===
TIMEZONE = "Asia/Taipei"
tz = ZoneInfo(TIMEZONE)
now = datetime.now(tz)
TODAY = now.strftime("%Y-%m-%d")     # 格式為 2025-06-23
year = TODAY[:4]        # 格式為 "2025"
year_month = TODAY[:7]  # 格式為 "2025-06"
week_only = now.strftime("%W")     # 只取週數（兩位數字）       ##(%U)：一週從週日開始
week_num = f"W{date.today().isocalendar()[1]}" # 組成 "W26"    ##(%W)：一週從週一開始（通常ISO格式）
today_str = now.strftime("%Y-%m-%d %H:%M")  # 加入時間

# === 專案根目錄 ===
BASE_PATH = Path(__file__).resolve().parent.parent

# === 常用路徑變數 ===
THEME_PATH = BASE_PATH / "themes" / f"{year}_themes.json"
CHARACTERS_PATH = BASE_PATH / "characters"
LOGS_PATH = BASE_PATH / "logs"

# === 角色與主題 ===
# 自動初始化 today_paths（若不存在會建立）
today_paths = get_today_paths()


