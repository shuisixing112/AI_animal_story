# generate_image.py

import time
import json
from config import TODAY, year_month, get_today_paths
from utils import (
    generate_image_from_prompt, upload_to_imgbb, 
    read_json_from_firebase, write_json_to_firebase, 
    append_txt_to_firebase, generate_imgbb_name, 
    slugify, log_and_print
)


# === 載入今日角色與主題資訊 ===
today_paths = get_today_paths()
today_themes = [
    {"character_id": cid, "theme": info["theme"]}
    for cid, info in today_paths.items()
    if "theme" in info
]

if not today_themes:
    log_and_print(f"\n❌ 今天 {TODAY} 沒有要處理的角色與主題\n", "error")
    raise SystemExit

# === 開始逐一處理角色圖像 ===
for entry in today_themes:
    today_cid = entry["character_id"]
    theme_slug = entry["theme"]

    log_path = today_paths[today_cid]["log"]
    txt_path = today_paths[today_cid]["txt"]

    log_data = read_json_from_firebase(log_path)
    prompts = log_data.get("prompt_list", [])
    image_urls = []

    for idx, prompt in enumerate(prompts, 1):
        log_and_print(f"\n🎨 開始生成圖片 {idx}: {prompt}\n", "OK")

        img = generate_image_from_prompt(prompt)
        img_name = generate_imgbb_name(cid=today_cid, theme_slug=theme_slug, index=idx)
        print(f"DEBUG: 產生圖檔名稱：{img_name}")

        if img:
            url = upload_to_imgbb(img, img_name)
            if url:
                image_urls.append(url)
                log_and_print(f"✅ 上傳成功：\n{url}\n", "OK")
            else:
                log_and_print("⚠️ 上傳失敗\n", "warning")
        else:
            log_and_print("⚠️ 生成失敗\n", "error")

        time.sleep(1.5)  # 為保險起見避免過快請求

    log_data["images"] = image_urls
    write_json_to_firebase(log_path, log_data)

    # === 附加圖片網址至 weekly story txt ===
    txt_block = f"Image_URLs ({TODAY}):\n"
    txt_block += "\n".join(f"- {url}" for url in image_urls)
    txt_block += "\n------------------------------------------------------------\n"
    append_txt_to_firebase(txt_path, txt_block)

    log_and_print(f"📦 圖片資訊已儲存至:\n{log_path}\n{txt_path}\n")

