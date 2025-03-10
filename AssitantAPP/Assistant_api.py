import os
import sys
import json
from dotenv import load_dotenv
from SimilarProduct import analyze_products 
import FileSearch as fs

# ====== 載入 .env 設定 ======
env_path = r'D:\CYCU\113_WebCrawler\CODE\.env'
if not os.path.exists(env_path):
    sys.exit(f"找不到環境變數檔案：{env_path}")
load_dotenv(dotenv_path=env_path)

def main():
    # ---------------------------
    # 1. 呼叫 SimilarProduct 模組處理產品分析
    # ---------------------------
    csv_file_path = r"D:\CYCU\113_WebCrawler\CODE\data\format_clean.csv"
    api_key_input = os.getenv("OPENAI_API_KEY")
    if not api_key_input:
        print("環境變數中找不到 OPENAI_API_KEY")
        return

    print("開始使用 SimilarProduct 進行產品分析...")
    analyze_products(csv_file_path, api_key_input)

    # ---------------------------
    # 2. 讀取 SimilarProduct 模組產生的 JSON 結果
    # ---------------------------
    similar_product_json_path = os.getenv("SimilarProduct_JSON_PATH")
    if not os.path.exists(similar_product_json_path):
        print(f"找不到 SimilarProduct JSON 檔案：{similar_product_json_path}")
        return

    with open(similar_product_json_path, "r", encoding="utf-8") as f:
        product_data = json.load(f)

    # 解析並整合所有關鍵字下的「相關產品」
    all_products = []
    for keyword, content in product_data.items():
        if "choices" in content and len(content["choices"]) > 0:
            content_str = content["choices"][0]["message"]["content"]
            content_str_clean = content_str.strip("```json").strip("```").strip()
            try:
                prod_dict = json.loads(content_str_clean)
                prods = prod_dict.get("相關產品", [])
                all_products.extend(prods)
            except json.JSONDecodeError:
                all_products.append(content_str_clean)

    if not all_products:
        print("未能從 SimilarProduct 結果中取得任何產品資訊。")
        return

    # 將產品列表合併成一個字串，並形成使用者問題
    product_list_str = "\n".join(all_products)
    user_question = (
        f"以下是多個產品列表(依關鍵字分類後再合併):\n{product_list_str}\n"
        "請問在現有的資料庫中相關或相似的功能類別(5碼)中文名稱有哪些？"
    )
    print("使用者問題:\n", user_question)

    # ---------------------------
    # 3. 呼叫 FileSearch 模組進行 PDF 內容查找
    # ---------------------------
    pdf_folder = os.getenv("PDFfloder_PATH")
    if not os.path.isdir(pdf_folder):
        print(f"找不到 PDF 資料夾：{pdf_folder}")
        return

    pdf_files = [
        os.path.join(pdf_folder, f)
        for f in os.listdir(pdf_folder)
        if f.lower().endswith(".pdf")
    ]
    if not pdf_files:
        print(f"在資料夾中找不到 PDF 檔案：{pdf_folder}")
        return

    all_chunks = []
    for pdf_file in pdf_files:
        print(f"正在讀取與切分 PDF：{pdf_file}")
        chunks = fs.pdf_to_chunks(pdf_file)
        all_chunks.extend(chunks)

    if not all_chunks:
        print("未能從 PDF 中擷取任何文字區塊。")
        return

    print("對所有 chunk 進行 Embedding ...")
    embedded_chunks = fs.get_embeddings_for_chunks(all_chunks, model="text-embedding-ada-002")

    print("根據使用者問題搜尋最相似的 chunk (top_k=20) ...")
    top_chunks = fs.search_relevant_chunks(user_question, embedded_chunks, top_k=20)

    print("使用 ChatCompletion 模組回應，整合相似 chunk 作為上下文提示 ...")
    answer = fs.answer_with_context(user_question, top_chunks, model="gpt-4o")

    # ---------------------------
    # 4. 將最終答案寫入指定的文字檔中
    # ---------------------------
    output_txt = "D:\\CYCU\\113_WebCrawler\\CODE\\data\\final_answer.txt"
    try:
        with open(output_txt, "w", encoding="utf-8") as f:
            f.write(answer)
        print("\n===== 最終答案 =====")
        print(answer)
        print(f"\n===== 答案已存入 {output_txt} =====")
    except Exception as e:
        print(f"寫入最終答案時發生錯誤：{e}")

if __name__ == "__main__":
    main()
