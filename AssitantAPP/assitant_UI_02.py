import sys
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QComboBox, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QTextEdit,
)
from PyQt5.QtGui import QIcon
"""使用 價量調查品項111-112.csv和 價量調查品項108-110.csv"""
# 資料讀取和合併
# file_111_112 = "./CODE/data/價量調查品項111-112.csv"
# file_108_110 = "./CODE/data/價量調查品項108-110.csv"

# data_111_112 = pd.read_csv(file_111_112)
# data_108_110 = pd.read_csv(file_108_110)
# combined_data = pd.concat([data_111_112, data_108_110], ignore_index=True)
# # 將特材代碼前五碼轉換為字串
# combined_data["特材代碼前五碼"] = combined_data["特材代碼前五碼"].astype(str)

"""使用 價量調查品項108-112.csv"""
file_108_112 = "D:/CYCU/113_WebCrawler/CODE/data/價量調查品項111-112_FINAL.csv"

data_108_112 = pd.read_csv(file_108_112)
combined_data = data_108_112
combined_data["特材代碼前五碼"] = combined_data["特材代碼前五碼"].astype(str)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._filtered_data = None  # 儲存篩選後的資料
        self.setWindowTitle("AI議價工具 GUI")
        self.setGeometry(100, 100, 600, 500)
        self.init_ui()

    def init_ui(self):
        # 主佈局
        main_layout = QVBoxLayout()
        # Icon 部分
        self.setWindowIcon(QIcon("./data/AIBrain.png"))

        # 特材代碼前五碼選項
        code_label = QLabel("特材代碼前五碼")
        self.code_combo = QComboBox()
        self.code_combo.addItems(sorted(combined_data["特材代碼前五碼"].unique()))
        self.code_combo.currentTextChanged.connect(self.update_category_options)
        code_layout = QHBoxLayout()
        code_layout.addWidget(code_label)
        code_layout.addWidget(self.code_combo)
        main_layout.addLayout(code_layout)

        # 核價類別選項
        param_label = QLabel("核價類別")
        self.param_combo = QComboBox()
        param_layout = QHBoxLayout()
        param_layout.addWidget(param_label)
        param_layout.addWidget(self.param_combo)
        main_layout.addLayout(param_layout)

        # 啟動按鈕
        self.result_button = QPushButton("顯示結果")
        self.result_button.clicked.connect(self.show_results)
        main_layout.addWidget(self.result_button)

        # 結果顯示
        result_label = QLabel("結果：")
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        main_layout.addWidget(result_label)
        main_layout.addWidget(self.result_display)

        # 設置中央小部件
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def update_category_options(self, selected_code):
        """根據選擇的特材代碼更新核價類別選項"""
        filtered_data = combined_data[combined_data["特材代碼前五碼"] == selected_code]
        categories = sorted(filtered_data["核價類別名稱"].unique())
        self.param_combo.clear()
        self.param_combo.addItems(categories)

    def show_results(self):
        """顯示選定特材代碼和核價類別的相關數據"""
        selected_code = self.code_combo.currentText()
        selected_category = self.param_combo.currentText()

        self._filtered_data = combined_data[
            (combined_data["特材代碼前五碼"] == selected_code) &
            (combined_data["核價類別名稱"] == selected_category)
        ]

        if self._filtered_data.empty:
            self.result_display.setText("沒有找到相關數據")
        else:
            results = self._filtered_data[["年份", "支付點數", "申請者簡稱", "許可證字號"]]
            result_text = results.to_string(index=False, header=True)
            self.result_display.setText(result_text)
            print(f"filtered_data:\n type:{type(self._filtered_data)}\n {self._filtered_data}")
    
    def get_filtered_data(self):
        """提供外部存取 filtered_data 的方法"""
        return self._filtered_data


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
