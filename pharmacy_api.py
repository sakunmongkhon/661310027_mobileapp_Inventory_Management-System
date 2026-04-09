
# ==================== DELETE ALL NOTIFICATIONS ====================
# (Moved to after all Notification endpoints for correct order)

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, Text, Date, DateTime, Boolean, Enum, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker, relationship
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, date, timedelta
from typing import Optional, List
from pydantic import BaseModel, Field
from apscheduler.schedulers.background import BackgroundScheduler
import os, shutil, uuid

# ==================== CONFIG ====================
DB_HOST = "192.168.0.105"
DB_PORT = 3306
DB_USER = "root"
DB_PASS = ""  # << เปลี่ยนตรงนี้
DB_NAME = "pharmacy_db"

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
SECRET_KEY = "pharmacy-secret-key-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ==================== DB SETUP ====================
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True)
    password_hash = Column(String(255))
    role = Column(Enum("admin", "staff"), default="staff")
    full_name = Column(String(200))
    created_at = Column(DateTime, default=datetime.now)

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)

class Medicine(Base):
    __tablename__ = "medicines"
    id = Column(Integer, primary_key=True)
    name = Column(String(300), nullable=False)
    generic_name = Column(String(300))
    category_id = Column(Integer)
    unit = Column(String(50), default="เม็ด")
    description = Column(Text)
    image_path = Column(String(500))
    min_stock = Column(Integer, default=10)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    batches = relationship(
        "Batch",
        back_populates="medicine",
        cascade="all, delete",
        primaryjoin="Medicine.id == Batch.medicine_id"
    )

class Batch(Base):
    __tablename__ = "batches"
    id = Column(Integer, primary_key=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id", ondelete="CASCADE", name="1"), nullable=False)
    batch_number = Column(String(100), nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    expire_date = Column(Date, nullable=False)
    received_date = Column(Date, default=date.today)
    note = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    medicine = relationship("Medicine", back_populates="batches")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    type = Column(Enum("expiry", "expired", "low_stock"))
    medicine_id = Column(Integer)
    batch_id = Column(Integer)
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)  # เพิ่มสถานะการแก้ไข
    created_at = Column(DateTime, default=datetime.now)

# ==================== AUTH ====================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

def verify_password(plain, hashed): return pwd_context.verify(plain, hashed)
def get_password_hash(password): return pwd_context.hash(password)

def create_token(data: dict):
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=401, detail="ไม่ได้เข้าสู่ระบบ")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=401, detail="ไม่พบผู้ใช้งาน")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Token ไม่ถูกต้อง")

# ==================== PYDANTIC ====================
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    full_name: str

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=3, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=200)

    @classmethod
    def __get_validators__(cls):
        yield from super().__get_validators__()
        yield cls.validate_password_length

    @classmethod
    def validate_password_length(cls, values):
        pw = values.get('password')
        if pw and len(pw.encode('utf-8')) > 72:
            raise ValueError('รหัสผ่านต้องไม่เกิน 72 bytes (ภาษาอังกฤษ/ตัวเลขไม่เกิน 72 ตัว, ภาษาไทยหรืออักขระพิเศษอาจน้อยกว่า)')
        return values

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    class Config: from_attributes = True

class BatchCreate(BaseModel):
    batch_number: str
    quantity: int
    expire_date: date
    received_date: Optional[date] = None
    note: Optional[str] = None

class BatchUpdate(BaseModel):
    batch_number: Optional[str] = None
    quantity: Optional[int] = None
    expire_date: Optional[date] = None
    note: Optional[str] = None

class BatchResponse(BaseModel):
    id: int
    batch_number: str
    quantity: int
    expire_date: date
    received_date: Optional[date] = None
    note: Optional[str] = None
    days_until_expire: Optional[int] = None
    class Config: from_attributes = True

class MedicineCreate(BaseModel):
    name: str
    generic_name: Optional[str] = None
    category_id: Optional[int] = None
    unit: Optional[str] = "เม็ด"
    description: Optional[str] = None
    min_stock: Optional[int] = 10

class MedicineUpdate(BaseModel):
    name: Optional[str] = None
    generic_name: Optional[str] = None
    category_id: Optional[int] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    min_stock: Optional[int] = None

class MedicineResponse(BaseModel):
    id: int
    name: str
    generic_name: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    unit: str
    description: Optional[str] = None
    image_path: Optional[str] = None
    min_stock: int
    total_stock: int = 0
    batches: List[BatchResponse] = []
    class Config: from_attributes = True

