

import time
from config import TODAY, year, year_month, week_num
import textwrap
from firebase_config import (
    initialize_firebase,
    get_story_txt_path,
    get_log_json_path,
    read_txt_from_firebase,
)
from utils import (
    call_Deepseek_story,
    extract_response,
    count_tokens,
    log_and_print,
    call_llm_for_story,
    append_txt_to_firebase,
    get_today_paths_path,
    read_json_from_firebase,
    write_json_to_firebase,
    extract_response_parts,
)

initialize_firebase()

log_file_path = f"logs/setup_log/{year_month}_{TODAY}_setup_log.txt"


# === 建立 prompt ===



# === 讀取 today_paths ===
today_paths = read_json_from_firebase(get_today_paths_path(year_month, TODAY))

# === 開始處理每位角色 ===
for cid, info in today_paths.items():
    theme_slug = info["theme"]
    log_path = info["log"]
    txt_path = info["txt"]

    # === 讀取角色卡 ===
    character_card = read_json_from_firebase(f"characters/data/{cid}.json")

    # === 讀取週記憶（可選） ===
    memory_path = f"memory/{cid}/memory_{year_month}.json"
    try:
        memory = read_txt_from_firebase(memory_path)
    except Exception:
        memory = ""

    # === 建立 Prompt ===
    system_prompt, user_prompt = call_llm_for_story(character_card, theme_slug, memory)
    log_and_print(f"\n🟡 Prompt 組合完成，開始生成...\n", error_type="OK")
    # === 呼叫 LLM 並解析 ===
    start_time = time.time()
    response_raw = call_Deepseek_story(system_prompt, user_prompt)
    full_response = extract_response_parts(response_raw)
    log_and_print(f"\n🟢 LLM 回應完成\n", error_type="OK")
    end_time = time.time()

    # === 記錄結果 ===
    story = full_response["story"]
    summary = full_response["summary"]
    prompts = full_response["prompt_list"]
    model = full_response["model"]
    tokens = count_tokens(system_prompt + user_prompt)
    duration = round(end_time - start_time, 2)

    # # # === Prompt 串接 LLM ===
    # start_time = time.time()
    # system_prompt, user_prompt = call_llm_for_story(character_card, theme_slug, memory)
    # # prompt = build_prompt(character, theme, recent_summary)
    # # log_and_print(f"\n🟡 Prompt 組合完成，開始生成...\n", log_file_path)

    # try:
    #     response_raw = call_Deepseek_story(system_prompt, user_prompt)
    #     text = response_raw["choices"][0]["message"]["content"]
    #     print(text)
    #     log_and_print(f"\n🟢 LLM 回應完成\n", log_file_path)

    #     response = extract_response(response_raw["choices"][0]["message"]["content"])
    #     end_time = time.time()
    #     story = response["story"]
    #     summary = response["summary"]
    #     prompts = response["prompt_list"]

    #     usage = response_raw.get("usage", {})
    #     tokens_input = count_tokens(system_prompt + user_prompt)
    #     tokens_output = usage.get("completion_tokens", 0)
    #     cost_usd = 0.0
    #     model = response_raw.get("model", "")
    #     duration = round(end_time - start_time, 2)

    # except Exception as e:
    #     log_and_print(f"❌ 回應解析失敗: {e}\n", log_file_path)
    #     raise

    # === 寫入 log.json ===
    log_data = read_json_from_firebase(log_path)
    log_data.update({
        "date": TODAY,
        "character": cid,
        "theme": theme_slug,
        "story": story,
        "summary": summary,
        "prompt_list": prompts,
        "model_story": model,
        "tokens_story": tokens,
        "duration": duration,
        "images": [],
    })
    write_json_to_firebase(log_path, log_data)

    # === 寫入 weekly 檔案 ===
    weekly_txt_path = get_story_txt_path(cid, year, week_num)
    # === 美化排版 ===
    image_urls = []
    wrapper = textwrap.TextWrapper(width=100, subsequent_indent="    ")
    story_formatted = wrapper.fill(story)
    summary_formatted = wrapper.fill(summary)
    max_index_len = len(str(len(prompts)))
    prompts_formatted = "\n".join([
        wrapper.fill(f"{str(i + 1).rjust(max_index_len)}. {p}")
        for i, p in enumerate(prompts)
    ])
    images_formatted = "\n".join(image_urls)

    daily_entry = f"""=== {TODAY}: {theme_slug} ===
    STORY:
    {story_formatted}

    SUMMARY:
    {summary_formatted}

    PROMPTS:
    {prompts_formatted}

    IMAGE URLs:
    {images_formatted}

    ------------------------------------------------------
    """
    append_txt_to_firebase(txt_path, daily_entry)

    # 寫入週檔案（append）
    append_txt_to_firebase(weekly_txt_path, daily_entry)
    log_and_print(f"✅ 故事生成並儲存完成！\n", error_type="OK")