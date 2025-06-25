# utils_common.py
import os
import json
import re
from firebase_admin import storage
import tiktoken
from datetime import datetime
from zoneinfo import ZoneInfo
from io import BytesIO
from PIL import Image
import requests
from dotenv import load_dotenv
from firebase_config import (
    get_bucket,
    read_txt_from_firebase,
    write_txt_to_firebase,
    get_theme_path,
    get_story_txt_path,
    get_log_json_path,
    get_error_log_path,
    get_memory_summary_path,
    get_memory_items_path,
)

load_dotenv()

# === 今日日期資訊 ===
TIMEZONE = "Asia/Taipei"
tz = ZoneInfo(TIMEZONE)
now = datetime.now(tz)
TODAY = now.strftime("%Y-%m-%d")     # 格式為 2025-06-23
year = TODAY[:4]        # 格式為 "2025"
month = TODAY[5:7]      # 結果會是 "06"
year_month = TODAY[:7]  # 格式為 "2025-06"

# === 日期與格式工具 ===
def get_today_date_str():
    taiwan_time = datetime.now(ZoneInfo("Asia/Taipei"))
    return taiwan_time.strftime("%Y-%m-%d")
def slugify(text):
    """
    將字串轉換為適合檔名的 slug（小寫並用底線取代特殊字元）。
    例如："Sharing & Friendship!" → "sharing_friendship"
    """
    return re.sub(r"[^a-zA-Z0-9]+", "_", text.strip()).lower()
