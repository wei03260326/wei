# FastAPI Todo 專案

這是一個用 FastAPI 製作的待辦事項（Todo）API 專案，功能包含：
- 註冊 / 登入 / JWT 驗證
- 新增、查詢、修改、刪除 Todo
- 登入驗證後才能操作

## 執行方式

```bash
# 進入專案資料夾
cd todo_project

# 建立虛擬環境
python -m venv venv

# 啟動虛擬環境
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 安裝依賴套件
pip install -r requirements.txt

# 啟動伺服器
uvicorn main:app --reload

