import os
import json
import openai
import requests
from typing import List
from dotenv import load_dotenv

# 載入環境變數（請確認 .env 路徑與內容正確）
env_path = r'D:\CYCU\113_WebCrawler\CODE\.env'
load_dotenv(dotenv_path=env_path)
openai.api_key = os.getenv("OPENAI_API_KEY")

# 1. Vector Store 設定
VECTOR_STORE_URL = "https://api.openai.com/v1/vector-stores"
VECTOR_STORE_ID = "vs_67bd434482c881918365732b6c9ac474"  # 與需求一致
VECTOR_STORE_NAME = "MedicalEquipment_PDF"

# 2. ChatCompletion 相關設定 (assistant 與 Name)
ASSISTANT_MODEL_ID = "asst_nvA34D7Wmv2pq19Ewx3Kllvu"
ASSISTANT_NAME = "Medical Equiment_Filea Saerch"  # 參考需求
RESPONSE_FORMAT = "json_object"

def search_similar_keywords(keywords: List[str]) -> dict:
    """
    使用 OpenAI 向量庫搜尋與關鍵字（可為多組）相關或相似的名稱，
    並回傳指定格式的 JSON 物件:
    
    {
      "功能類別(5碼)": "...",
      "中文名稱": "...",
      "費用年": "..."
    }
    """
    # 將多個關鍵字合併成一個查詢字串
    combined_query = " ".join(keywords)

    # 3. 呼叫 OpenAI Vector Store 查詢
    # 將向量庫 ID 納入 URL，並使用冒號語法呼叫 query 功能
    vector_store_query_url = f"{VECTOR_STORE_URL}/{VECTOR_STORE_ID}"
    headers = {
        "Authorization": f"Bearer {openai.api_key}",
        "Content-Type": "application/json",
        "OpenAI-Beta": "assistants=v2"  # 符合 Assistants API 的要求
    }
    data = {
        "queries": [
            {
                "query": combined_query,
                "top_k": 5  # 可依需求調整
            }
        ]
    }

    response = requests.post(vector_store_query_url, headers=headers, json=data)
    if response.status_code != 200:
        raise Exception(f"Vector store query failed: {response.text}")
    
    results = response.json()

    # 4. 整理 Vector Store 回傳的資料作為上下文 (Context)
    top_contexts = []
    if "results" in results and results["results"]:
        matches = results["results"][0].get("matches", [])
        for idx, match_item in enumerate(matches):
            snippet = match_item.get("metadata", {}).get("text", "")
            top_contexts.append(f"<chunk {idx+1}> {snippet}")

    context_text = "\n".join(top_contexts) if top_contexts else "無相關資料"

    # 5. 呼叫 ChatCompletion，並以 JSON 格式回覆（只包含：功能類別(5碼)、中文名稱、費用年）
    system_message = (
        "You are a helpful assistant that answers questions based on the provided context. "
        "If the user asks about content not in context, say you are not sure. "
        "請依以下需求，僅以 JSON 格式作答（Response Format=json_object），並包含：\n"
        "功能類別(5碼)、中文名稱、費用年。\n"
        "範例：{\n"
        "  \"功能類別(5碼)\": \"xxxxx\",\n"
        "  \"中文名稱\": \"xxxxxx\",\n"
        "  \"費用年\": \"xxxx\"\n"
        "}"
    )

    user_message = (
        f"提供的關鍵字: {combined_query}\n\n"
        f"可用參考內容:\n{context_text}\n\n"
        "請回答對應的功能類別(5碼)、中文名稱、費用年。只以 JSON 回覆，不要多餘解釋。"
    )

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        temperature=0,
        user=ASSISTANT_MODEL_ID,  # 根據需求設定；目前用於識別最終使用者
    )

    answer_text = completion["choices"][0]["message"]["content"]

    # 6. 嘗試解析模型回傳的內容為 JSON
    try:
        answer_json = json.loads(answer_text)
    except Exception as e:
        raise ValueError("模型回傳內容無法解析成 JSON: \n" + answer_text) from e

    return answer_json

if __name__ == "__main__":
    # 測試使用範例：輸入關鍵字清單
    keywords = ["接頭", "人工覆蓋物", "支架"]
    result = search_similar_keywords(keywords)
    print("=== 最終 JSON 結果 ===")
    print(result)
