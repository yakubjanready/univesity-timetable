# UniSchedule — Universitet Jadval Tizimi v2.0

## Loyiha tuzilmasi
```
jadval-tizimi/
├── backend/
│   ├── main.py           # FastAPI backend (barcha API)
│   └── requirements.txt  # Python paketlari
└── frontend/
    └── index.html        # Zamonaviy SPA frontend
```

## O'rnatish va ishga tushirish

### 1. Backend (FastAPI)
```bash
cd backend

# Virtual muhit yaratish
python -m venv venv
source venv/bin/activate      # Linux/Mac
# venv\Scripts\activate       # Windows

# Paketlarni o'rnatish
pip install -r requirements.txt

# Serverni ishga tushirish
uvicorn main:app --reload --port 8000
```

Backend: http://localhost:8000
API docs: http://localhost:8000/docs

### 2. Frontend
```bash
# Shunchaki brauzerda oching:
frontend/index.html
```
Yoki local server bilan:
```bash
cd frontend
python -m http.server 3000
# http://localhost:3000 ga kiring
```

## Asosiy xususiyatlar

### ✅ Nizo aniqlash va bloklash
- Bir xil vaqtda bir auditoriyaga 2 ta dars — BLOKLANGAN
- Bir vaqtda o'qituvchining 2 ta darsi — BLOKLANGAN  
- Bir guruh bir vaqtda 2 ta dars — BLOKLANGAN
- Bo'sh auditoriyalar avtomatik taklif qilinadi

### ✅ Smena nazorati
- 1-smena: faqat 08:00–13:00 oralig'ida
- 2-smena: faqat 13:00–18:00 oralig'ida
- Buzilish — BLOKLANGAN

### ✅ O'qituvchi mavjudligi
- Har bir kun uchun vaqt slotlari
- Slot tashqarisida tayinlash — BLOKLANGAN

### ✅ Kritik holat avtomatizatsiyasi
- Auditoriya "kritik" holatga o'tganda
- Barcha darslar avtomatik qayta tayinlanadi
- Bo'sh auditoriya topilmasa → requires_action
- Bildirishnomalar avtomatik yuboriladi

### ✅ 3NF ma'lumotlar bazasi sxemasi
- TEACHER, SUBJECT, GROUP, ROOM — mustaqil sushnostlar
- SLOT — barcha sushnostlarning kesishish nuqtasi
- TEACHER_AVAILABILITY — alohida jadval (1NF)
- EQUIPMENT — alohida jadval (1NF)

## API Endpoints

| Method | URL | Tavsif |
|--------|-----|--------|
| GET/POST | /teachers | O'qituvchilar |
| PUT/DELETE | /teachers/{id} | Tahrirlash/o'chirish |
| GET/POST | /availability | Mavjudlik slotlari |
| GET/POST | /subjects | Fanlar |
| GET/POST | /groups | Guruhlar |
| GET/POST | /rooms | Auditoriyalar |
| GET/POST | /slots | Darslar (nizo tekshiruvi bilan) |
| DELETE | /slots/{id} | Bekor qilish |
| GET | /notifications | Bildirishnomalar |
| GET | /stats | Statistika |
| POST | /seed | Demo ma'lumotlar |