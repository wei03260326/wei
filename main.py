from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import SQLModel, Session, create_engine, select
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.hash import bcrypt
from models import Todo, User

app = FastAPI()

# 資料庫位置（在本機產生 todos.db 檔案）
sqlite_file_name = "todos.db"
engine = create_engine(f"sqlite:///{sqlite_file_name}", echo=True)


# 建立資料表（啟動時自動執行）
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


# 建立一個取得資料庫 session 的方法
def get_session():
    with Session(engine) as session:
        yield session
SECRET_KEY = "your-secret-key"  # 實際部署時應改成更安全的金鑰
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="無效的 Token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 驗證失敗")

    user = session.exec(select(User).where(User.email == email)).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="找不到使用者")
    return user
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)



@app.post("/todos")
def create_todo(todo: Todo, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    db_todo = Todo(
        title=todo.title,
        owner_id=current_user.id  # 👈 把這筆待辦事項跟目前登入者綁定
    )
    session.add(db_todo)
    session.commit()
    session.refresh(db_todo)
    return db_todo


@app.get("/todos")
def read_todos(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    todos = session.exec(select(Todo).where(Todo.owner_id == current_user.id)).all()
    return todos

@app.get("/todos/{todo_id}")
def read_todo(todo_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    todo = session.get(Todo, todo_id)
    if not todo or todo.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="你沒有權限查看這筆資料")
    return todo

@app.put("/todos/{todo_id}")
def update_todo(todo_id: int, updated_todo: Todo, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    todo = session.get(Todo, todo_id)
    if not todo or todo.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="你沒有權限修改這筆資料")
    todo.title = updated_todo.title
    session.commit()
    session.refresh(todo)
    return {"message": "已更新", "todo": todo}


@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int, session: Session = Depends(get_session)):
    todo = session.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="找不到")
    session.delete(todo)
    session.commit()
    return {"message": "已刪除"}
from models import User  # 已有匯入 Todo，這裡要一併匯入 User
from passlib.hash import bcrypt

@app.post("/register")
def register(user: User, session: Session = Depends(get_session)):
    # 檢查 email 是否已存在
    existing_user = session.exec(select(User).where(User.email == user.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email 已被註冊")

    # 加密密碼後再存進資料庫
    user.hashed_password = bcrypt.hash(user.hashed_password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"message": "註冊成功", "user_id": user.id}
@app.post("/login")
def login(user: User, session: Session = Depends(get_session)):
    db_user = session.exec(select(User).where(User.email == user.email)).first()
    if not db_user or not db_user.verify_password(user.hashed_password):
        raise HTTPException(status_code=401, detail="帳號或密碼錯誤")

    # 成功的話產生 JWT token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
    




