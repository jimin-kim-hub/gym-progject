from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine, text, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os

app = FastAPI()

# --- 1. 환경 설정 (지점 추가/수정은 여기서!) ---
GYM_CONFIG = {
    "헬스장1": {"pw": "1111"},
    "헬스장2": {"pw": "2222"},
    "헬스장3": {"pw": "3333"}
}

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class GymLog(Base):
    __tablename__ = "gym_logs"
    id = Column(Integer, primary_key=True, index=True)
    gym_name = Column(String)
    count = Column(Integer)
    timestamp = Column(String)

Base.metadata.create_all(bind=engine)

def get_kst_now():
    return (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S")

# --- 2. 메인 화면 (제목 수정 완료!) ---
@app.get("/", response_class=HTMLResponse)
def main_selection():
    buttons = "".join([
        f'<button onclick="location.href=\'/admin/{name}\'" style="padding:20px; width:280px; margin:10px; font-size:18px; font-weight:bold; border-radius:15px; border:none; background:white; color:#333; cursor:pointer; box-shadow:0 4px 10px rgba(0,0,0,0.05);">🏢 {name} 인원 등록</button><br>'
        for name in GYM_CONFIG.keys()
    ])
    return f"""
    <html><body style="text-align:center; padding-top:80px; font-family:sans-serif; background:#f0f2f5; color:#333;">
        <h1 style="margin-bottom:10px;">📊 헬스장 실시간 인원 등록</h1>
        <p style="color:#666; margin-bottom:40px;">등록할 지점을 선택해 주세요.</p>
        {buttons}
        <br><br><a href="/history" style="color:#007bff; text-decoration:none; font-size:14px;">📊 전체 통합 기록 보기</a>
    </body></html>
    """

# --- 3. 지점별 로그인 ---
@app.get("/admin/{gym_name}", response_class=HTMLResponse)
async def admin_login(gym_name: str):
    return f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
    <body style="text-align:center; padding-top:100px; font-family:sans-serif; background:#f0f2f5;">
        <div style="display:inline-block; background:white; padding:40px; border-radius:20px; box-shadow:0 10px 25px rgba(0,0,0,0.1);">
            <h2>🔐 {gym_name} 접속</h2>
            <form action="/admin/dashboard" method="post">
                <input type="hidden" name="gym_name" value="{gym_name}">
                <input type="password" name="password" placeholder="비밀번호" style="padding:15px; width:200px; border-radius:10px; border:1px solid #ddd;" required autofocus><br><br>
                <button type="submit" style="padding:15px 30px; background:#007bff; color:white; border:none; border-radius:10px; cursor:pointer; font-weight:bold;">관리자 모드 시작</button>
            </form>
            <br><a href="/" style="font-size:12px; color:#888;">홈으로 돌아가기</a>
        </div>
    </body></html>
    """

# --- 4. 지점별 대시보드 ---
@app.post("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(gym_name: str = Form(...), password: str = Form(...)):
    if GYM_CONFIG.get(gym_name, {}).get("pw") != password:
        return "<script>alert('비밀번호가 틀렸습니다!'); history.back();</script>"
    
    counts = [5, 10, 15, 20, 25, 30, 35, 40]
    buttons_html = "".join([f'<button class="count-btn" onclick="saveCount(\'{gym_name}\', {c})">약 {c}명</button>' for c in counts])

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{gym_name} 인원 등록</title>
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
            .nav-link {{ display: block; margin-top: 20px; font-size: 14px; color: #007bff; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div id="main-screen">
                <h2 style="margin-bottom: 10px;">🏋️ {gym_name} 혼잡도 입력</h2>
                <table class="info-table">
                    <thead><tr><th>구분</th><th>인원 기준</th></tr></thead>
                    <tbody>
                        <tr><td><span class="badge low">여유</span></td><td>20명 이하</td></tr>
                        <tr><td><span class="badge mid">보통</span></td><td>21명 ~ 30명</td></tr>
                        <tr><td><span class="badge high">혼잡</span></td><td>31명 이상</td></tr>
                    </tbody>
                </table>
                <div class="btn-grid">{buttons_html}</div>
                <a class="nav-link" href="/history?gym_name={gym_name}">📊 {gym_name} 기록 보기</a>
                
                <form action="/admin/reset" method="post" onsubmit="return confirm('기록을 삭제하시겠습니까?');" style="margin-top:20px;">
                    <input type="hidden" name="gym_name" value="{gym_name}">
                    <input type="hidden" name="password" value="{password}">
                    <button type="submit" style="background:none; border:none; color:#dc3545; font-size:12px; cursor:pointer; text-decoration:underline;">데이터 초기화</button>
                </form>
                
                <hr style="margin-top:20px; border:0; border-top:1px solid #eee;">
                <a class="nav-link" href="/" style="color: #6c757d;">🏠 홈으로 (지점 선택)</a>
            </div>
            <div id="result-screen">
                <div class="success-icon">✅</div>
                <h2>저장 완료!</h2>
                <button class="back-btn" onclick="location.reload()">돌아가기</button>
            </div>
        </div>
        <script>
            async function saveCount(name, val) {{
                try {{
                    const response = await fetch(`/admin/update?gym_name=${{name}}&count=${{val}}`, {{ method: "POST" }});
                    if(response.ok) {{
                        document.getElementById('main-screen').style.display = 'none';
                        document.getElementById('result-screen').style.display = 'block';
                    }}
                }} catch (error) {{ alert("연결 실패"); }}
            }}
        </script>
    </body></html>
    """

# --- 이하 저장/조회 로직 동일 ---
@app.post("/admin/update")
async def update_count(gym_name: str, count: int):
    db = SessionLocal(); new_log = GymLog(gym_name=gym_name, count=count, timestamp=get_kst_now())
    db.add(new_log); db.commit(); db.close()
    return {"status": "success"}

@app.post("/admin/reset")
async def reset_history(gym_name: str = Form(...), password: str = Form(...)):
    if GYM_CONFIG.get(gym_name, {}).get("pw") != password: return "권한 없음"
    db = SessionLocal(); db.execute(text(f"DELETE FROM gym_logs WHERE gym_name = :name"), {{"name": gym_name}})
    db.commit(); db.close()
    return HTMLResponse(f"<script>alert('{gym_name} 초기화 완료'); location.href='/';</script>")

@app.get("/history", response_class=HTMLResponse)
def get_history(gym_name: str = None):
    db = SessionLocal(); query = db.query(GymLog)
    if gym_name: query = query.filter(GymLog.gym_name == gym_name)
    logs = query.order_by(GymLog.id.desc()).limit(50).all(); db.close()
    rows = "".join([f"<tr><td>{l.gym_name}</td><td>{l.timestamp}</td><td>{l.count}명</td></tr>" for l in logs])
    return f"<html><body style='text-align:center; padding:20px; font-family:sans-serif;'><h2>📊 기록</h2><table border='1' style='margin:auto; width:90%; border-collapse:collapse;'>{rows}</table><br><a href='/'>홈으로</a></body></html>"

# --- 카카오 챗봇 전용 응답 API (지점별 구분 로직 포함) ---
@app.post("/kakao")
async def kakao_bot(request: Request):
    # 카카오 설정창 URL 뒤에 붙인 ?gym_name=헬스장1 정보를 읽어옵니다.
    params = request.query_params
    gym_name = params.get("gym_name", "헬스장1") # 기본값은 헬스장1
    
    db = SessionLocal()
    try:
        # 데이터베이스에서 요청받은 '해당 지점'의 가장 최신 기록만 가져옵니다.
        last_log = db.query(GymLog).filter(GymLog.gym_name == gym_name).order_by(GymLog.id.desc()).first()
    finally:
        db.close()
    
    if last_log:
        msg = f"현재 [{last_log.gym_name}] 이용 인원은 약 {last_log.count}명입니다! 💪"
    else:
        msg = f"[{gym_name}]의 등록된 인원 정보가 없습니다."
        
    return {
        "version": "2.0",
        "template": {
            "outputs": [{"simpleText": {"text": msg}}]
        }
    }