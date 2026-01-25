from fastapi import FastAPI
from fastapi.responses import FileResponse
import sqlite3
from datetime import datetime, timedelta # 시간 조절 도구 추가

app = FastAPI()

def init_db():
    conn = sqlite3.connect("gym.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gym_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            count INTEGER,
            timestamp DATETIME
        )
    """)
    conn.commit()
    conn.close()

init_db()

# 한국 시간을 가져오는 함수
def get_kst_now():
    # UTC 기준 시간에 9시간을 더합니다
    return (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S")

def judge_status(count: int):
    if count <= 20: return "여유 (쾌적해요! 🏃‍♂️)"
    elif 21 <= count <= 30: return "보통 (운동하기 적당해요. 🙂)"
    else: return "붐빔 (나중에 오시는 건 어떨까요? 😅)"

@app.get("/")
def read_root():
    return FileResponse("index.html")

@app.get("/update")
def update_count(count: int):
    kst_now = get_kst_now() # 한국 시간 생성
    conn = sqlite3.connect("gym.db")
    cursor = conn.cursor()
    # 자동으로 저장되게 두지 않고, 우리가 만든 한국 시간을 직접 넣습니다
    cursor.execute("INSERT INTO gym_logs (count, timestamp) VALUES (?, ?)", (count, kst_now))
    conn.commit()
    conn.close()
    return {"message": f"현재 {judge_status(count)} 저장 완료!", "시간": kst_now}

@app.get("/current")
def get_current():
    conn = sqlite3.connect("gym.db")
    cursor = conn.cursor()
    cursor.execute("SELECT count, timestamp FROM gym_logs ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"현재_인원": row[0], "상태": judge_status(row[0]), "업데이트_시간": row[1]}
    return {"message": "데이터 없음"}