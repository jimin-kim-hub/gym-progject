from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine, text, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os

app = FastAPI()

# --- 1. 환경 설정 (이름만 바꾸면 바로 적용됩니다!) ---
GYM_CONFIG = {
    "헬스장1": {"pw": "1111"},
    "헬스장2": {"pw": "2222"},
    "헬스장3": {"pw": "3333"}
}

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 테이블 정의 (gym_name 추가)
class GymLog(Base):
    __tablename__ = "gym_logs"
    id = Column(Integer, primary_key=True, index=True)
    gym_name = Column(String)  # 어느 헬스장인지 저장
    count = Column(Integer)
    timestamp = Column(String)

Base.metadata.create_all(bind=engine)

# --- 2. 유틸리티 ---
def get_kst_now():
    return (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S")

# --- 3. 메인 화면 (지점 선택 페이지) ---
@app.get("/", response_class=HTMLResponse)
def main_selection():
    buttons = "".join([
        f'<button onclick="location.href=\'/admin/{name}\'" style="padding:20px; width:200px; margin:10px; font-size:18px; border-radius:10px; border:none; background:#007bff; color:white; cursor:pointer;">{name} 관리</button><br>'
        for name in GYM_CONFIG.keys()
    ])
    return f"""
    <html><body style="text-align:center; padding-top:50px; font-family:sans-serif; background:#f0f2f5;">
        <h2>🏋️ 필짐 통합 관리 시스템</h2>
        <p>관리할 헬스장을 선택해주세요.</p>
        {buttons}
        <br><a href="/history" style="color:#888; text-decoration:none;">전체 기록 보기</a>
    </body></html>
    """

# --- 4. 지점별 로그인 페이지 ---
@app.get("/admin/{gym_name}", response_class=HTMLResponse)
async def admin_login(gym_name: str):
    if gym_name not in GYM_CONFIG:
        return "존재하지 않는 지점입니다."
    return f"""
    <html><body style="text-align:center; padding-top:100px; font-family:sans-serif;">
        <h2>🔐 {gym_name} 로그인</h2>
        <form action="/admin/dashboard" method="post">
            <input type="hidden" name="gym_name" value="{gym_name}">
            <input type="password" name="password" placeholder="비밀번호" style="padding:15px; border-radius:10px; border:1px solid #ddd;" required autofocus><br><br>
            <button type="submit" style="padding:15px 30px; background:#28a745; color:white; border:none; border-radius:10px;">접속</button>
        </form>
    </body></html>
    """

# --- 5. 지점별 대시보드 (입력 화면) ---
@app.post("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(gym_name: str = Form(...), password: str = Form(...)):
    if GYM_CONFIG.get(gym_name, {}).get("pw") != password:
        return "<script>alert('비밀번호가 틀렸습니다!'); history.back();</script>"
    
    counts = [5, 10, 15, 20, 25, 30, 35, 40]
    btn_html = "".join([f'<button onclick="saveCount(\'{gym_name}\', {c})" style="padding:20px; font-size:18px; border-radius:10px; border:none; background:#f1f3f5; cursor:pointer;">{c}명</button>' for c in counts])

    return f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
    <body style="text-align:center; font-family:sans-serif; padding:20px;">
        <h2>🏢 {gym_name} 혼잡도 입력</h2>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">{btn_html}</div>
        <script>
            async function saveCount(name, val) {{
                await fetch(`/admin/update?gym_name=${{name}}&count=${{val}}`, {{ method: 'POST' }});
                alert(name + ' ' + val + '명 저장 완료!');
                location.href = '/';
            }}
        </script>
    </body></html>
    """

# --- 6. 데이터 저장 API ---
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

# --- 7. 조회 페이지 (지점별 필터링) ---
@app.get("/history", response_class=HTMLResponse)
def get_history(gym_name: str = None):
    db = SessionLocal()
    query = db.query(GymLog)
    if gym_name:
        query = query.filter(GymLog.gym_name == gym_name)
    logs = query.order_by(GymLog.id.desc()).limit(50).all()
    db.close()
    
    rows = "".join([f"<tr><td>{l.gym_name}</td><td>{l.timestamp}</td><td>{l.count}명</td></tr>" for l in logs])
    return f"""
    <html><body style="text-align:center; font-family:sans-serif;">
        <h2>📊 데이터 기록</h2>
        <table border="1" style="margin:auto; width:90%; border-collapse:collapse;">
            <tr style="background:#eee;"><th>지점</th><th>시간</th><th>인원</th></tr>
            {rows}
        </table><br>
        <a href="/">홈으로 돌아가기</a>
    </body></html>
    """