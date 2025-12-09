# File: backend/app.py (PHIÊN BẢN HOÀN THIỆN, ĐÃ SỬA LỖI VALIDATION)

import os
import sqlite3
from flask import Flask, request, jsonify, render_template
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- CẤU HÌNH VÀ KHỞI TẠO ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
DATABASE = 'backend/chatbot.db'

if not api_key:
    raise ValueError("GEMINI_API_KEY không được tìm thấy. Hãy kiểm tra file .env.")

client = genai.Client(api_key=api_key)
app = Flask(__name__)

# --- HÀM HỖ TRỢ DATABASE ---

def get_db():
    """Tạo kết nối database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row 
    return conn

def save_message(user_id, role, message):
    """Lưu tin nhắn (user/assistant) vào database."""
    conn = get_db()
    conn.execute(
        "INSERT INTO conversations (user_id, role, message) VALUES (?, ?, ?)",
        (user_id, role, message)
    )
    conn.commit()
    conn.close()

# HÀM GET_HISTORY ĐÃ SỬA (Sử dụng key 'text')
def get_history(user_id, limit=5):
    """Lấy lịch sử hội thoại gần nhất và trả về định dạng list dictionary."""
    conn = get_db()
    messages = conn.execute(
        "SELECT role, message FROM conversations WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    conn.close()
    
    messages.reverse() 
    
    # TRẢ VỀ FORMAT ĐƠN GIẢN VỚI KEY 'text'
    history = []
    for row in messages:
        role = 'user' if row['role'] == 'user' else 'model'
        history.append({"role": role, "text": row['message']}) # Dùng key 'text'
        
    return history

# --- HÀM GỌI API GEMINI ---

def ask_gemini(question, history=None, system_prompt="Bạn là chatbot hỗ trợ sinh viên của Trường X. Hãy trả lời câu hỏi một cách thân thiện, chính xác và bám sát vai trò hỗ trợ học tập."):
    """
    Hàm gọi API Gemini, có truyền lịch sử hội thoại (history) để duy trì ngữ cảnh.
    """
    try:
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.7
        )
        
        # 1. CHUYỂN ĐỔI history ĐƠN GIẢN SANG types.Content
        gemini_history = []
        if history:
            for item in history:
                # CÁCH SỬA LỖI: Tạo Content trực tiếp từ chuỗi (string) để tránh lỗi validation
                gemini_history.append(
                    types.Content(
                        role=item['role'], 
                        parts=[item['text']] # Chỉ truyền chuỗi tin nhắn vào list parts
                    )
                )
        
        # 2. Tạo Chat Session với lịch sử
        chat = client.chats.create(
            model="gemini-2.5-flash",
            history=gemini_history,
            config=config
        )
        
        # 3. Gửi tin nhắn mới
        response = chat.send_message(question)
        
        return response.text
        
    except Exception as e:
        # IN LỖI CHI TIẾT RA TERMINAL để dễ debug
        print(f"LỖI CHI TIẾT KHI GỌI API: {e}")
        # TRẢ VỀ CHUỖI LỖI ĐƠN GIẢN, TRÁNH LƯU CHUỖI LỖI LỚN VÀO DB
        return "Đã xảy ra lỗi kết nối hoặc xác thực API. Vui lòng thử lại."


# --- ENDPOINTS FLASK ---

@app.route("/")
def index():
    """Endpoint trả về trang chat (sử dụng file chat.html)."""
    return render_template("chat.html")

@app.route("/history")
def history():
    """Endpoint trả về lịch sử hội thoại dưới dạng JSON."""
    user_id = request.args.get("user_id", "guest_user")
    
    # Dùng hàm get_history đã sửa
    messages = get_history(user_id, limit=999) 
    
    # Chuyển đổi định dạng history đã sửa thành định dạng phù hợp cho JSON response
    # Lưu ý: Chuyển key 'text' thành 'message' để JS hiểu
    history_list = [{"role": item['role'], "message": item['text']} for item in messages]
    
    return jsonify({"history": history_list})

@app.post("/chat")
def chat():
    """
    API endpoint nhận câu hỏi, xử lý database, gọi AI và trả lời.
    """
    try:
        data = request.get_json()
        user_id = data.get("user_id", "guest_user") 
        question = data.get("message")

        if not question:
            return jsonify({"error": "Thiếu nội dung tin nhắn"}), 400

        # 1. Lưu câu hỏi vào DB
        save_message(user_id, 'user', question)
        
        # 2. Lấy lịch sử hội thoại (5 tin nhắn gần nhất)
        history = get_history(user_id, limit=5)
        
        # 3. Gọi hàm xử lý và nhận câu trả lời
        answer = ask_gemini(question, history=history)
        
        # 4. Lưu câu trả lời vào DB
        save_message(user_id, 'assistant', answer)

        return jsonify({"answer": answer})

    except Exception as e:
        print(f"Lỗi trong endpoint /chat: {e}")
        return jsonify({"error": "Lỗi server nội bộ"}), 500

# --- CHẠY SERVER FLASK ---
if __name__ == "__main__":
    print("Đang chạy server Flask...")
    app.run(debug=True)