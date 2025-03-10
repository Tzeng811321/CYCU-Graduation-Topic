import pandas as pd
import requests
from dotenv import load_dotenv
import os
import json

env_path = r'D:\CYCU\113_WebCrawler\CODE\.env'
load_dotenv(dotenv_path=env_path)

def analyze_products(csv_file, api_key, keywords=None):
    """
    讀取產品 CSV 檔案，並呼叫 OpenAI API 取得多個關鍵字的回應，
    最終將所有關鍵字的回應都存入同一個 JSON 檔，並印出該檔案位置與回應摘要。
    """

    if keywords is None:
        input_keywords = input("請輸入關鍵字（以逗號分隔）：")
        keywords = [k.strip() for k in input_keywords.split(",") if k.strip()]

    API_URL = "https://api.openai.com/v1/chat/completions"
    df = pd.read_csv(csv_file)
    all_products = pd.Series(df.values.ravel()).dropna().unique()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # 系統提示 (system prompt)
    system_prompt = """
#### **功能**
- 分析產品名稱，找出與關鍵字相關或相似的名稱（不包含關鍵字本身）。
- 使用 OpenAI API 進行語意比對，篩選類似產品。
- **確保返回的 JSON 格式與系統要求相符**。

#### **輸入格式**
關鍵字: {keyword}
[產品清單]:
"107年","自動血管夾AUTOMATIC CLIP(TITANIUM),M SIZE,槍帶夾"
"108年","PTCA BALLOON CATHETER(Over-the-wire)"
"108年","真空傷口引流套(矽質)/套組(矽質引流管+矽質吸引球)"
"109年","雙極式或全人工髖關節髖臼杯+內襯(HIP CUP+INSERT)"
"109年","人工關節置換系統/膝關節(股骨、脛骨、髕骨)"
"110年","脊椎內固定系統/脊椎椎弓根螺釘"

#### **輸出格式**
    {"關鍵字": "骨水泥", "出現年度": [107, 109], "相關產品": ["產品X", "產品Y"]},
    {"關鍵字": "人工關節", "出現年度": [109, 110], "相關產品": ["產品A", "產品B"]}
""".strip()

    # 用於儲存所有關鍵字的完整 API 回傳
    all_results = {}

    for keyword in keywords:
        # ※ 若不再需要 occurrence_years、相關產品等，可視需求刪除下列程式
        occurrence_years = df.columns[
            df.apply(lambda col: col.astype(str).str.contains(keyword, na=False)).any()
        ].tolist()

        product_list_str = "\n".join(all_products)
        user_message = (
            f"請根據以下產品清單，找出與關鍵字「{keyword}」相關或相似的產品名稱（不包含關鍵字本身），"
            "並確保輸出格式符合系統指定的 JSON 格式。\n"
            f"以下為產品清單：\n{product_list_str}"
        )

        data = {
            "model": "gpt-4o",  # 請確認您有權限使用此模型名稱
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.2
        }

        try:
            response = requests.post(API_URL, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()

            # 將整個回傳存到 all_results
            all_results[keyword] = result

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred for keyword {keyword}: {http_err}")
            # 失敗的關鍵字也可在 all_results 中標示錯誤訊息
            all_results[keyword] = {"error": str(http_err)}
        except Exception as err:
            print(f"An error occurred for keyword {keyword}: {err}")
            all_results[keyword] = {"error": str(err)}

    # === 1) 將 all_results 寫到單一 JSON 檔 ===
    output_dir = os.path.dirname(csv_file)
    single_json_path = os.path.join(output_dir, "SimilarProduct_Output.json")
    with open(single_json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    # (1) print All_Responses.json存儲位置
    print(f"\n所有關鍵字的回應已寫入： {single_json_path}")

    # === 2) 取代原先 # === 3. 顯示結果 ===，改為顯示 All_Responses.json 的資訊 ===
    print("\n=== 顯示 SimilarProduct_Output.json 之資訊 ===")
    # 我們可直接使用 all_results (字典) 來印出指定欄位
    for keyword, res_dict in all_results.items():
        print(f"\n關鍵字: {keyword}")
        if "error" in res_dict:
            # 若該關鍵字呼叫失敗
            print(f"  - 發生錯誤: {res_dict['error']}")
            continue

        # 否則，成功呼叫到 API，res_dict 是整個 ChatCompletions 的回應
        _id = res_dict.get("id", "")
        _object = res_dict.get("object", "")
        _model = res_dict.get("model", "")
        _usage = res_dict.get("usage", {})
        _choices = res_dict.get("choices", [])

        # 預設值
        finish_reason = ""
        message_content = ""

        if _choices and isinstance(_choices, list):
            # 取第一個 choice
            choice_0 = _choices[0]
            finish_reason = choice_0.get("finish_reason", "")
            if "message" in choice_0 and isinstance(choice_0["message"], dict):
                message_content = choice_0["message"].get("content", "")

        # DEBUG用   顯示指定的 6 個欄位
        print(f"id: {_id}\n")
        print(f"object: {_object}\n")
        print(f"model: {_model}\n")
        print(f"message: {message_content}\n")
        print(f"finish_reason: {finish_reason}\n")
        print(f"usage: {_usage}\n")


if __name__ == "__main__":
    csv_file_path = r"D:\CYCU\113_WebCrawler\CODE\data\format_clean.csv"
    api_key_input = os.getenv("OPENAI_API_KEY")
    analyze_products(csv_file_path, api_key_input)