class NotificationResponse(BaseModel):
    id: int
    type: str
    medicine_id: Optional[int] = None
    batch_id: Optional[int] = None
    message: str
    is_read: bool
    is_resolved: bool
    created_at: datetime
    class Config: from_attributes = True

# ==================== HELPERS ====================
def medicine_to_response(m: Medicine, db: Session) -> dict:
    today = date.today()
    total = sum(b.quantity for b in m.batches if b.expire_date >= today)
    batches_resp = []
    for b in sorted(m.batches, key=lambda x: x.expire_date):
        days = (b.expire_date - today).days
        batches_resp.append({
            "id": b.id,
            "batch_number": b.batch_number,
            "quantity": b.quantity,
            "expire_date": b.expire_date,
            "received_date": b.received_date,
            "note": b.note,
            "days_until_expire": days
        })
    # query หมวดหมู่แยก เพราะ DB ไม่มี FK constraint ระหว่าง medicines -> categories
    category_name = None
    if m.category_id:
        cat = db.query(Category).filter(Category.id == m.category_id).first()
        category_name = cat.name if cat else None
    return {
        "id": m.id,
        "name": m.name,
        "generic_name": m.generic_name,
        "category_id": m.category_id,
        "category_name": category_name,
        "unit": m.unit,
        "description": m.description,
        "image_path": m.image_path,
        "min_stock": m.min_stock,
        "total_stock": total,
        "batches": batches_resp
    }

# ==================== SCHEDULER ====================
def check_expiry_and_stock():
    db = SessionLocal()
    try:
        today = date.today()
        warn_date = today + timedelta(days=30)
        # 1. ใกล้หมดอายุ (<=30 วัน)
        batches = db.query(Batch).filter(
            Batch.expire_date <= warn_date,
            Batch.expire_date >= today,
            Batch.quantity > 0
        ).all()
        for b in batches:
            days_left = (b.expire_date - today).days
            med = db.query(Medicine).filter(Medicine.id == b.medicine_id).first()
            if not med:
                continue
            exists = db.query(Notification).filter(
                Notification.batch_id == b.id,
                Notification.type == "expiry",
                Notification.is_resolved == False
            ).first()
            if not exists:
                db.add(Notification(
                    type="expiry",
                    medicine_id=b.medicine_id,
                    batch_id=b.id,
                    message=f"ยา {med.name} Batch {b.batch_number} จะหมดอายุในอีก {days_left} วัน ({b.expire_date})"
                ))

        # 2. หมดอายุแล้ว
        expired_batches = db.query(Batch).filter(
            Batch.expire_date < today,
            Batch.quantity > 0
        ).all()
        for b in expired_batches:
            med = db.query(Medicine).filter(Medicine.id == b.medicine_id).first()
            if not med:
                continue
            exists = db.query(Notification).filter(
                Notification.batch_id == b.id,
                Notification.type == "expired",
                Notification.is_resolved == False
            ).first()
            if not exists:
                db.add(Notification(
                    type="expired",
                    medicine_id=b.medicine_id,
                    batch_id=b.id,
                    message=f"ยา {med.name} Batch {b.batch_number} หมดอายุแล้ว ({b.expire_date})"
                ))

        # 3. สต็อกต่ำกว่า 5
        medicines = db.query(Medicine).all()
        for m in medicines:
            total = sum(b.quantity for b in m.batches if b.expire_date >= today)
            if total < 5:
                exists = db.query(Notification).filter(
                    Notification.medicine_id == m.id,
                    Notification.type == "low_stock",
                    Notification.is_resolved == False
                ).first()
                if not exists:
                    db.add(Notification(
                        type="low_stock",
                        medicine_id=m.id,
                        message=f"ยา {m.name} สต็อกต่ำกว่า 5 (คงเหลือ {total} {m.unit})"
                    ))
        db.commit()
    finally:
        db.close()

# ==================== APP (สร้างครั้งเดียว) ====================
app = FastAPI(title="Pharmacy Inventory API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/image", StaticFiles(directory="image"), name="image")

scheduler = BackgroundScheduler()
scheduler.add_job(check_expiry_and_stock, "interval", hours=6)
scheduler.start()

