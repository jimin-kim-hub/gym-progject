from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine, text, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os

app = FastAPI()

# --- 1. 데이터베이스 설정 (Supabase 연동) ---
# 지민님이 완성하신 무적의 주소입니다.
DATABASE_URL = "postgresql://postgres.ghnmnsaborthmiftdnsb:YY64RTzNQoUsoWik@aws-1-ap-northeast-2.pooler.supabase.com:6543/postgres?pgbouncer=true"

# SQLAlchemy 설정
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 테이블 구조 정의 (기존 SQLite 구조와 동일하게)
class GymLog(Base):
    __tablename__ = "gym_logs"
    id = Column(Integer, primary_key=True, index=True)
    count = Column(Integer)
    timestamp = Column(String) # 기존 코드와 호환성을 위해 String으로 유지

# DB 테이블 생성 (최초 1회 실행)
Base.metadata.create_all(bind=engine)

# --- 2. 유틸리티 함수 ---
def get_kst_now():
    return (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S")

def judge_status(count: int):
    if count <= 20: return "여유 (쾌적해요! 🏃‍♂️)"
    elif count <= 30: return "보통 (운동하기 적당해요. 🙂)"
    else: return "붐빔 (나중에 오시는 건 어떨까요? 😅)"

# --- 3. 메인 및 기록 확인 페이지 ---
@app.get("/")
def read_root():
    return {"status": "running", "message": "FeelGym Server with Supabase"}

@app.get("/history", response_class=HTMLResponse)
def get_history():
    db = SessionLocal()
    # 최신순으로 기록 가져오기
    logs = db.query(GymLog).order_by(GymLog.id.desc()).all()
    db.close()
    
    html = "<html><head><meta name='viewport' content='width=device-width, initial-scale=1'></head>"
    html += "<body style='text-align:center; font-family:sans-serif;'><h2>📊 전체 혼잡도 기록 (Supabase)</h2><table border='1' style='margin:auto; width:90%; border-collapse:collapse;'>"
    html += "<tr style='background:#f4f4f9;'><th>시간</th><th>인원</th><th>상태</th></tr>"
    for log in logs:
        html += f"<tr><td>{log.timestamp}</td><td>{log.count}명</td><td>{judge_status(log.count)}</td></tr>"
    html += "</table><br><a href='/admin'>관리자 페이지로</a></body></html>"
    return html

# 4. 카카오톡 챗봇 응답 API
@app.post("/kakao")
async def kakao_bot():
    db = SessionLocal()
    last_log = db.query(GymLog).order_by(GymLog.id.desc()).first()
    db.close()
    
    msg = f"현재 필짐 인원은 약 {last_log.count}명, [{judge_status(last_log.count)}] 상태입니다! 💪" if last_log else "기록이 없습니다."
    return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": msg}}]}}

# --- 5. 관리자 섹션 ---
ADMIN_PASSWORD = "1234"

@app.get("/admin", response_class=HTMLResponse)
async def admin_login_page():
    return """
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
    <body style="text-align:center; padding-top:100px; font-family:sans-serif; background:#f0f2f5;">
        <div style="display:inline-block; background:white; padding:40px; border-radius:20px; box-shadow:0 10px 25px rgba(0,0,0,0.1);">
            <h2>🔐 필짐 관리자 (DB 연동형)</h2>
            <form action="/admin/dashboard" method="post">
                <input type="password" name="password" placeholder="비밀번호" style="padding:15px; width:200px; border-radius:10px; border:1px solid #ddd;" required autofocus><br><br>
                <button type="submit" style="padding:15px 30px; background:#007bff; color:white; border:none; border-radius:10px; cursor:pointer;">접속하기</button>
            </form>
        </div>
    </body></html>
    """

@app.post("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(password: str = Form(...)):
    if password != ADMIN_PASSWORD:
        return HTMLResponse("<script>alert('비밀번호가 틀렸습니다!'); history.back();</script>")
    
    counts = [5, 10, 15, 20, 25, 30, 35, 40]
    buttons_html = "".join([f'<button class="count-btn" onclick="saveCount({c})">약 {c}명</button>' for c in counts])

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>필짐 공릉점 관리자</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: sans-serif; text-align: center; padding: 20px; background-color: #f8f9fa; color: #333; }}
            .container {{ background: white; padding: 25px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); max-width: 450px; margin: 0 auto; }}
            .info-table {{ width: 100%; border-collapse: collapse; margin-bottom: 25px; font-size: 14px; border-radius: 10px; overflow: hidden; border: 1px solid #eee; }}
            .info-table th {{ background: #eee; padding: 10px; }}
            .info-table td {{ padding: 10px; border-top: 1px solid #eee; }}
            .badge {{ padding: 3px 8px; border-radius: 5px; font-weight: bold; }}
            .low {{ background: #d4edda; color: #155724; }}
            .mid {{ background: #fff3cd; color: #856404; }}
            .high {{ background: #f8d7da; color: #721c24; }}
            .btn-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px; }}
            .count-btn {{ padding: 20px; font-size: 17px; font-weight: bold; border: none; border-radius: 12px; background: #f1f3f5; cursor: pointer; transition: 0.2s; color: #495057; }}
            .count-btn:active {{ transform: scale(0.95); background: #e9ecef; }}
            #result-screen {{ display: none; padding: 40px 0; }}
            .success-icon {{ font-size: 60px; margin-bottom: 20px; }}
            .back-btn {{ margin-top: 20px; background: none; border: 1px solid #adb5bd; color: #495057; padding: 10px 20px; border-radius: 8px; cursor: pointer; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div id="main-screen">
                <h2 style="margin-bottom: 10px;">🏋️ 필짐 혼잡도 입력</h2>
                <table class="info-table">
                    <thead><tr><th>구분</th><th>인원 기준</th></tr></thead>
                    <tbody>
                        <tr><td><span class="badge low">여유</span></td><td>20명 이하</td></tr>
                        <tr><td><span class="badge mid">보통</span></td><td>21명 ~ 30명</td></tr>
                        <tr><td><span class="badge high">혼잡</span></td><td>31명 이상</td></tr>
                    </tbody>
                </table>
                <div class="btn-grid">{buttons_html}</div>
                <a href="/history" style="font-size: 14px; color: #007bff; text-decoration: none;">📊 전체 기록 보기</a>
                
                <form action="/admin/reset" method="post" onsubmit="return confirm('정말 모든 기록을 삭제하시겠습니까?');" style="margin-top:30px;">
                    <input type="hidden" name="password" value="{ADMIN_PASSWORD}">
                    <button type="submit" style="background:none; border:none; color:#dc3545; font-size:12px; cursor:pointer; text-decoration:underline;">데이터 초기화</button>
                </form>
            </div>
            <div id="result-screen">
                <div class="success-icon">✅</div>
                <h2>저장 완료!</h2>
                <p id="time-text" style="color: #888; font-size: 15px;"></p>
                <button class="back-btn" onclick="location.reload()">돌아가기</button>
            </div>
        </div>
        <script>
            async function saveCount(val) {{
                try {{
                    const response = await fetch(`/admin/quick-update?count=${{val}}`, {{ method: "POST" }});
                    const data = await response.json();
                    document.getElementById('main-screen').style.display = 'none';
                    document.getElementById('result-screen').style.display = 'block';
                    document.getElementById('time-text').innerText = "방금 전 Supabase에 저장됨";
                }} catch (error) {{
                    alert("서버 연결에 실패했습니다.");
                }}
            }}
        </script>
    </body></html>
    """

@app.post("/admin/quick-update")
async def quick_update(count: int):
    kst_now = get_kst_now()
    db = SessionLocal()
    new_log = GymLog(count=count, timestamp=kst_now)
    db.add(new_log)
    db.commit()
    db.close()
    return {"status": "success", "count": count}

@app.post("/admin/reset")
async def reset_history(password: str = Form(...)):
    if password != ADMIN_PASSWORD:
        return HTMLResponse("<script>alert('권한이 없습니다.'); history.back();</script>")
    db = SessionLocal()
    db.execute(text("DELETE FROM gym_logs"))
    db.commit()
    db.close()
    return HTMLResponse("<script>alert('기록이 초기화되었습니다.'); location.href='/admin';</script>")