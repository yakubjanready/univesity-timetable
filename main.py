from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Time, Enum, ForeignKey, DateTime, Text, JSON, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, time
import enum

DATABASE_URL = "sqlite:///"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(title="Jadval Tizimi API", version="2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ─────────────── ENUMS ───────────────
class SmenaEnum(str, enum.Enum):
    first = "first"
    second = "second"
    mixed = "mixed"

class AuditoriyaTuriEnum(str, enum.Enum):
    lecture = "lecture"
    lab = "lab"
    computer = "computer"

class AuditoriyaHolatEnum(str, enum.Enum):
    active = "active"
    maintenance = "maintenance"
    critical = "critical"

class MashgulotTuriEnum(str, enum.Enum):
    lecture = "lecture"
    practical = "practical"
    lab = "lab"

class SlotHolatEnum(str, enum.Enum):
    scheduled = "scheduled"
    requires_action = "requires_action"
    cancelled = "cancelled"

class HaftaKuniEnum(str, enum.Enum):
    Du = "Du"
    Se = "Se"
    Ch = "Ch"
    Pa = "Pa"
    Ju = "Ju"

class BildirHodisaEnum(str, enum.Enum):
    reassigned = "reassigned"
    cancelled = "cancelled"
    conflict = "conflict"
    no_room = "no_room"

class BildirQabHolatEnum(str, enum.Enum):
    teacher = "teacher"
    student = "student"
    dispatcher = "dispatcher"
    admin = "admin"

class HarakatEnum(str, enum.Enum):
    create = "create"
    update = "update"
    cancel = "cancel"
    reassign = "reassign"

# ─────────────── DB MODELS ───────────────
class Teacher(Base):
    __tablename__ = "teacher"
    id = Column(Integer, primary_key=True, index=True)
    fio = Column(String(200), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    telefon = Column(String(20))
    availability = relationship("TeacherAvailability", back_populates="teacher", cascade="all, delete-orphan")
    slots = relationship("Slot", back_populates="teacher")

class TeacherAvailability(Base):
    __tablename__ = "teacher_availability"
    id = Column(Integer, primary_key=True, index=True)
    oqituvchi_id = Column(Integer, ForeignKey("teacher.id"), nullable=False)
    hafta_kuni = Column(Enum(HaftaKuniEnum), nullable=False)
    boshlanish_vaqti = Column(String(5), nullable=False)
    tugash_vaqti = Column(String(5), nullable=False)
    teacher = relationship("Teacher", back_populates="availability")

class Subject(Base):
    __tablename__ = "subject"
    id = Column(Integer, primary_key=True, index=True)
    nomi = Column(String(200), nullable=False)
    kodi = Column(String(20), unique=True, nullable=False)
    mashg_turi = Column(Enum(MashgulotTuriEnum), nullable=False)
    haftada_soat = Column(Integer, nullable=False)
    talablar = Column(Text)
    slots = relationship("Slot", back_populates="subject")

class StudentGroup(Base):
    __tablename__ = "student_group"
    id = Column(Integer, primary_key=True, index=True)
    nomi = Column(String(50), nullable=False)
    talabalar_soni = Column(Integer, nullable=False)
    smenasi = Column(Enum(SmenaEnum), nullable=False)
    slots = relationship("Slot", back_populates="group")

class Room(Base):
    __tablename__ = "room"
    id = Column(Integer, primary_key=True, index=True)
    raqami = Column(String(20), nullable=False)
    sigimi = Column(Integer, nullable=False)
    turi = Column(Enum(AuditoriyaTuriEnum), nullable=False)
    korpus = Column(String(50))
    holat = Column(Enum(AuditoriyaHolatEnum), default=AuditoriyaHolatEnum.active)
    equipment = relationship("Equipment", back_populates="room", cascade="all, delete-orphan")
    slots = relationship("Slot", back_populates="room")

class Equipment(Base):
    __tablename__ = "equipment"
    id = Column(Integer, primary_key=True, index=True)
    auditoriya_id = Column(Integer, ForeignKey("room.id"), nullable=False)
    turi = Column(String(100), nullable=False)
    room = relationship("Room", back_populates="equipment")

class Slot(Base):
    __tablename__ = "slot"
    id = Column(Integer, primary_key=True, index=True)
    fan_id = Column(Integer, ForeignKey("subject.id"), nullable=False)
    oqituvchi_id = Column(Integer, ForeignKey("teacher.id"), nullable=False)
    guruh_id = Column(Integer, ForeignKey("student_group.id"), nullable=False)
    auditoriya_id = Column(Integer, ForeignKey("room.id"), nullable=False)
    hafta_kuni = Column(Enum(HaftaKuniEnum), nullable=False)
    boshlanish_vaqti = Column(String(5), nullable=False)
    tugash_vaqti = Column(String(5), nullable=False)
    holat = Column(Enum(SlotHolatEnum), default=SlotHolatEnum.scheduled)
    subject = relationship("Subject", back_populates="slots")
    teacher = relationship("Teacher", back_populates="slots")
    group = relationship("StudentGroup", back_populates="slots")
    room = relationship("Room", back_populates="slots")

class Notification(Base):
    __tablename__ = "notification"
    id = Column(Integer, primary_key=True, index=True)
    slot_id = Column(Integer, ForeignKey("slot.id"))
    qabul_qiluvchi_id = Column(Integer)
    qabul_qiluvchi_turi = Column(Enum(BildirQabHolatEnum))
    hodisa_turi = Column(Enum(BildirHodisaEnum))
    matni = Column(Text)
    yuborilgan_sana = Column(DateTime, default=datetime.now)
    holat = Column(String(20), default="sent")

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True, index=True)
    slot_id = Column(Integer, ForeignKey("slot.id"))
    foydalanuvchi_id = Column(Integer, default=1)
    harakat = Column(Enum(HarakatEnum))
    eski_qiymat = Column(JSON)
    yangi_qiymat = Column(JSON)
    sana_vaqt = Column(DateTime, default=datetime.now)

Base.metadata.create_all(bind=engine)

# ─────────────── DEPENDENCY ───────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ─────────────── PYDANTIC SCHEMAS ───────────────
class TeacherCreate(BaseModel):
    fio: str
    email: str
    telefon: Optional[str] = None

class TeacherOut(TeacherCreate):
    id: int
    class Config: from_attributes = True

class AvailabilityCreate(BaseModel):
    oqituvchi_id: int
    hafta_kuni: HaftaKuniEnum
    boshlanish_vaqti: str
    tugash_vaqti: str

class AvailabilityOut(AvailabilityCreate):
    id: int
    class Config: from_attributes = True

class SubjectCreate(BaseModel):
    nomi: str
    kodi: str
    mashg_turi: MashgulotTuriEnum
    haftada_soat: int
    talablar: Optional[str] = None

class SubjectOut(SubjectCreate):
    id: int
    class Config: from_attributes = True

class GroupCreate(BaseModel):
    nomi: str
    talabalar_soni: int
    smenasi: SmenaEnum

class GroupOut(GroupCreate):
    id: int
    class Config: from_attributes = True

class RoomCreate(BaseModel):
    raqami: str
    sigimi: int
    turi: AuditoriyaTuriEnum
    korpus: Optional[str] = None
    holat: AuditoriyaHolatEnum = AuditoriyaHolatEnum.active

class RoomOut(RoomCreate):
    id: int
    class Config: from_attributes = True

class SlotCreate(BaseModel):
    fan_id: int
    oqituvchi_id: int
    guruh_id: int
    auditoriya_id: int
    hafta_kuni: HaftaKuniEnum
    boshlanish_vaqti: str
    tugash_vaqti: str

class SlotOut(BaseModel):
    id: int
    fan_id: int
    oqituvchi_id: int
    guruh_id: int
    auditoriya_id: int
    hafta_kuni: HaftaKuniEnum
    boshlanish_vaqti: str
    tugash_vaqti: str
    holat: SlotHolatEnum
    subject: Optional[SubjectOut] = None
    teacher: Optional[TeacherOut] = None
    group: Optional[GroupOut] = None
    room: Optional[RoomOut] = None
    class Config: from_attributes = True

class NotificationOut(BaseModel):
    id: int
    slot_id: Optional[int]
    qabul_qiluvchi_id: Optional[int]
    qabul_qiluvchi_turi: Optional[BildirQabHolatEnum]
    hodisa_turi: Optional[BildirHodisaEnum]
    matni: Optional[str]
    yuborilgan_sana: Optional[datetime]
    holat: Optional[str]
    class Config: from_attributes = True

# ─────────────── HELPERS ───────────────
def time_to_mins(t: str) -> int:
    h, m = map(int, t.split(":"))
    return h * 60 + m

def times_overlap(s1: str, e1: str, s2: str, e2: str) -> bool:
    return time_to_mins(s1) < time_to_mins(e2) and time_to_mins(e1) > time_to_mins(s2)

def check_room_conflict(db: Session, room_id: int, day: str, start: str, end: str, exclude_slot_id: int = None):
    q = db.query(Slot).filter(
        Slot.auditoriya_id == room_id,
        Slot.hafta_kuni == day,
        Slot.holat != SlotHolatEnum.cancelled
    )
    if exclude_slot_id:
        q = q.filter(Slot.id != exclude_slot_id)
    for s in q.all():
        if times_overlap(start, end, s.boshlanish_vaqti, s.tugash_vaqti):
            return s
    return None

def check_teacher_conflict(db: Session, teacher_id: int, day: str, start: str, end: str, exclude_slot_id: int = None):
    q = db.query(Slot).filter(
        Slot.oqituvchi_id == teacher_id,
        Slot.hafta_kuni == day,
        Slot.holat != SlotHolatEnum.cancelled
    )
    if exclude_slot_id:
        q = q.filter(Slot.id != exclude_slot_id)
    for s in q.all():
        if times_overlap(start, end, s.boshlanish_vaqti, s.tugash_vaqti):
            return s
    return None

def check_group_conflict(db: Session, group_id: int, day: str, start: str, end: str, exclude_slot_id: int = None):
    q = db.query(Slot).filter(
        Slot.guruh_id == group_id,
        Slot.hafta_kuni == day,
        Slot.holat != SlotHolatEnum.cancelled
    )
    if exclude_slot_id:
        q = q.filter(Slot.id != exclude_slot_id)
    for s in q.all():
        if times_overlap(start, end, s.boshlanish_vaqti, s.tugash_vaqti):
            return s
    return None

def check_teacher_availability(db: Session, teacher_id: int, day: str, start: str, end: str) -> bool:
    avail = db.query(TeacherAvailability).filter(
        TeacherAvailability.oqituvchi_id == teacher_id,
        TeacherAvailability.hafta_kuni == day
    ).all()
    if not avail:
        return True  # No restrictions set = always available
    for a in avail:
        if time_to_mins(a.boshlanish_vaqti) <= time_to_mins(start) and time_to_mins(end) <= time_to_mins(a.tugash_vaqti):
            return True
    return False

def check_group_smena(group: StudentGroup, start: str, end: str) -> bool:
    s = time_to_mins(start)
    e = time_to_mins(end)
    if group.smenasi == SmenaEnum.first:
        return e <= time_to_mins("13:00")
    elif group.smenasi == SmenaEnum.second:
        return s >= time_to_mins("13:00")
    return True

def send_notification(db: Session, slot_id: int, recipient_id: int, recipient_type: str, event_type: str, text: str):
    n = Notification(
        slot_id=slot_id, qabul_qiluvchi_id=recipient_id,
        qabul_qiluvchi_turi=recipient_type, hodisa_turi=event_type, matni=text
    )
    db.add(n)

def log_action(db: Session, slot_id: int, action: str, old_val=None, new_val=None):
    log = AuditLog(slot_id=slot_id, harakat=action, eski_qiymat=old_val, yangi_qiymat=new_val)
    db.add(log)

def find_alternative_rooms(db: Session, day: str, start: str, end: str, min_capacity: int, room_type: str):
    rooms = db.query(Room).filter(
        Room.holat == AuditoriyaHolatEnum.active,
        Room.sigimi >= min_capacity,
        Room.turi == room_type
    ).all()
    result = []
    for r in rooms:
        if not check_room_conflict(db, r.id, day, start, end):
            result.append(r)
    return result

def handle_critical_room(db: Session, room_id: int):
    affected = db.query(Slot).filter(
        Slot.auditoriya_id == room_id,
        Slot.holat == SlotHolatEnum.scheduled
    ).all()
    reassigned, failed = 0, 0
    for slot in affected:
        group = db.query(StudentGroup).get(slot.guruh_id)
        subject = db.query(Subject).get(slot.fan_id)
        alts = find_alternative_rooms(db, slot.hafta_kuni, slot.boshlanish_vaqti, slot.tugash_vaqti, group.talabalar_soni, subject.mashg_turi)
        old_room_id = slot.auditoriya_id
        if alts:
            slot.auditoriya_id = alts[0].id
            log_action(db, slot.id, "reassign", {"auditoriya_id": old_room_id}, {"auditoriya_id": alts[0].id})
            send_notification(db, slot.id, slot.oqituvchi_id, "teacher", "reassigned",
                f"{subject.nomi} darsi {alts[0].raqami}-auditoriyaga ko'chirildi")
            send_notification(db, slot.id, slot.guruh_id, "student", "reassigned",
                f"{subject.nomi} darsi {alts[0].raqami}-auditoriyaga ko'chirildi")
            reassigned += 1
        else:
            slot.holat = SlotHolatEnum.requires_action
            send_notification(db, slot.id, 1, "dispatcher", "no_room",
                f"{subject.nomi} | {group.nomi} | {slot.hafta_kuni} | {slot.boshlanish_vaqti} uchun bo'sh auditoriya yo'q")
            failed += 1
    db.commit()
    return {"reassigned": reassigned, "requires_action": failed}

# ─────────────── ROUTES: TEACHERS ───────────────
@app.get("/teachers", response_model=List[TeacherOut])
def get_teachers(db: Session = Depends(get_db)):
    return db.query(Teacher).all()

@app.post("/teachers", response_model=TeacherOut)
def create_teacher(data: TeacherCreate, db: Session = Depends(get_db)):
    if db.query(Teacher).filter(Teacher.email == data.email).first():
        raise HTTPException(400, "Bu email allaqachon mavjud")
    t = Teacher(**data.dict())
    db.add(t); db.commit(); db.refresh(t)
    return t

@app.put("/teachers/{id}", response_model=TeacherOut)
def update_teacher(id: int, data: TeacherCreate, db: Session = Depends(get_db)):
    t = db.query(Teacher).get(id)
    if not t: raise HTTPException(404, "O'qituvchi topilmadi")
    for k, v in data.dict().items(): setattr(t, k, v)
    db.commit(); db.refresh(t)
    return t

@app.delete("/teachers/{id}")
def delete_teacher(id: int, db: Session = Depends(get_db)):
    t = db.query(Teacher).get(id)
    if not t: raise HTTPException(404, "O'qituvchi topilmadi")
    db.delete(t); db.commit()
    return {"ok": True}

# ─────────────── ROUTES: AVAILABILITY ───────────────
@app.get("/teachers/{teacher_id}/availability", response_model=List[AvailabilityOut])
def get_availability(teacher_id: int, db: Session = Depends(get_db)):
    return db.query(TeacherAvailability).filter(TeacherAvailability.oqituvchi_id == teacher_id).all()

@app.post("/availability", response_model=AvailabilityOut)
def create_availability(data: AvailabilityCreate, db: Session = Depends(get_db)):
    a = TeacherAvailability(**data.dict())
    db.add(a); db.commit(); db.refresh(a)
    return a

@app.delete("/availability/{id}")
def delete_availability(id: int, db: Session = Depends(get_db)):
    a = db.query(TeacherAvailability).get(id)
    if not a: raise HTTPException(404)
    db.delete(a); db.commit()
    return {"ok": True}

# ─────────────── ROUTES: SUBJECTS ───────────────
@app.get("/subjects", response_model=List[SubjectOut])
def get_subjects(db: Session = Depends(get_db)):
    return db.query(Subject).all()

@app.post("/subjects", response_model=SubjectOut)
def create_subject(data: SubjectCreate, db: Session = Depends(get_db)):
    if db.query(Subject).filter(Subject.kodi == data.kodi).first():
        raise HTTPException(400, "Bu fan kodi allaqachon mavjud")
    s = Subject(**data.dict())
    db.add(s); db.commit(); db.refresh(s)
    return s

@app.put("/subjects/{id}", response_model=SubjectOut)
def update_subject(id: int, data: SubjectCreate, db: Session = Depends(get_db)):
    s = db.query(Subject).get(id)
    if not s: raise HTTPException(404)
    for k, v in data.dict().items(): setattr(s, k, v)
    db.commit(); db.refresh(s)
    return s

@app.delete("/subjects/{id}")
def delete_subject(id: int, db: Session = Depends(get_db)):
    s = db.query(Subject).get(id)
    if not s: raise HTTPException(404)
    db.delete(s); db.commit()
    return {"ok": True}

# ─────────────── ROUTES: GROUPS ───────────────
@app.get("/groups", response_model=List[GroupOut])
def get_groups(db: Session = Depends(get_db)):
    return db.query(StudentGroup).all()

@app.post("/groups", response_model=GroupOut)
def create_group(data: GroupCreate, db: Session = Depends(get_db)):
    g = StudentGroup(**data.dict())
    db.add(g); db.commit(); db.refresh(g)
    return g

@app.put("/groups/{id}", response_model=GroupOut)
def update_group(id: int, data: GroupCreate, db: Session = Depends(get_db)):
    g = db.query(StudentGroup).get(id)
    if not g: raise HTTPException(404)
    for k, v in data.dict().items(): setattr(g, k, v)
    db.commit(); db.refresh(g)
    return g

@app.delete("/groups/{id}")
def delete_group(id: int, db: Session = Depends(get_db)):
    g = db.query(StudentGroup).get(id)
    if not g: raise HTTPException(404)
    db.delete(g); db.commit()
    return {"ok": True}

# ─────────────── ROUTES: ROOMS ───────────────
@app.get("/rooms", response_model=List[RoomOut])
def get_rooms(db: Session = Depends(get_db)):
    return db.query(Room).all()

@app.post("/rooms", response_model=RoomOut)
def create_room(data: RoomCreate, db: Session = Depends(get_db)):
    r = Room(**data.dict())
    db.add(r); db.commit(); db.refresh(r)
    return r

@app.put("/rooms/{id}", response_model=RoomOut)
def update_room(id: int, data: RoomCreate, db: Session = Depends(get_db)):
    r = db.query(Room).get(id)
    if not r: raise HTTPException(404)
    old_status = r.holat
    for k, v in data.dict().items(): setattr(r, k, v)
    db.commit(); db.refresh(r)
    if old_status != AuditoriyaHolatEnum.critical and r.holat == AuditoriyaHolatEnum.critical:
        handle_critical_room(db, id)
    return r

@app.delete("/rooms/{id}")
def delete_room(id: int, db: Session = Depends(get_db)):
    r = db.query(Room).get(id)
    if not r: raise HTTPException(404)
    db.delete(r); db.commit()
    return {"ok": True}

@app.get("/rooms/{room_id}/free-slots")
def get_free_slots(room_id: int, day: str, start: str, end: str, db: Session = Depends(get_db)):
    room = db.query(Room).get(room_id)
    if not room: raise HTTPException(404)
    conflict = check_room_conflict(db, room_id, day, start, end)
    return {"is_free": conflict is None, "conflict_slot": SlotOut.from_orm(conflict) if conflict else None}

# ─────────────── ROUTES: SLOTS ───────────────
@app.get("/slots", response_model=List[SlotOut])
def get_slots(group_id: Optional[int] = None, teacher_id: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(Slot)
    if group_id: q = q.filter(Slot.guruh_id == group_id)
    if teacher_id: q = q.filter(Slot.oqituvchi_id == teacher_id)
    return q.all()

@app.post("/slots", response_model=SlotOut)
def create_slot(data: SlotCreate, db: Session = Depends(get_db)):
    group = db.query(StudentGroup).get(data.guruh_id)
    subject = db.query(Subject).get(data.fan_id)
    room = db.query(Room).get(data.auditoriya_id)
    teacher = db.query(Teacher).get(data.oqituvchi_id)

    if not all([group, subject, room, teacher]):
        raise HTTPException(404, "Bir yoki bir nechta resurs topilmadi")

    if room.holat == AuditoriyaHolatEnum.critical:
        raise HTTPException(400, "Bu auditoriya kritik holatda, foydalanib bo'lmaydi")

    if room.sigimi < group.talabalar_soni:
        raise HTTPException(400, f"Auditoriya sig'imi ({room.sigimi}) guruh talabalar sonidan ({group.talabalar_soni}) kam")

    if not check_group_smena(group, data.boshlanish_vaqti, data.tugash_vaqti):
        smena_labels = {"first": "1-smena (08:00-13:00)", "second": "2-smena (13:00-18:00)", "mixed": "aralash"}
        raise HTTPException(400, f"Guruh smenasiga mos kelmaydi: {smena_labels[group.smenasi]}")

    if not check_teacher_availability(db, data.oqituvchi_id, data.hafta_kuni, data.boshlanish_vaqti, data.tugash_vaqti):
        raise HTTPException(400, "O'qituvchi bu vaqtda mavjud emas (mavjudlik jadvali)")

    rc = check_room_conflict(db, data.auditoriya_id, data.hafta_kuni, data.boshlanish_vaqti, data.tugash_vaqti)
    if rc:
        t = db.query(Teacher).get(rc.oqituvchi_id)
        s = db.query(Subject).get(rc.fan_id)
        alts = find_alternative_rooms(db, data.hafta_kuni, data.boshlanish_vaqti, data.tugash_vaqti, group.talabalar_soni, subject.mashg_turi)
        alt_list = [{"id": r.id, "raqami": r.raqami, "korpus": r.korpus, "sigimi": r.sigimi} for r in alts]
        raise HTTPException(409, detail={
            "message": f"{room.raqami}-auditoriya {data.hafta_kuni} {data.boshlanish_vaqti} da band. O'qituvchi: {t.fio} — {s.nomi}",
            "alternatives": alt_list
        })

    tc = check_teacher_conflict(db, data.oqituvchi_id, data.hafta_kuni, data.boshlanish_vaqti, data.tugash_vaqti)
    if tc:
        raise HTTPException(409, detail={"message": f"O'qituvchi {data.hafta_kuni} {data.boshlanish_vaqti} da boshqa darsda", "alternatives": []})

    gc = check_group_conflict(db, data.guruh_id, data.hafta_kuni, data.boshlanish_vaqti, data.tugash_vaqti)
    if gc:
        raise HTTPException(409, detail={"message": f"Guruh {data.hafta_kuni} {data.boshlanish_vaqti} da boshqa darsda", "alternatives": []})

    slot = Slot(**data.dict())
    db.add(slot); db.commit(); db.refresh(slot)
    log_action(db, slot.id, "create", None, data.dict())
    db.commit()
    return slot

@app.delete("/slots/{id}")
def delete_slot(id: int, db: Session = Depends(get_db)):
    slot = db.query(Slot).get(id)
    if not slot: raise HTTPException(404)
    log_action(db, slot.id, "cancel", {"holat": slot.holat}, {"holat": "cancelled"})
    slot.holat = SlotHolatEnum.cancelled
    db.commit()
    return {"ok": True}

# ─────────────── ROUTES: NOTIFICATIONS ───────────────
@app.get("/notifications", response_model=List[NotificationOut])
def get_notifications(db: Session = Depends(get_db)):
    return db.query(Notification).order_by(Notification.yuborilgan_sana.desc()).limit(50).all()

# ─────────────── ROUTES: STATS ───────────────
@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    return {
        "teachers": db.query(Teacher).count(),
        "subjects": db.query(Subject).count(),
        "groups": db.query(StudentGroup).count(),
        "rooms": db.query(Room).count(),
        "slots_active": db.query(Slot).filter(Slot.holat == SlotHolatEnum.scheduled).count(),
        "slots_requires_action": db.query(Slot).filter(Slot.holat == SlotHolatEnum.requires_action).count(),
        "rooms_critical": db.query(Room).filter(Room.holat == AuditoriyaHolatEnum.critical).count(),
        "notifications": db.query(Notification).count(),
    }

# ─────────────── SEED DATA ───────────────
@app.post("/seed")
def seed_data(db: Session = Depends(get_db)):
    if db.query(Teacher).count() > 0:
        return {"message": "Ma'lumotlar allaqachon mavjud"}

    teachers = [
        Teacher(fio="Petrov Ivan Vasilyevich", email="petrov@univ.uz", telefon="+998901234567"),
        Teacher(fio="Sergeyeva Malika Hamidovna", email="sergeyeva@univ.uz", telefon="+998901234568"),
        Teacher(fio="Karimov Jasur Aliyevich", email="karimov@univ.uz", telefon="+998901234569"),
    ]
    for t in teachers: db.add(t)
    db.flush()

    avail = [
        TeacherAvailability(oqituvchi_id=teachers[0].id, hafta_kuni="Du", boshlanish_vaqti="08:00", tugash_vaqti="13:00"),
        TeacherAvailability(oqituvchi_id=teachers[0].id, hafta_kuni="Ch", boshlanish_vaqti="08:00", tugash_vaqti="13:00"),
        TeacherAvailability(oqituvchi_id=teachers[1].id, hafta_kuni="Du", boshlanish_vaqti="09:00", tugash_vaqti="18:00"),
        TeacherAvailability(oqituvchi_id=teachers[1].id, hafta_kuni="Se", boshlanish_vaqti="09:00", tugash_vaqti="18:00"),
        TeacherAvailability(oqituvchi_id=teachers[2].id, hafta_kuni="Pa", boshlanish_vaqti="08:00", tugash_vaqti="18:00"),
        TeacherAvailability(oqituvchi_id=teachers[2].id, hafta_kuni="Ju", boshlanish_vaqti="08:00", tugash_vaqti="18:00"),
    ]
    for a in avail: db.add(a)

    subjects = [
        Subject(nomi="Matematika", kodi="MATH101", mashg_turi="lecture", haftada_soat=4, talablar="Dоska"),
        Subject(nomi="Fizika", kodi="PHYS101", mashg_turi="lab", haftada_soat=3, talablar="Laboratoriya"),
        Subject(nomi="Dasturlash asoslari", kodi="CS101", mashg_turi="practical", haftada_soat=4, talablar="Kompyuterlar"),
        Subject(nomi="Ingliz tili", kodi="ENG101", mashg_turi="practical", haftada_soat=2, talablar=""),
    ]
    for s in subjects: db.add(s)

    groups = [
        StudentGroup(nomi="CS-101", talabalar_soni=25, smenasi="first"),
        StudentGroup(nomi="MATH-202", talabalar_soni=30, smenasi="second"),
        StudentGroup(nomi="PHYS-301", talabalar_soni=20, smenasi="mixed"),
    ]
    for g in groups: db.add(g)

    rooms = [
        Room(raqami="300", sigimi=35, turi="lecture", korpus="A-korpus", holat="active"),
        Room(raqami="305", sigimi=30, turi="lecture", korpus="A-korpus", holat="active"),
        Room(raqami="Lab-1", sigimi=25, turi="lab", korpus="B-korpus", holat="active"),
        Room(raqami="PC-201", sigimi=30, turi="computer", korpus="C-korpus", holat="active"),
        Room(raqami="210", sigimi=40, turi="lecture", korpus="A-korpus", holat="active"),
    ]
    for r in rooms: db.add(r)
    db.flush()

    slots = [
        Slot(fan_id=subjects[0].id, oqituvchi_id=teachers[0].id, guruh_id=groups[0].id,
             auditoriya_id=rooms[0].id, hafta_kuni="Du", boshlanish_vaqti="09:00", tugash_vaqti="10:30"),
        Slot(fan_id=subjects[2].id, oqituvchi_id=teachers[2].id, guruh_id=groups[0].id,
             auditoriya_id=rooms[3].id, hafta_kuni="Pa", boshlanish_vaqti="10:00", tugash_vaqti="11:30"),
        Slot(fan_id=subjects[3].id, oqituvchi_id=teachers[1].id, guruh_id=groups[1].id,
             auditoriya_id=rooms[1].id, hafta_kuni="Du", boshlanish_vaqti="14:00", tugash_vaqti="15:30"),
    ]
    for s in slots: db.add(s)
    db.commit()
    return {"message": "Demo ma'lumotlar yuklandi"}
