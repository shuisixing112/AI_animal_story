# 每日資料建立（文件建立，預建立）
# logs/每日/日期_角色_主題slug.generation_log.json
# config.py需告知scripts/位置
# theme 檔名稱 ex:W25_theme.json

import os
from config import TODAY, year, year_month, week_num
from utils import (
    get_theme_path,
    load_theme_file,
    get_today_theme,
    get_today_characters,
    slugify,
    get_log_json_path,
    save_today_paths,
    log_and_print,
    write_json_to_firebase,
    write_txt_to_firebase,
    get_story_txt_path,
)

# === 主題檔案路徑與載入 ===
THEME_PATH = get_theme_path(year, week_num)

weekly_theme = load_theme_file(THEME_PATH)

# === 抓出今天的角色與主題 ===
character_themes = get_today_characters(weekly_theme, TODAY)

if not character_themes:
    log_and_print(f"✅ 今天 {TODAY} 沒有要生成內容的角色，結束執行。\n", error_type="WARNING")
    exit()

log_and_print(f"🧩 今天 {TODAY} 角色：{', '.join(character_themes.keys())}\n", error_type="OK")

# === 初始化 today_paths 結構 ===
today_paths = {}

for cid, theme in character_themes.items():
    theme_slug = slugify(theme.get("title", "unknown"))
    story_path = get_story_txt_path(cid, year, week_num)
    log_path = get_log_json_path(cid, TODAY, theme_slug)

    today_paths[cid] = {
        "theme": theme_slug,
        "log": log_path,
        "txt": story_path,
    }

    # 初始化 story 檔（如果不存在）
    write_txt_to_firebase(story_path, "# Weekly log file initialized\n")

    # 初始化 log.json
    if not os.path.exists(log_path) or os.path.getsize(log_path) == 0:
        log_data = {
            "date": TODAY,
            "character": cid,
            "theme": theme_slug,
            "story": "",
            "summary": "",
            "prompt_list":[],
            "model_story": "",
            "duration": 0.0
        }
        write_json_to_firebase(log_path, log_data)

# === 儲存 today_paths 為 JSON ===
today_paths_path = save_today_paths(today_paths, year_month, TODAY)
log_and_print(f"✅ 已儲存 today_paths 至：{today_paths_path}\n", error_type="OK")