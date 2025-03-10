import pandas as pd
import csv
# 讀取 CSV 檔案
input_file = 'D:/CYCU/113_WebCrawler/CODE/data/價量調查品項108-112.csv'  # 輸入檔案名稱
output_file = 'D:/CYCU/113_WebCrawler/CODE/data/AfterModify.csv'  # 輸出檔案名稱

# 讀取 CSV，假設檔案使用 UTF-8 編碼
df = pd.read_csv(input_file, encoding='utf-8')

# 去除「核價類別名稱」欄位前方的空白字元
if '核價類別名稱' in df.columns:
    df['核價類別名稱'] = df['核價類別名稱'].astype(str).str.lstrip()
else:
    print("找不到 '核價類別名稱' 欄位")

# 儲存修改後的 CSV 檔案
df.to_csv(output_file, index=False, encoding='utf-8')

print(f"已移除前置空白，並儲存至 {output_file}")