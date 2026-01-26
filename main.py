from fastapi import FastAPI, Request, Form
from fastapi.responses import FileResponse,HTMLResponse  # HTMLResponse 추가
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
# 모든 기록 조회 페이지
@app.get("/history")
def get_history():
    conn = sqlite3.connect("gym.db")
    cursor = conn.cursor()
    # 최신순으로 모든 기록 가져오기
    cursor.execute("SELECT count, timestamp FROM gym_logs ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    # 간단한 HTML 표로 만들기
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
            tr:nth-child(even) { background-color: #f9f9f9; }
        </style>
    </head>
    <body>
        <h2>📊 전체 혼잡도 기록</h2>
        <table>
            <tr><th>시간</th><th>인원수</th><th>상태</th></tr>
    """
    
    for row in rows:
        status = judge_status(row[0])
        html_content += f"<tr><td>{row[1]}</td><td>{row[0]}명</td><td>{status}</td></tr>"
    
    html_content += "</table><br><a href='/'>입력 화면으로 돌아가기</a></body></html>"
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)
# 카카오톡 챗봇 전용 응답 API
@app.post("/kakao")
async def kakao_bot():
    conn = sqlite3.connect("gym.db")
    cursor = conn.cursor()
    cursor.execute("SELECT count FROM gym_logs ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if row:
        count = row[0]
        status = judge_status(count)
        msg = f"현재 필짐 공릉점 인원은 약 {count}명이며, [{status}] 상태입니다! 오늘도 득근하세요! 💪"
    else:
        msg = "아직 기록된 혼잡도 정보가 없습니다."

    # 카카오톡이 요구하는 형식(JSON)으로 응답
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": msg
                    }
                }
            ]
        }
    }
# 1. 관리자 전용 비밀번호 설정 (원하시는 대로 바꾸세요)
ADMIN_PASSWORD = "1234"

# 2. 관리자 로그인 및 입력 페이지
@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    # 트레이너가 접속하면 보게 될 화면입니다.
    return """
    <html>
    <head>
        <title>필짐 관리자 전용</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: sans-serif; text-align: center; padding: 50px 20px; background-color: #f4f4f9; }
            .card { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
            button { width: 100%; padding: 12px; background-color: #28a745; color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>🔐 필짐 관리자 전용</h2>
            <p>비밀번호와 현재 인원을 입력하세요.</p>
            <form action="/admin/update" method="post">
                <input type="password" name="password" placeholder="비밀번호 4자리" required>
                <input type="number" name="count" placeholder="현재 인원 (숫자만)" required>
                <button type="submit">인원수 업데이트</button>
            </form>
            <br>
            <a href="/history" style="color: #666; font-size: 14px;">기록 보기</a>
        </div>
    </body>
    </html>
    """

# 3. 비밀번호 확인 후 데이터 저장 처리
@app.post("/admin/update")
async def admin_update(password: str = Form(...), count: int = Form(...)):
    if password != ADMIN_PASSWORD:
        return HTMLResponse(content="<script>alert('비밀번호가 틀렸습니다!'); history.back();</script>")
    
    # 비밀번호가 맞으면 기존 update 로직을 실행합니다.
    kst_now = get_kst_now()
    conn = sqlite3.connect("gym.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO gym_logs (count, timestamp) VALUES (?, ?)", (count, kst_now))
    conn.commit()
    conn.close()
    
    return HTMLResponse(content=f"<script>alert('{count}명으로 업데이트 되었습니다!'); location.href='/admin';</script>")