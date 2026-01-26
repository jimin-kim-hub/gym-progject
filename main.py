from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
import sqlite3
from datetime import datetime, timedelta

app = FastAPI()

# 1. 데이터베이스 초기화 (기록 저장용)
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

# 2. 한국 시간 및 상태 판정 함수
def get_kst_now():
    return (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S")

def judge_status(count: int):
    if count <= 20: return "여유 (쾌적해요! 🏃‍♂️)"
    elif count <= 30: return "보통 (운동하기 적당해요. 🙂)"
    else: return "붐빔 (나중에 오시는 건 어떨까요? 😅)"

# 3. 메인 페이지 및 기록 확인
@app.get("/")
def read_root():
    return {"status": "running", "message": "FeelGym Server is Online"}

@app.get("/history", response_class=HTMLResponse)
def get_history():
    conn = sqlite3.connect("gym.db")
    cursor = conn.cursor()
    cursor.execute("SELECT count, timestamp FROM gym_logs ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    html = "<html><head><meta name='viewport' content='width=device-width, initial-scale=1'></head>"
    html += "<body style='text-align:center; font-family:sans-serif;'><h2>📊 전체 혼잡도 기록</h2><table border='1' style='margin:auto; width:90%; border-collapse:collapse;'>"
    html += "<tr style='background:#f4f4f9;'><th>시간</th><th>인원</th><th>상태</th></tr>"
    for row in rows:
        html += f"<tr><td>{row[1]}</td><td>{row[0]}명</td><td>{judge_status(row[0])}</td></tr>"
    html += "</table><br><a href='/admin'>관리자 페이지로</a></body></html>"
    return html

# 4. 카카오톡 챗봇 응답 API
@app.post("/kakao")
async def kakao_bot():
    conn = sqlite3.connect("gym.db")
    cursor = conn.cursor()
    cursor.execute("SELECT count FROM gym_logs ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if row:
        count = row[0]
        msg = f"현재 필짐 공릉점 인원은 약 {count}명이며, [{judge_status(count)}] 상태입니다! 오늘도 득근하세요! 💪"
    else:
        msg = "아직 기록된 혼잡도 정보가 없습니다."
    
    return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": msg}}]}}

# --- 관리자 섹션 (보안 및 버튼식 UI) ---
ADMIN_PASSWORD = "1234"

@app.get("/admin", response_class=HTMLResponse)
async def admin_login_page():
    return """
    <html>
    <head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
    <body style="text-align:center; padding-top:100px; font-family:sans-serif; background:#f0f2f5;">
        <div style="display:inline-block; background:white; padding:40px; border-radius:20px; shadow:0 10px 25px rgba(0,0,0,0.1);">
            <h2>🔐 필짐 관리자</h2>
            <form action="/admin/dashboard" method="post">
                <input type="password" name="password" placeholder="비밀번호" style="padding:15px; width:200px; border-radius:10px; border:1px solid #ddd;" required autofocus><br><br>
                <button type="submit" style="padding:15px 30px; background:#007bff; color:white; border:none; border-radius:10px; cursor:pointer;">접속하기</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.post("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(password: str = Form(...)):
    if password != ADMIN_PASSWORD:
        return HTMLResponse("<script>alert('비밀번호가 틀렸습니다!'); history.back();</script>")
    
    buttons_html = "".join([f'<button onclick="updateCount({c})" style="padding:20px; font-size:18px; font-weight:bold; border:none; border-radius:15px; background:#212529; color:white; cursor:pointer;">약 {c}명</button>' for c in [5, 10, 15, 20, 25, 30, 35, 40]])

    return f"""
    <html>
    <head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
    <body style="text-align:center; padding:20px; font-family:sans-serif; background:#f8f9fa;">
        <div style="background:white; padding:30px 20px; border-radius:25px; max-width:500px; margin:auto; box-shadow:0 10px 30px rgba(0,0,0,0.05);">
            <h2>🏋️‍♂️ 혼잡도 업데이트</h2>
            <p style="background:#f1f3f5; padding:15px; border-radius:15px; font-size:14px;">🟢 ~20명: 여유 | 🟡 ~30명: 보통 | 🔴 31명~: 붐빔</p>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">{buttons_html}</div>
            <br><a href="/history" style="color:#868e96; text-decoration:none; font-size:14px;">📊 전체 기록 보기</a>
        </div>
        <script>
            function updateCount(c) {{
                if(confirm("현재 인원을 '약 " + c + "명'으로 업데이트할까요?")) {{
                    fetch("/admin/quick-update?count=" + c, {{ method: "POST" }})
                    .then(res => res.json())
                    .then(data => alert("✅ 저장 완료! 챗봇에 즉시 반영되었습니다."));
                }}
            }}
        </script>
    </body>
    </html>
    """

@app.post("/admin/quick-update")
async def quick_update(count: int):
    kst_now = get_kst_now()
    conn = sqlite3.connect("gym.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO gym_logs (count, timestamp) VALUES (?, ?)", (count, kst_now))
    conn.commit()
    conn.close()
    return {"status": "success", "count": count}