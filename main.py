from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
import sqlite3
from datetime import datetime, timedelta

app = FastAPI()

# DB 초기화
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

# 시간 및 상태 판정 함수
def get_kst_now():
    return (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S")

def judge_status(count: int):
    if count <= 20: return "여유 (쾌적해요! 🏃‍♂️)"
    elif 21 <= count <= 30: return "보통 (운동하기 적당해요. 🙂)"
    else: return "붐빔 (나중에 오시는 건 어떨까요? 😅)"

# 기본 페이지
@app.get("/")
def read_root():
    return {"status": "running", "message": "FeelGym Server"}

# 카카오톡 챗봇 응답
@app.post("/kakao")
async def kakao_bot():
    conn = sqlite3.connect("gym.db")
    cursor = conn.cursor()
    cursor.execute("SELECT count FROM gym_logs ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if row:
        count = row[0]
        msg = f"현재 필짐 인원은 약 {count}명이며, [{judge_status(count)}] 상태입니다! 💪"
    else:
        msg = "아직 기록된 정보가 없습니다."
    
    return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": msg}}]}}

# 기록 조회 페이지
@app.get("/history", response_class=HTMLResponse)
def get_history():
    conn = sqlite3.connect("gym.db")
    cursor = conn.cursor()
    cursor.execute("SELECT count, timestamp FROM gym_logs ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    html = "<html><body style='text-align:center;'><h2>📊 전체 기록</h2><table border='1' style='margin:auto;'>"
    html += "<tr><th>시간</th><th>인원</th><th>상태</th></tr>"
    for row in rows:
        html += f"<tr><td>{row[1]}</td><td>{row[0]}명</td><td>{judge_status(row[0])}</td></tr>"
    html += "</table><br><a href='/admin'>관리자 페이지로</a></body></html>"
    return html

# --- 관리자 기능 섹션 ---
ADMIN_PASSWORD = "1234"

@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    return """
    <html>
    <head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
    <body style="text-align:center; padding-top:50px; font-family:sans-serif;">
        <div style="display:inline-block; padding:20px; border:1px solid #ccc; border-radius:10px;">
            <h2>🔐 필짐 관리자</h2>
            <form action="/admin/update" method="post">
                <input type="password" name="password" placeholder="비밀번호" style="padding:10px; margin-bottom:10px;"><br>
                <input type="number" name="count" placeholder="현재 인원수" style="padding:10px; margin-bottom:10px;"><br>
                <button type="submit" style="padding:10px 20px; background:#28a745; color:white; border:none; border-radius:5px;">업데이트</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.post("/admin/update")
async def admin_update(password: str = Form(...), count: int = Form(...)):
    if password != ADMIN_PASSWORD:
        return HTMLResponse("<script>alert('비밀번호가 틀렸습니다!'); history.back();</script>")
    
    kst_now = get_kst_now()
    conn = sqlite3.connect("gym.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO gym_logs (count, timestamp) VALUES (?, ?)", (count, kst_now))
    conn.commit()
    conn.close()
    return HTMLResponse(f"<script>alert('{count}명으로 업데이트 완료!'); location.href='/admin';</script>")