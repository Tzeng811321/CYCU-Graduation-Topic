import os
import json
import openai
import PyPDF2
import numpy as np
from typing import List, Tuple
from dotenv import load_dotenv

##############################################################################
# 1. 載入環境變數 & 初始化
##############################################################################
env_path = r'D:\CYCU\113_WebCrawler\CODE\.env'
load_dotenv(dotenv_path=env_path)
openai.api_key = os.getenv("OPENAI_API_KEY")  # 或直接設定 openai.api_key = "sk-xxxxx"

##############################################################################
# 2. 工具函式：讀取並切分 PDF
##############################################################################
def pdf_to_chunks(pdf_path: str, chunk_size: int = 800, chunk_overlap: int = 100) -> List[str]:
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text.strip() + "\n"

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - chunk_overlap if (end - chunk_overlap) > 0 else end
    return chunks

##############################################################################
# 3. 工具函式：使用 OpenAI Embeddings 將 chunk 向量化
##############################################################################
def get_embeddings_for_chunks(chunks: List[str], model="text-embedding-ada-002") -> List[Tuple[str, np.ndarray]]:
    embedded_chunks = []
    for chunk in chunks:
        resp = openai.Embedding.create(model=model, input=chunk)
        vector = np.array(resp["data"][0]["embedding"])
        embedded_chunks.append((chunk, vector))
    return embedded_chunks

##############################################################################
# 4. 工具函式：根據使用者 query，搜尋最相似的 chunk
##############################################################################
def search_relevant_chunks(
    query: str,
    embedded_chunks: List[Tuple[str, np.ndarray]],
    top_k: int = 3,
    embed_model="text-embedding-ada-002",
) -> List[str]:
    query_resp = openai.Embedding.create(model=embed_model, input=query)
    query_vec = np.array(query_resp["data"][0]["embedding"])

    scores = []
    for chunk_text, chunk_vec in embedded_chunks:
        score = cosine_similarity(query_vec, chunk_vec)
        scores.append((chunk_text, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    top_chunks = [item[0] for item in scores[:top_k]]
    return top_chunks

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

##############################################################################
# 5. 用 ChatCompletion 回答，將相似 chunks 當作「context」提示
##############################################################################
def answer_with_context(query: str, top_chunks: List[str], model="gpt-3.5-turbo") -> str:
    context_text = "\n---\n".join(
        [f"<chunk> {i+1}\n{ch}" for i, ch in enumerate(top_chunks)]
    )

    system_msg = (
        "You are a helpful assistant that answers questions based on the provided context. "
        "Use the context to answer the user's question. "
        "If the user asks about content not in context, say you are not sure. "
        "When you cite content, reference the <chunk> number."
    )
    user_content = f"Context:\n{context_text}\n\nQuestion: {query}"
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_content},
    ]

    resp = openai.ChatCompletion.create(model=model, messages=messages, temperature=0.2)
    return resp["choices"][0]["message"]["content"]

##############################################################################
# 6. 主程式：自動抓取指定資料夾內所有 PDF，並使用 JSON 檔的產品列表
##############################################################################
if __name__ == "__main__":

    # 6.1 讀取 JSON 檔，將「產品列表」依「關鍵字」分類
    json_file = os.getenv("SimilarProduct_JSON_PATH")  # 你上傳的 JSON 檔名稱
    products_by_keyword = {}  # { 關鍵字: [相關產品1, 相關產品2, ...], ... }

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for top_key, content_dict in data.items():
        # content_dict["choices"][0]["message"]["content"] 是一段 JSON 字串
        content_str = content_dict["choices"][0]["message"]["content"]

        # 去掉外層的 ```json ... ```，再用 json.loads 解析
        content_str_clean = content_str.strip("```json").strip("```").strip()
        embedded = json.loads(content_str_clean)  # embedded 解析後的 dict

        # 增加一行撈取 "關鍵字"
        real_keyword = embedded.get("關鍵字", "")
        product_list = embedded.get("相關產品", [])

        # 依「關鍵字」將產品列表歸類
        # 註：若您想用 top_key 當索引，則改回 top_key 也可以
        #     或是將兩者做比較看是否一致
        products_by_keyword[real_keyword] = product_list

    # 這邊可自行合併所有產品或直接保留分群的資料結構
    # 以下示範依關鍵字分群後，串成一個完整字串
    grouped_str_list = []
    for kw, plist in products_by_keyword.items():
        # 先把「關鍵字」寫上去，再逐筆列出該關鍵字下的產品
        section_lines = [f"【關鍵字】{kw}"]  # 可以用其他格式
        section_lines.extend(plist)
        # grouped_str_list.append("\n".join(section_lines))
        grouped_str_list.append("".join(section_lines))

    # 把各個關鍵字分段合併
    final_merged_str = "\n\n".join(grouped_str_list)
    
    # 6.2 使用者可自訂問題，示範將「關鍵字」與「產品列表」合併拼成一個字串
    user_question = (
        f"以下是多個產品列表:\n{final_merged_str}\n\n"
        "請協助我搜尋PDF (以及現有資料庫)中，"
        "所有與上方產品列表內容相關或相似的醫材／產品，"
        "並列出更多與其功能類別相關或相似的(5碼)中文名稱或其他可參考的資訊。"
    )
    print("user_question:\n", user_question)  # DEBUG 用

    # 6.3 指定 PDF 資料夾 (自動讀取所有 PDF)
    pdf_folder = os.getenv("PDFfloder_PATH")
    pdf_files = [
        os.path.join(pdf_folder, f)
        for f in os.listdir(pdf_folder)
        if f.lower().endswith(".pdf")
    ]

    # 6.4 讀取與切分 PDF
    all_chunks = []
    for pdf_file in pdf_files:
        print(f"Reading and splitting PDF: {pdf_file}")
        chunks = pdf_to_chunks(pdf_file)
        all_chunks.extend(chunks)

    # 6.5 對所有 chunks 做 Embedding
    print("Embedding all chunks ...")
    embedded_chunks = get_embeddings_for_chunks(all_chunks, model="text-embedding-ada-002")

    # 6.6 搜尋與問題最相似的前 20 個 chunks
    top_chunks = search_relevant_chunks(user_question, embedded_chunks, top_k=20)

    # 6.7 呼叫 ChatCompletion 結合最相似 chunks (可換成 gpt-4o 或其他模型)
    answer = answer_with_context(user_question, top_chunks, model="gpt-4o")

    # 6.8 將最終回答寫入文字檔
    output_txt = "D:\\CYCU\\113_WebCrawler\\CODE\\data\\final_answer.txt"
    with open(output_txt, "w", encoding="utf-8") as f:
        f.write(answer)

    print("\n===== ANSWER =====")
    print(answer)
    print(f"===== The answer is also saved to {output_txt} =====")
