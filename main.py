from fastapi import FastAPI, Request, Form
from fastapi.responses import FileResponse, HTMLResponse
import sqlite3
from datetime import datetime, timedelta

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

def get_kst_now():
    return (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S")

def judge_status(count: int):
    if count <= 20: return "여유 (쾌적해요! 🏃‍♂️)"
    elif 21 <= count <= 30: return "보통 (운동하기 적당해요. 🙂)"
    else: return "붐빔 (나중에 오시는 건 어떨까요? 😅)"

@app.get("/")
def read_root():
    return {"message": "FeelGym Server is Running"}

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

@app.get("/history")
def get_history():
    conn = sqlite3.connect("gym.db")
    cursor = conn.cursor()
    cursor.execute("SELECT count, timestamp FROM gym_logs ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    html_content = """
    <html>
    <head>
        <title>필짐 공릉점 기록</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: sans-serif; text-align: center; padding: 20px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: center; }
            th { background-color: #f4f4f9; }
        </style>
    </head>
    <body>
        <h2>📊 전체 혼잡도 기록</h2>
        <table><tr><th>시간</th><th>인원수</th><th>상태</th></tr>
    """
    for row in rows:
        html_content += f"<tr><td>{row[1]}</td><td>{row[0]}명</td><td>{judge_status(row[0])}</td></tr>"
    html_content += "</table><br><a href='/admin'>관리자 페이지로</a></body></html>"
    return HTMLResponse(content=html_content)

@app.post("/kakao")
async def kakao_bot():
    conn = sqlite3.connect("gym.db")
    cursor = conn.cursor()
    cursor.execute("SELECT count FROM gym_logs ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    msg = f"현재 필짐 인원은 약 {row[0]}명, [{judge_status(row[0])}] 상태입니다! 💪" if row else "기록된 정보가 없습니다."
    return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": msg}}]}}

# --- 관리자 페이지 섹션 ---
ADMIN_PASSWORD = "1234"

@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    return """
    <html>
    <head>
        <title>필짐 관리자 전용</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: sans-serif; text-align: center; padding: 50px 20px; background-color: #f4f4f9; }
            .card { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 400px; margin: auto; }
            input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
            button { width: 100%; padding: 12px; background-color: #28a745; color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>🔐 필짐 관리자</h2>
            <form action="/admin/update" method="post">
                <input type="password" name="password" placeholder="비밀번호" required>
                <input type="number" name="count" placeholder="현재 인원수" required>
                <button type="submit">업데이트</button>
            </form>
            <br><a href="/history">기록 확인</a>
        </div>
    </body>
    </html>
    """

@app.post("/admin/update")
async def admin_update(password: str = Form(...), count: int = Form(...)):
    if password != ADMIN_PASSWORD:
        return HTMLResponse("<script>alert('비밀번호 불일치'); history.back();</script>")
    
    kst_now = get_kst_now()
    conn = sqlite3.connect("gym.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO gym_logs (count, timestamp) VALUES (?, ?)", (count, kst_now))
    conn.commit()
    conn.close()
    return HTMLResponse(f"<script>alert('{count}명 업데이트 완료!'); location.href='/admin';</script>")