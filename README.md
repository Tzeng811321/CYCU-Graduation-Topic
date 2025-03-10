# CYCU-Graduation-Topic
Use openAI api to find similar Medical Equipment

#========HOW TO USE===============

假設你已經安裝好 Conda（或 Anaconda/Miniconda）。
如果你還沒有安裝 Conda，請先[安裝 Miniconda 或 Anaconda](https://docs.conda.io/en/latest/miniconda.html)
再進行以下步驟。
---

## 1. 確認 Conda 是否可以使用
打開終端機（Terminal）或 CMD（Windows），輸入：

conda --version

若可以顯示 conda 的版本號表示安裝完成；若指令找不到，可能需要確認「Conda 的安裝路徑」是否已加入系統環境變數。
---

## 2. 創建新的 Conda 環境

conda create -n myenv python=3.13


Conda 會列出要安裝的套件清單並詢問是否繼續，輸入 `y` 或 `yes`。
---

## 3. 啟動（Activate）新的環境
當 Conda 成功建立完環境後，輸入：

conda activate myenv

---

## 4. 安裝需要的套件

conda install requirements.txt -r

Conda 會自動檢查並安裝相依套件，並詢問是否繼續，請輸入 `y` 或 `yes` 確認。


## 5. 查看已安裝的套件
在已啟動的 `myenv` 環境中，可以透過以下指令查看已安裝的所有套件與版本：

conda list或pip list

---

## 6. 離開（Deactivate）環境
使用完成後，你可以輸入以下指令返回系統的預設 Python 環境：

conda deactivate

如果成功，終端機或 CMD 提示列前的 `(myenv)` 會消失。

---

## 7. （可選）刪除不再需要的環境
如果未來不再需要此環境，可在**沒有**啟動該環境（已經 `conda deactivate` 後）執行：

conda remove -n myenv --all

---

## 總結
1. **安裝 Conda**（若尚未安裝）。
2. **確認 Conda** 可用：`conda --version`
3. **建立環境**（例如 `conda create -n myenv python=3.13`）
4. **啟動環境**：`conda activate py13env`
5. **安裝所需套件**：`conda install requirements.txt -r ` 或 `pip install requirements.txt-r`
6. **使用完後關閉環境**：`conda deactivate`
7. **刪除環境（可選）**：`conda remove -n myenv --all`

Wrote By Tseng Chia Tsai

#=================================
