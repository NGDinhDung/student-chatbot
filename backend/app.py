import os
import sqlite3
import json
import difflib
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify, render_template
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- CẤU HÌNH ---
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super_secret_key")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "chatbot.db")
api_key = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-1.5-flash"
client = genai.Client(api_key=api_key) if api_key else None

# --- DATABASE ---
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Tạo các bảng cần thiết
    tables = [
        '''CREATE TABLE IF NOT EXISTS users (mssv TEXT PRIMARY KEY, name TEXT, email TEXT, major TEXT)''',
        '''CREATE TABLE IF NOT EXISTS chat_sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, title TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''',
        '''CREATE TABLE IF NOT EXISTS conversations (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER, user_id TEXT, role TEXT, message TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''',
        '''CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, message TEXT, created_at TEXT)''',
        '''CREATE TABLE IF NOT EXISTS faq (id INTEGER PRIMARY KEY AUTOINCREMENT, question TEXT, answer TEXT)''',
        '''CREATE TABLE IF NOT EXISTS schedules (mssv TEXT PRIMARY KEY, student_name TEXT, schedule_info TEXT)'''
    ]
    for table in tables: c.execute(table)
    conn.commit(); conn.close()

def seed_faq_data():
    """Nạp dữ liệu FAQ chuẩn"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    sample_data = [
        ("xem thông tin sinh viên ở đâu", "Để xem thông tin sinh viên: Bạn vào https://portal.ut.edu.vn/ -> Đăng nhập -> Chọn mục 'Thông tin cá nhân'."),
        ("xem thời khóa biểu ở đâu", "Để xem TKB: Bạn vào https://portal.ut.edu.vn/ -> Đăng nhập -> Chọn mục 'Thời khóa biểu'."),
        ("khi nào tôi được nghỉ tết", "Theo lịch nghỉ Tết 2025: Sinh viên được nghỉ từ 20/01 đến hết 09/02/2025 (3 tuần)."),
        ("đóng học phí ở đâu", "Bạn đóng học phí trực tuyến tại trang: https://payment.ut.edu.vn/"),
        ("quên mật khẩu portal", "Nếu quên mật khẩu Portal, hãy dùng chức năng 'Quên mật khẩu' trên web hoặc liên hệ Phòng Công tác Sinh viên.")
    ]
    try:
        c.execute("SELECT count(*) FROM faq")
        if c.fetchone()[0] == 0:
            c.executemany("INSERT INTO faq (question, answer) VALUES (?, ?)", sample_data)
            conn.commit()
            print(">>> Đã nạp dữ liệu mẫu FAQ!")
    except: pass
    conn.close()

init_db()
seed_faq_data()

# --- HELPER: CRAWL WEB TRƯỜNG ---
def crawl_ut_news():
    """Hàm này đi đọc báo dùm sinh viên"""
    news_items = []
    try:
        url = "https://ut.edu.vn/chuyen-muc/thong-bao-14.html"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Lấy 10 tin mới nhất để AI có nhiều dữ liệu
            articles = soup.select('.list-news .item')[:8] 
            
            for article in articles:
                title_tag = article.select_one('a')
                date_tag = article.select_one('.date')
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    link = title_tag.get('href')
                    if link and not link.startswith('http'): link = 'https://ut.edu.vn' + link
                    date = date_tag.get_text(strip=True) if date_tag else ""
                    
                    news_items.append(f"- {title} ({date}) [Link: {link}]")
    except Exception as e:
        print(f"Lỗi Crawl: {e}")
    return "\n".join(news_items) # Trả về 1 đoạn văn bản dài chứa tất cả tin tức

# --- LOGIC CHAT THÔNG MINH ---
def get_faq_answer_fast(user_question):
    try:
        conn = get_db()
        rows = conn.execute("SELECT question, answer FROM faq").fetchall()
        conn.close()
        if not rows: return None
        db_questions = [row['question'] for row in rows]
        matches = difflib.get_close_matches(user_question.lower(), [q.lower() for q in db_questions], n=1, cutoff=0.65)
        if matches:
            for row in rows:
                if row['question'].lower() == matches[0]: return row['answer']
    except: pass
    return None

def ask_gemini(question, history, user_info, latest_news_context):
    if not client: return "Lỗi: Server chưa cấu hình API Key."

    # Đây là nơi chúng ta "mớm" tin tức cho AI
    system_instruction = f"""
    Bạn là Trợ lý ảo UTH.
    Người dùng: {user_info.get('name')} (MSSV: {user_info.get('mssv')}).
    
    DỮ LIỆU TIN TỨC MỚI NHẤT TỪ WEBSITE TRƯỜNG (Sử dụng thông tin này để trả lời nếu người dùng hỏi về thông báo/tin tức):
    --- BẮT ĐẦU TIN TỨC ---
    {latest_news_context}
    --- KẾT THÚC TIN TỨC ---

    QUY TẮC TRẢ LỜI:
    1. Nếu người dùng hỏi về thông báo, sự kiện, học phí mới nhất -> Hãy tra cứu trong phần "DỮ LIỆU TIN TỨC" ở trên và tóm tắt lại.
    2. Nếu có link trong tin tức, hãy đính kèm link cho người dùng bấm.
    3. Nếu không tìm thấy trong tin tức, hãy trả lời dựa trên kiến thức chung về UTH (Portal: portal.ut.edu.vn).
    4. Trả lời ngắn gọn, thân thiện.
    """
    
    try:
        config = types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.3)
        gemini_history = []
        for m in history:
            gemini_history.append(types.Content(role=m['role'], parts=[types.Part(text=m['text'])]))

        chat = client.chats.create(model=MODEL_NAME, history=gemini_history, config=config)
        response = chat.send_message(question)
        return response.text
    except: return "Hệ thống AI đang quá tải."

# --- ROUTES ---
@app.route("/")
def index(): return render_template("chat.html")

@app.route("/login")
def login_page(): return render_template("login.html")

@app.route("/register")
def register_page(): return render_template("register.html")

@app.post("/api/login")
def login_api():
    data = request.get_json()
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE mssv = ? OR email = ?", (data['identifier'], data['identifier'])).fetchone()
    conn.close()
    return jsonify({"success": True, "user": {"mssv": user["mssv"], "name": user["name"]}}) if user else (jsonify({"success": False}), 401)

@app.post("/api/register")
def register_api():
    try:
        d = request.get_json()
        conn = get_db()
        conn.execute("INSERT INTO users (mssv, name, email, major) VALUES (?, ?, ?, ?)", (d['mssv'], d['name'], d['email'], d['major']))
        conn.commit(); conn.close()
        return jsonify({"success": True})
    except: return jsonify({"success": False}), 409

@app.post("/chat")
def chat():
    try:
        d = request.get_json()
        uid, name, msg, sid = d.get("user_id"), d.get("user_name"), d.get("message"), d.get("session_id")
        
        if not sid: 
            conn = get_db(); c = conn.cursor()
            c.execute("INSERT INTO chat_sessions (user_id, title) VALUES (?, ?)", (uid, msg[:40]+"..."))
            sid = c.lastrowid; conn.commit(); conn.close()

        # 1. Tìm trong FAQ trước (Nhanh nhất)
        answer = get_faq_answer_fast(msg)
        
        # 2. Nếu không có trong FAQ -> Crawl tin tức -> Hỏi AI
        if not answer:
            # Lấy tin tức mới nhất từ web trường
            news_context = crawl_ut_news()
            
            # Lấy lịch sử chat
            history = []
            if sid:
                conn = get_db()
                rows = conn.execute("SELECT role, message FROM conversations WHERE session_id = ? ORDER BY timestamp ASC", (sid,)).fetchall()
                conn.close()
                history = [{"role": ('user' if r['role'] == 'user' else 'model'), "text": r['message']} for r in rows][-5:]
            
            # Gọi AI với "bộ não" đã được nạp tin tức
            answer = ask_gemini(msg, history, {'mssv': uid, 'name': name}, news_context)

        # Lưu tin nhắn
        conn = get_db()
        conn.execute("INSERT INTO conversations (session_id, user_id, role, message) VALUES (?, ?, ?, ?)", (sid, uid, 'user', msg))
        conn.execute("INSERT INTO conversations (session_id, user_id, role, message) VALUES (?, ?, ?, ?)", (sid, uid, 'assistant', answer))
        conn.commit(); conn.close()

        return jsonify({"answer": answer, "session_id": sid})
    except Exception as e:
        print(e)
        return jsonify({"error": "Lỗi server"}), 500

@app.get("/api/sessions")
def get_sessions():
    conn = get_db()
    rows = conn.execute("SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY created_at DESC", (request.args.get("user_id"),)).fetchall()
    conn.close()
    return jsonify({"sessions": [{"id": r["id"], "title": r["title"]} for r in rows]})

@app.get("/api/messages")
def get_messages():
    conn = get_db()
    rows = conn.execute("SELECT role, message FROM conversations WHERE session_id = ? ORDER BY timestamp ASC", (request.args.get("session_id"),)).fetchall()
    conn.close()
    return jsonify({"messages": [{"role": m['role'], "message": m['message']} for m in rows]})

@app.post("/api/delete_session")
def delete_session():
    d = request.get_json()
    conn = get_db()
    conn.execute("DELETE FROM conversations WHERE session_id = ?", (d['session_id'],))
    conn.execute("DELETE FROM chat_sessions WHERE id = ?", (d['session_id'],))
    conn.commit(); conn.close()
    return jsonify({"success": True})

@app.post('/feedback')
def feedback():
    d = request.json
    conn = get_db()
    conn.execute("INSERT INTO feedback (name, message, created_at) VALUES (?, ?, ?)", (d.get('name'), d.get('message'), datetime.now().strftime("%Y-%m-%d")))
    conn.commit(); conn.close()
    return jsonify({'status': 'success'})

# API riêng cho Frontend load tin tức bên Sidebar
@app.get("/api/news")
def get_latest_news_api():
    # Tái sử dụng hàm crawl, nhưng format lại thành JSON list cho frontend
    text_data = crawl_ut_news() # Dữ liệu dạng text
    # (Ở đây ta chấp nhận parse lại đơn giản hoặc chỉnh hàm crawl trả về list object sẽ tốt hơn)
    # Để code ngắn gọn, tôi giữ logic cũ cho API news frontend
    # ... (Code crawl API frontend giữ nguyên như phiên bản trước nếu bạn muốn, 
    # hoặc đơn giản hóa là gọi lại hàm crawl_ut_news rồi split text)
    
    # Để đảm bảo code chạy ngay, tôi viết lại đoạn này ngắn gọn:
    news_items = []
    try:
        url = "https://ut.edu.vn/chuyen-muc/thong-bao-14.html"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = soup.select('.list-news .item')[:5]
        for article in articles:
            t = article.select_one('a')
            d = article.select_one('.date')
            if t:
                link = t.get('href')
                if link and not link.startswith('http'): link = 'https://ut.edu.vn' + link
                news_items.append({"title": t.get_text(strip=True), "link": link, "desc": d.get_text(strip=True) if d else ""})
    except: pass
    if not news_items: news_items = [{"title": "Lịch thi học kỳ", "link": "https://portal.ut.edu.vn", "desc": "Xem trên Portal"}]
    return jsonify({"news": news_items})

if __name__ == "__main__":
    app.run(debug=True, port=5000)