def generate_imgbb_name(cid: str, theme_slug: str, index: int) -> str:
    """
    根據角色 ID、主題 slug 與編號產生唯一圖檔名稱
    範例格式：2025-06-23_152145_rabbit_chef_creative_cooking_01
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    return f"{timestamp}_{cid}_{theme_slug}_{index:02d}"
def sanitize_for_json(obj: dict) -> dict:                  #將Python的Path物件轉成字串，好存進JSON(JSON不能直接存PATH)
        if isinstance(obj, dict):
            return {k: sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [sanitize_for_json(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        else:
            return str(obj)

# === 雲端讀寫工具 ===
def log_and_print(message: str, error_type: str = "info"):
    print(message)

    # 設定檔案名稱與路徑
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    log_path = get_error_log_path(date_str)

    # 讀取現有 log 檔案（如果存在）
    try:
        bucket = get_bucket()
        blob = bucket.blob(log_path)
        if blob.exists():
            content = blob.download_as_text()
            log_data = json.loads(content)
        else:
            log_data = []
    except Exception as e:
        print(f"⚠️ 無法讀取現有錯誤日誌：{e}")
        log_data = []
        raise

    # 加入新紀錄
    log_entry = {
        "timestamp": now.isoformat(),
        "type": error_type,
        "message": message
    }
    log_data.append(log_entry)

    # 寫入 Firebase
    try:
        json_str = json.dumps(log_data, ensure_ascii=False, indent=2)
        blob.upload_from_string(json_str, content_type="application/json")
    except Exception as e:
        print(f"❌ 錯誤紀錄寫入失敗：{e}")
def update_log(log_path, updates: dict):
    """合併 log 資料並寫入 Firebase"""
    # 讀取原始資料
    try:
        log_data = read_json_from_firebase(str(log_path))
    except Exception:
        log_data = {}

    # 合併更新
    log_data.update(updates)

    # 寫回 Firebase
    write_json_to_firebase(str(log_path), log_data)
def update_memory_summary(cid, week, new_summary):          #Firebase Storage
    """
    合併寫入角色每週的記憶摘要（儲存在Firebase Storage）
    """
    path = get_memory_summary_path(cid, week)  # 回傳類似 logs/memory/cid/2025/W25.txt

    # 嘗試讀取舊的摘要內容
    try:
        old_summary = read_txt_from_firebase(path).strip()
    except FileNotFoundError:
        old_summary = ""

    # 合併新內容
    combined = f"{old_summary}\n\n=== Week {week} ===\n{new_summary}".strip()

    # 上傳更新後的內容
    write_txt_to_firebase(path, combined)
def append_txt_to_firebase(path: str, content: str):
    bucket = storage.bucket()
    blob = bucket.blob(path)
    # 先讀取現有內容（如果有）
    if blob.exists():
        existing = blob.download_as_text()
    else:
        existing = ""
    # 合併後寫回去
    updated = existing + content
    blob.upload_from_string(updated, content_type="text/plain")

# === 檔案與日誌工具 ===
def write_json_to_firebase(path: str, data: dict):
    bucket = get_bucket()
    blob = bucket.blob(path)  # ✅ 不再需要 Path() 處理

    # 將 dict 轉成 JSON 並編碼為 bytes
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    buffer = BytesIO(json_str.encode("utf-8"))

    blob.upload_from_file(buffer, content_type="application/json")
def read_json_from_firebase(path: str) -> dict:
    print(f"[DEBUG] 正在從 Firebase 讀取：{path}")
    bucket = get_bucket()
    blob = bucket.blob(str(path))
    if not blob.exists():
        return {}
    content = blob.download_as_text()
    return json.loads(content)
def write_image_info(path, content):
    """
    將圖片上傳資訊寫入指定 JSON 檔案（Firebase Storage）
    - path: 檔案路徑（logs/images/...）
    - content: 要寫入的資料（dict 格式）
    """
    write_json_to_firebase(path, content)

# === 雲端主題讀取 ===
def load_theme_file(path):                                   #Firebase Storage
    return read_json_from_firebase(path)
def get_today_theme(weekly_theme: dict, today: str) -> list:
    """根據日期取得今天主題清單"""
    if today not in weekly_theme:
        log_and_print(f"\n⚠️ 今日日期 {today} 在主題週中找不到對應項目\n", error_type="WARNING")
    return weekly_theme.get(today, [])
def get_today_characters(weekly_theme: dict, today: str) -> dict:
    """從主題中抓出 character_id 對應主題資料"""
    result = {}
    for item in weekly_theme.get(today, []):
        cid = item.get("character_id")
        theme = item.get("theme", {})
        if cid:
            result[cid] = theme
    return result

# === Firebase 路徑工具 ===
def get_today_paths_path(year_month: str, today: str) -> str:
    return f"logs/today_paths/{year_month}/{today}.json"
def get_today_paths():                                  #Firebase Storage
    path = f"logs/today_paths/{year_month}/{TODAY}.json"
    default_data = {}

    # 嘗試讀取 today_paths
    try:
        data = read_json_from_firebase(path)
        return data
    except json.JSONDecodeError as e:
        log_and_print(f"⚠️ 讀取 today_paths JSON 失敗，格式錯誤：{e}\n將以空資料覆蓋修正：\n{path}", error_type="error")
        write_json_to_firebase(path, default_data)
        return default_data
    except FileNotFoundError:
        log_and_print(f"⚠️ 找不到 today_paths JSON，將自動建立：{path}", error_type="WARNING")
        write_json_to_firebase(path, default_data)
        return default_data
def save_today_paths(today_paths: dict, year_month: str, today: str) -> str:
    path = f"logs/today_paths/{year_month}/{today}.json"
    write_json_to_firebase(path, sanitize_for_json(today_paths))
    return path

# === LLM與生成功能 ===
def build_prompt(character_name: str, theme_slug: str, memory_summary: str) -> str:
    user_prompt = (
        f"Today's character: {character_name}\n"
        f"Theme: {theme_slug}\n"
        f"Previous memory: {memory_summary}\n"
        f"Please write a new story and 10 visual prompts accordingly."
    )
    return user_prompt
def call_llm_for_story(character_card, theme_slug, memory_summary):
    """
    傳入角色卡資訊、主題 slug、記憶摘要，回傳 system + user prompt 組合。
    """
    character_name = character_card.get("name", "Unknown")
    system_prompt = (
        "You are a visual storytelling artist and illustrator who specializes in creating emotional, wordless picture books. "
        "Your job is to write a warm and moving story based on a given character and theme, and then break it down into a story summary, full narrative, and 10 image prompts.\n\n"
        "Please strictly reply using the following format:\n\n"
        "###STORY:\n(Full story in English)\n\n"
        "###SUMMARY:\n(1-2 sentence overview)\n\n"
        "###PROMPTS:\n- prompt_1\n- prompt_2\n...\n- prompt_10\n\n"
        "Do NOT include any other commentary, explanation, or text outside of this format.\n"
        "All prompts must be visual, concise, and suitable for use in image generation tools (no dialogue or captions)."
    )
    user_prompt = build_prompt(character_name, theme_slug, memory_summary)
    return system_prompt, user_prompt
# === call Deepseek stoy ===
def call_Deepseek_story(system_prompt: str, user_prompt: str, model="deepseek/deepseek-r1-0528:free") -> dict:
    api_key = os.getenv("OR_DEEPKEEP_R1_API")  # 環境變數中讀取 key
    if not api_key:
        log_and_print(f"\n❌ 環境變數 OR_DEEPKEEP_R1_API 未設置！\n", error_type="ERROR")
        raise SystemExit
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Title": "AI_Animal_Story_Generator" 
    }

    data = {
        "model": model,
        "messages": [
            {"role": "system","content": system_prompt},
            {"role": "user","content": user_prompt}],
        "temperature": 1.0,
        "max_tokens": 2048        
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    response.raise_for_status()
    return response.json()
def count_tokens(text: str) -> int:
    # 基本估算：用空白分隔詞彙數
    return len(text.split())
# 解析英文格式回傳（去除 LLM 加料的前言／後記)
def extract_response(text: str) -> dict:
    """
    從 LLM 的回應文字中萃取 story、summary 與 prompt_list。
    預期格式如下：
    ###STORY:
    ...
    ###SUMMARY:
    ...
    ###PROMPTS:
    - ...
    - ...
    """
    story_match = re.search(r"###STORY:\s*(.*?)\s*###SUMMARY:", text, re.DOTALL)
    summary_match = re.search(r"###SUMMARY:\s*(.*?)\s*###PROMPTS:", text, re.DOTALL)
    prompts_match = re.findall(r"-\s*(.+)", text.split("###PROMPTS:")[-1])

    if not story_match or not summary_match or not prompts_match:
        log_and_print("\n❌ extract_response 解析失敗，格式可能不符\n", "error")
        log_and_print(f"\n{text}\n")
        raise RuntimeError("解析失敗")

    return {
        "story": story_match.group(1).strip(),
        "summary": summary_match.group(1).strip(),
        "prompt_list": [p.strip() for p in prompts_match]
    }
def extract_response_parts(raw_response: dict) -> dict:
    content = raw_response["choices"][0]["message"]["content"]
    print(content)
    return {
        "story": extract_between(content, "###STORY:", "###SUMMARY:"),
        "summary": extract_between(content, "###SUMMARY:", "###PROMPTS:"),
        "prompt_list": extract_list_after(content, "###PROMPTS:"),
        "model": raw_response.get("model", ""),
        "duration": raw_response.get("duration", 0.0)
    }
def extract_between(text: str, start_marker: str, end_marker: str) -> str:
    """
    從指定起止標記之間擷取文字
    """
    try:
        return text.split(start_marker)[1].split(end_marker)[0].strip()
    except IndexError:
        return ""
def extract_list_after(text: str, marker: str) -> list:
    """
    從指定標記後提取 markdown 列表格式（- item）
    """
    try:
        section = text.split(marker)[1]
        return [line[1:].strip() for line in section.strip().split("\n") if line.startswith("-")]
    except IndexError:
        return []
# 圖片生成模擬（TODO: 換成實際生圖）
def generate_image_from_prompt(prompt):
    img = Image.new("RGB", (512, 512), color="white")
    return img
# 上傳圖片至 imgbb
def upload_to_imgbb(image, name):
    IMG_BB_API_KEY = os.getenv("IMG_BB_API_KEY")  # 環境變數中讀取 key
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    encoded_img = buffered.getvalue()

    response = requests.post(
        "https://api.imgbb.com/1/upload",   # ImgBB url
        params={"key": IMG_BB_API_KEY},
        files={"image": encoded_img},
        data={"name": name}
    )
    if response.status_code == 200:
        return response.json()["data"]["url"]
    else:
        log_and_print(f"❌ Upload failed:\n{response.text}\n", "error")
        return None