# ==================== AUTH ENDPOINTS ====================
@app.post("/auth/register", status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    try:
        if db.query(User).filter(User.username == data.username).first():
            raise HTTPException(status_code=400, detail="Username นี้ถูกใช้แล้ว")
        # bcrypt รับ password ได้สูงสุด 72 bytes (passlib จะตัดอัตโนมัติถ้าใช้ .encode("utf-8") ก่อนตัด)
        pw_bytes = data.password.encode("utf-8")
        print(f"[DEBUG REGISTER] password={data.password!r} bytes={pw_bytes} len={len(pw_bytes)}")
        if len(pw_bytes) > 72:
            cut = 72
            while cut > 0 and (pw_bytes[cut] & 0b11000000) == 0b10000000:
                cut -= 1
            pw_bytes = pw_bytes[:cut]
        safe_password = pw_bytes.decode("utf-8", errors="ignore")
        print(f"[DEBUG REGISTER] safe_password={safe_password!r} safe_len={len(safe_password.encode('utf-8'))}")
        print(f"[DEBUG HASH INPUT] safe_password={safe_password!r} safe_len={len(safe_password.encode('utf-8'))}")
        try:
            hashed_pw = get_password_hash(safe_password)
        except Exception as hash_ex:
            print(f"[HASH ERROR] password={safe_password!r} len={len(safe_password.encode('utf-8'))}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Hash error: {hash_ex}")
        user = User(
            username=data.username,
            password_hash=hashed_pw,
            full_name=data.full_name,
            role="staff"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return {"id": user.id, "username": user.username, "full_name": user.full_name, "role": user.role}
    except Exception as ex:
        import traceback
        print("[REGISTER ERROR]", ex)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {ex}")

@app.post("/auth/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=400, detail="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    token = create_token({"sub": user.username, "role": user.role})
    return {"access_token": token, "token_type": "bearer", "role": user.role, "full_name": user.full_name or ""}

@app.post("/auth/admin-login", response_model=TokenResponse)
def admin_login(db: Session = Depends(get_db)):
    user = db.query(User).filter(User.role == "admin").first()
    if not user:
        # สร้าง admin อัตโนมัติถ้ายังไม่มีในฐานข้อมูล
        user = User(
            username="admin",
            password_hash=get_password_hash("admin1234"),
            full_name="Administrator",
            role="admin"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    token_str = create_token({"sub": user.username, "role": user.role})
    return {
        "access_token": token_str,
        "token_type": "bearer",
        "role": user.role,
        "full_name": user.full_name or "Administrator"
    }

# ==================== CATEGORIES ====================
@app.get("/categories", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Category).all()

@app.post("/categories", response_model=CategoryResponse)
def create_category(data: CategoryCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    cat = Category(**data.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat

# ==================== MEDICINES ====================
@app.get("/medicines", response_model=List[MedicineResponse])
def get_medicines(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return [medicine_to_response(m, db) for m in db.query(Medicine).all()]

@app.get("/medicines/{medicine_id}", response_model=MedicineResponse)
def get_medicine(medicine_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    m = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="ไม่พบยา")
    return medicine_to_response(m, db)

@app.post("/medicines", response_model=MedicineResponse)
def create_medicine(data: MedicineCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    m = Medicine(**data.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    return medicine_to_response(m, db)

@app.put("/medicines/{medicine_id}", response_model=MedicineResponse)
def update_medicine(medicine_id: int, data: MedicineUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    m = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="ไม่พบยา")
    # mark การแจ้งเตือนที่เกี่ยวข้องกับยานี้เป็น resolved
    db.query(Notification).filter(Notification.medicine_id == medicine_id, Notification.is_resolved == False).update({"is_resolved": True})
    db.commit()
    # อัปเดตยา
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(m, k, v)
    db.commit()
    db.refresh(m)
    # สร้างการแจ้งเตือนใหม่
    check_expiry_and_stock()
    days = (m.batches[0].expire_date - date.today()).days if m.batches else None
    return {**{c.name: getattr(m, c.name) for c in m.__table__.columns}, "days_until_expire": days}

@app.delete("/medicines/{medicine_id}")
def delete_medicine(medicine_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    m = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="ไม่พบยา")
    db.delete(m)
    db.commit()
    return {"message": "ลบยาสำเร็จ"}

@app.post("/medicines/{medicine_id}/image")
def upload_image(medicine_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), _=Depends(get_current_user)):
    m = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="ไม่พบยา")
    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)
    m.image_path = f"/uploads/{filename}"
    db.commit()
    return {"image_path": m.image_path}

# ==================== BATCHES ====================
@app.post("/medicines/{medicine_id}/batches", response_model=BatchResponse)
def add_batch(medicine_id: int, data: BatchCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    m = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="ไม่พบยา")
    b = Batch(medicine_id=medicine_id, **data.model_dump())
    db.add(b)
    db.commit()
    db.refresh(b)
    days = (b.expire_date - date.today()).days
    return {**{c.name: getattr(b, c.name) for c in b.__table__.columns}, "days_until_expire": days}

@app.put("/batches/{batch_id}", response_model=BatchResponse)
def update_batch(batch_id: int, data: BatchUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    b = db.query(Batch).filter(Batch.id == batch_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="ไม่พบ Batch")
    # mark การแจ้งเตือนที่เกี่ยวข้องกับ batch นี้เป็น resolved
    db.query(Notification).filter(Notification.batch_id == batch_id, Notification.is_resolved == False).update({"is_resolved": True})
    db.commit()
    # อัปเดต batch
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(b, k, v)
    db.commit()
    db.refresh(b)
    # สร้างการแจ้งเตือนใหม่
    check_expiry_and_stock()
    days = (b.expire_date - date.today()).days
    return {**{c.name: getattr(b, c.name) for c in b.__table__.columns}, "days_until_expire": days}

@app.delete("/batches/{batch_id}")
def delete_batch(batch_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    b = db.query(Batch).filter(Batch.id == batch_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="ไม่พบ Batch")
    db.delete(b)
    db.commit()
    return {"message": "ลบ Batch สำเร็จ"}

# ==================== NOTIFICATIONS ====================

# ดึงแจ้งเตือนทั้งหมด (optionally filter by is_resolved)
@app.get("/notifications", response_model=List[NotificationResponse])
def get_notifications(is_resolved: Optional[bool] = None, db: Session = Depends(get_db), _=Depends(get_current_user)):
    q = db.query(Notification)
    if is_resolved is not None:
        q = q.filter(Notification.is_resolved == is_resolved)
    return q.order_by(Notification.created_at.desc()).limit(100).all()

# ดึงแจ้งเตือนแยก 2 กลุ่ม (ยังไม่ได้แก้ไข/แก้ไขแล้ว) (return dict)
@app.get("/notifications/grouped")
def get_notifications_grouped(db: Session = Depends(get_db), _=Depends(get_current_user)):
    not_resolved = db.query(Notification).filter(Notification.is_resolved == False).order_by(Notification.created_at.desc()).all()
    resolved = db.query(Notification).filter(Notification.is_resolved == True).order_by(Notification.created_at.desc()).all()
    return {
        "unresolved": [NotificationResponse.model_validate(n).model_dump() for n in not_resolved],
        "resolved": [NotificationResponse.model_validate(n).model_dump() for n in resolved]
    }

@app.get("/notifications/unread-count")
def unread_count(db: Session = Depends(get_db), _=Depends(get_current_user)):
    count = db.query(Notification).filter(Notification.is_read == False).count()
    return {"count": count}

@app.put("/notifications/{noti_id}/read")
def mark_read(noti_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    n = db.query(Notification).filter(Notification.id == noti_id).first()
    if n:
        n.is_read = True
        db.commit()
    return {"message": "อ่านแล้ว"}

@app.put("/notifications/read-all")
def mark_all_read(db: Session = Depends(get_db), _=Depends(get_current_user)):
    db.query(Notification).filter(Notification.is_read == False).update({"is_read": True})
    db.commit()
    return {"message": "อ่านทั้งหมดแล้ว"}

# ==================== DELETE ALL NOTIFICATIONS ====================
@app.delete("/notifications/delete-all")
def delete_all_notifications(db: Session = Depends(get_db), _=Depends(get_current_user)):
    db.query(Notification).delete()
    db.commit()
    return {"message": "ลบการแจ้งเตือนทั้งหมดแล้ว"}

@app.post("/notifications/sync")
def sync_notifications(db: Session = Depends(get_db), _=Depends(get_current_user)):
    check_expiry_and_stock()
    return {"message": "Synced"}

# ==================== DASHBOARD ====================
@app.get("/dashboard")
def dashboard(db: Session = Depends(get_db), _=Depends(get_current_user)):
    today = date.today()
    total_medicines = db.query(Medicine).count()
    expiring_soon = db.query(Notification).filter(Notification.type == "expiry", Notification.is_resolved == False).count()
    expired = db.query(Notification).filter(Notification.type == "expired", Notification.is_resolved == False).count()
    low_stock = db.query(Notification).filter(Notification.type == "low_stock", Notification.is_resolved == False).count()
    unread_noti = db.query(Notification).filter(Notification.is_resolved == False).count()
    return {
        "total_medicines": total_medicines,
        "expiring_soon": expiring_soon,
        "expired": expired,
        "low_stock": low_stock,
        "unresolved_notifications": unread_noti
    }

@app.on_event("startup")
def startup():
    check_expiry_and_stock()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("pharmacy_api:app", host="0.0.0.0", port=8000, reload=True)