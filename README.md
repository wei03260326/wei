## 執行方式

# 進入專案資料夾
cd wei

# 建立虛擬環境
python -m venv venv

# 啟動虛擬環境
# Windows (cmd):
venv\Scripts\activate
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS / Linux:
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt

# 啟動開發伺服器
uvicorn main:app --reload
