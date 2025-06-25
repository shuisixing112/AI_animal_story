# generate_image.py

import time
from config import TODAY, year_month, BASE_PATH, get_today_paths
from utils import (
    generate_image_from_prompt, upload_to_imgbb, write_json, 
    get_log_path, generate_imgbb_name, slugify, log_and_print
)
import json
from pathlib import Path

log_file_path = BASE_PATH/"logs"/year_month/f"{TODAY}_setup_log.txt"

# === 載入今日角色與主題資訊 ===
today_paths = get_today_paths()
today_themes = [
    {"character_id": cid, "theme": info["theme"]}
    for cid, info in today_paths.items()
    if "theme" in info
]

if not today_themes:
    log_and_print(f"\n❌ 今天 {TODAY} 沒有要處理的角色與主題\n", log_file_path)
    raise SystemExit
print("🟢 generate_image.py started1")
# === 開始逐一處理角色圖像 ===
for entry in today_themes:
    today_cid = entry["character_id"]
    theme_slug = entry["theme"]

    log_path = today_paths[today_cid]["log"]
    with open(log_path, "r", encoding="utf-8") as f:
        log_data = json.load(f)

    prompts = log_data.get("prompt_list", [])
    image_urls = []

    for idx, prompt in enumerate(prompts, 1):
        log_and_print(f"\n🎨 開始生成圖片 {idx}: {prompt}\n", log_file_path)
        img = generate_image_from_prompt(prompt)
        img_name = generate_imgbb_name(cid=today_cid, theme_slug=theme_slug, index=idx)
        print(f"DEBUG: 產生圖檔名稱：{img_name}")
        if img:
            url = upload_to_imgbb(img, img_name)
            if url:
                image_urls.append(url)
                log_and_print(f"✅ 上傳成功：\n{url}\n", log_file_path)
            else:
                log_and_print("⚠️ 上傳失敗\n", log_file_path)
        else:
            log_and_print("⚠️ 生成失敗\n", log_file_path)

        time.sleep(1.5)  # 為保險起見避免過快請求

    log_data["images"] = image_urls
    write_json(log_path, log_data)

    # === 同步更新角色 weekly txt ===
    txt_path = today_paths[today_cid]["txt"]
    with open(txt_path, "a", encoding="utf-8") as f:
        f.write(f"Image URLs ({TODAY}):\n")
        for url in image_urls:
            f.write(f"- {url}\n")
        f.write("\n------------------------------------------------------------\n")

    log_and_print(f"📦 圖片資訊已儲存至:\n {log_path}\n{txt_path}\n", log_file_path)

