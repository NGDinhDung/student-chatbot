# File: backend/app.py (ĐÃ CÓ CHỨC NĂNG ĐĂNG NHẬP & CÁ NHÂN HÓA)

import os
import sqlite3
import json
import re
from flask import Flask, request, jsonify, render_template, url_for
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
DATABASE = 'backend/chatbot.db'

# Cập nhật danh sách Intent để khớp với DB mới
FAQ_INTENTS = {
    "HOI_HOC_PHAN": "Hỏi về học phần, tín chỉ.",
    "HOI_LICH_THI": "Hỏi về lịch thi.",
    "HOI_LICH_HOC": "Hỏi về thời khóa biểu.",
    "HOI_HOC_PHI": "Hỏi về học phí, cách đóng tiền.",
    "HOI_TOT_NGHIEP": "Hỏi về điều kiện tốt nghiệp."
}

if not api_key:
    raise ValueError("Thiếu GEMINI_API_KEY.")

client = genai.Client(api_key=api_key)
app = Flask(__name__)

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row 
    return conn

def save_message(user_id, role, message):
    conn = get_db()
    conn.execute("INSERT INTO conversations (user_id, role, message) VALUES (?, ?, ?)", (user_id, role, message))
    conn.commit()
    conn.close()

def get_history(user_id, limit=5):
    conn = get_db()
    messages = conn.execute("SELECT role, message FROM conversations WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?", (user_id, limit)).fetchall()
    conn.close()
    messages.reverse() 
    history = []
    for row in messages:
        role = 'user' if row['role'] == 'user' else 'model'
        history.append({"role": role, "text": row['message']})
    return history

# --- 1. CHỨC NĂNG ĐĂNG NHẬP (MỚI) ---
@app.route("/login", methods=["GET"])
def login_page():
    """Trả về trang đăng nhập."""
    return render_template("login.html")

@app.post("/api/login")
def login_api():
    """Xử lý đăng nhập bằng MSSV hoặc Email."""
    data = request.get_json()
    identifier = data.get("identifier") # Có thể là MSSV hoặc Email

    if not identifier:
        return jsonify({"success": False, "message": "Vui lòng nhập MSSV hoặc Email."}), 400

    conn = get_db()
    # Tìm kiếm trong bảng users
    user = conn.execute(
        "SELECT * FROM users WHERE mssv = ? OR email = ?", 
        (identifier, identifier)
    ).fetchone()
    conn.close()

    if user:
        return jsonify({
            "success": True, 
            "user": {
                "mssv": user["mssv"],
                "name": user["name"],
                "email": user["email"]
            }
        })
    else:
        return jsonify({"success": False, "message": "Thông tin không tồn tại trong hệ thống."}), 401

# --- 2. TRA CỨU CÁ NHÂN HÓA (MỚI) ---
def get_personal_info(mssv, question):
    """
    Nếu người dùng hỏi về 'của tôi', 'của em', 'thời khóa biểu', 
    hàm này sẽ tra cứu dữ liệu riêng của MSSV đó.
    """
    question_lower = question.lower()
    
    # Logic tra cứu Thời khóa biểu cá nhân
    if "thời khóa biểu" in question_lower or "lịch học" in question_lower:
        conn = get_db()
        row = conn.execute("SELECT * FROM schedules WHERE mssv = ?", (mssv,)).fetchone()
        conn.close()
        if row:
            return f"Thời khóa biểu cá nhân của {row['student_name']} ({mssv}): {row['schedule_info']}"
        else:
            return "Hiện tại chưa có dữ liệu thời khóa biểu cho tài khoản của bạn."
            
    return None

# --- 3. LOGIC FAQ & GEMINI (Đã tối ưu) ---
def get_faq_answer(question):
    # (Giữ nguyên logic cũ, chỉ rút gọn cho ngắn gọn ở đây)
    # ... (Code xử lý intent giống phiên bản trước) ...
    tool_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "intent": types.Schema(type=types.Type.STRING, description="Intent ID"),
            "keyword": types.Schema(type=types.Type.STRING, description="Keyword")
        },
        required=["intent"]
    )
    system_prompt = f"Phân loại câu hỏi UTH. Intents: {', '.join(FAQ_INTENTS.keys())}. Nếu không khớp: 'CHUNG'."
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[types.Content(role="user", parts=[types.Part(text=question)])],
            config=types.GenerateContentConfig(system_instruction=system_prompt, response_mime_type="application/json", response_schema=tool_schema, temperature=0.0)
        )
        json_data = json.loads(response.text)
        intent = json_data.get('intent', 'CHUNG')
        
        if intent in FAQ_INTENTS:
            conn = get_db()
            row = conn.execute("SELECT answer FROM faq WHERE intent_category = ?", (intent,)).fetchone()
            conn.close()
            if row: return row['answer']
    except: pass
    return None

def ask_gemini(question, history, user_info=None):
    """Hỏi Gemini với ngữ cảnh người dùng."""
    user_context = ""
    if user_info:
        user_context = f"Người dùng hiện tại: {user_info['name']} (MSSV: {user_info['mssv']}). "

    system_prompt = f"{user_context}Bạn là trợ lý ảo của Trường Đại học Giao thông Vận tải (UTH). Hãy trả lời thân thiện, chính xác."
    
    try:
        config = types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.7)
        gemini_history = []
        if history:
            for item in history:
                gemini_history.append(types.Content(role=item['role'], parts=[types.Part(text=item['text'])]))
        
        chat = client.chats.create(model="gemini-2.5-flash", history=gemini_history, config=config)
        response = chat.send_message(question)
        return response.text
    except Exception as e:
        return "Hệ thống AI đang bận."

# --- ENDPOINTS ---
@app.route("/")
def index():
    return render_template("chat.html")

@app.route("/history")
def history():
    user_id = request.args.get("user_id")
    if not user_id: return jsonify({"history": []})
    
    messages = get_history(user_id, limit=20) 
    history_list = [{"role": item['role'], "message": item['text']} for item in messages]
    return jsonify({"history": history_list})

@app.post("/chat")
def chat():
    try:
        data = request.get_json()
        user_id = data.get("user_id") 
        user_name = data.get("user_name", "Bạn")
        question = data.get("message")

        if not user_id or not question:
            return jsonify({"error": "Thiếu thông tin người dùng hoặc tin nhắn"}), 400

        # LOGIC HYBRID NÂNG CAO
        answer = None
        
        # 1. Tra cứu thông tin cá nhân (TKB của CHÍNH MÌNH)
        answer = get_personal_info(user_id, question)
        
        # 2. Nếu không phải hỏi cá nhân, tìm trong FAQ
        if not answer:
            answer = get_faq_answer(question)
            
        # 3. Cuối cùng hỏi Gemini
        if not answer:
            history = get_history(user_id, limit=5)
            answer = ask_gemini(question, history, user_info={'mssv': user_id, 'name': user_name})
        
        save_message(user_id, 'user', question)
        save_message(user_id, 'assistant', answer)

        return jsonify({"answer": answer})

    except Exception as e:
        print(e)
        return jsonify({"error": "Lỗi server"}), 500

@app.post("/feedback")
def feedback():
    return jsonify({"status": "success"})

if __name__ == "__main__":
    app.run(debug=True)