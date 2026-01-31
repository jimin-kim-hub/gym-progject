from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine, text, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os

app = FastAPI()

# --- 1. 환경 설정 ---
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

# --- 2. 유틸리티 ---
def get_kst_now():
    return (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S")

# --- 3. 메인 선택 화면 (디자인 강화) ---
@app.get("/", response_class=HTMLResponse)
def main_selection():
    buttons = "".join([
        f'<button onclick="location.href=\'/admin/{name}\'" style="padding:20px; width:250px; margin:10px; font-size:18px; font-weight:bold; border-radius:15px; border:none; background:white; color:#333; cursor:pointer; box-shadow:0 4px 10px rgba(0,0,0,0.05); transition:0.2s;">🏢 {name} 관리자 접속</button><br>'
        for name in GYM_CONFIG.keys()
    ])
    return f"""
    <html><body style="text-align:center; padding-top:80px; font-family:sans-serif; background:#f0f2f5; color:#333;">
        <h1 style="margin-bottom:10px;">🏋️ 필짐 통합 관리 도구</h1>
        <p style="color:#666; margin-bottom:40px;">관리하실 지점을 선택해 주세요.</p>
        {buttons}
        <br><br><a href="/history" style="color:#007bff; text-decoration:none; font-size:14px;">📊 전체 통합 기록 보기</a>
    </body></html>
    """

# --- 4. 지점별 로그인 페이지 ---
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
            <br><a href="/" style="font-size:12px; color:#888;">지점 다시 선택하기</a>
        </div>
    </body></html>
    """

# --- 5. 지점별 대시보드 (기존 예쁜 디자인 복구!) ---
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
        <title>{gym_name} 관리자</title>
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
                <a href="/history?gym_name={gym_name}" style="font-size: 14px; color: #007bff; text-decoration: none;">📊 {gym_name} 기록 보기</a>
                
                <form action="/admin/reset" method="post" onsubmit="return confirm('정말 {gym_name}의 기록만 삭제하시겠습니까?');" style="margin-top:30px;">
                    <input type="hidden" name="gym_name" value="{gym_name}">
                    <input type="hidden" name="password" value="{password}">
                    <button type="submit" style="background:none; border:none; color:#dc3545; font-size:12px; cursor:pointer; text-decoration:underline;">지점 데이터 초기화</button>
                </form>
            </div>
            <div id="result-screen">
                <div class="success-icon">✅</div>
                <h2>저장 완료!</h2>
                <p style="color: #888; font-size: 15px;">Supabase에 안전하게 기록되었습니다.</p>
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
                }} catch (error) {{
                    alert("서버 연결 실패");
                }}
            }}
        </script>
    </body></html>
    """

# --- 6. 데이터 저장 및 초기화 API ---
@app.post("/admin/update")
async def update_count(gym_name: str, count: int):
    db = SessionLocal()
    try:
        new_log = GymLog(gym_name=gym_name, count=count, timestamp=get_kst_now())
        db.add(new_log)
        db.commit()
    finally:
        db.close()
    return {"status": "success"}

@app.post("/admin/reset")
async def reset_history(gym_name: str = Form(...), password: str = Form(...)):
    if GYM_CONFIG.get(gym_name, {}).get("pw") != password:
        return "권한이 없습니다."
    db = SessionLocal()
    try:
        # 해당 지점의 데이터만 삭제
        db.execute(text(f"DELETE FROM gym_logs WHERE gym_name = :name"), {{"name": gym_name}})
        db.commit()
    finally:
        db.close()
    return HTMLResponse(f"<script>alert('{gym_name} 기록이 초기화되었습니다.'); location.href='/';</script>")

# --- 7. 조회 페이지 ---
@app.get("/history", response_class=HTMLResponse)
def get_history(gym_name: str = None):
    db = SessionLocal()
    query = db.query(GymLog)
    if gym_name:
        query = query.filter(GymLog.gym_name == gym_name)
    logs = query.order_by(GymLog.id.desc()).limit(50).all()
    db.close()
    
    rows = "".join([f"<tr><td>{l.gym_name}</td><td>{l.timestamp}</td><td>{l.count}명</td></tr>" for l in logs])
    title = f"📊 {gym_name} 기록" if gym_name else "📊 전체 통합 기록"
    return f"""
    <html><body style="text-align:center; font-family:sans-serif; padding:20px;">
        <h2>{title}</h2>
        <table border="1" style="margin:auto; width:90%; border-collapse:collapse; border:1px solid #eee;">
            <tr style="background:#f4f4f9;"><th>지점</th><th>시간</th><th>인원</th></tr>
            {rows}
        </table><br>
        <a href="/" style="text-decoration:none; color:#007bff;">홈으로 돌아가기</a>
    </body></html>
    """