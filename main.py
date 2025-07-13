from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import SQLModel, Session, create_engine, select
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.hash import bcrypt
from models import User, UserCreate, Todo
from fastapi.security import OAuth2PasswordRequestForm

app = FastAPI()

# ===== 資料庫設定 =====
sqlite_file_name = "todos.db"
engine = create_engine(f"sqlite:///{sqlite_file_name}", echo=True)

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

# ===== JWT 設定 =====
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
security = HTTPBearer()

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="無效的 Token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token 驗證失敗")

    user = session.exec(select(User).where(User.email == email)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="找不到使用者")
    return user

# ===== 註冊與登入 =====
@app.post("/register")
def register(user: UserCreate, session: Session = Depends(get_session)):
    hashed_pw = bcrypt.hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_pw)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return {"msg": "註冊成功", "user": db_user.email}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    db_user = session.exec(select(User).where(User.email == form_data.username)).first()
    if not db_user or not db_user.verify_password(form_data.password):
        raise HTTPException(status_code=401, detail="帳號或密碼錯誤")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# ===== Todo CRUD =====
@app.post("/todos")
def create_todo(todo: Todo, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    db_todo = Todo(title=todo.title, owner_id=current_user.id)
    session.add(db_todo)
    session.commit()
    session.refresh(db_todo)
    return db_todo

@app.get("/todos")
def read_todos(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    return session.exec(select(Todo).where(Todo.owner_id == current_user.id)).all()

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
def delete_todo(todo_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    todo = session.get(Todo, todo_id)
    if not todo or todo.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="你沒有權限刪除")
    session.delete(todo)
    session.commit()
    return {"message": "已刪除"}