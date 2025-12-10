# File: backend/app.py (PHIÊN BẢN HOÀN CHỈNH - SỬA LỖI ĐỊNH DẠNG & LOGIC UTH)

import os
import sqlite3
import json 
from flask import Flask, request, jsonify, render_template, url_for
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- CẤU HÌNH VÀ KHỞI TẠO ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
DATABASE = 'backend/chatbot.db'

# Định nghĩa các Ý định (Intents) mà bot có thể xử lý qua FAQ
FAQ_INTENTS = {
    "HOI_HOC_PHAN": "Hỏi về số lượng học phần, tín chỉ, hoặc nội dung học phần.",
    "HOI_LICH_THI": "Hỏi về lịch thi, thời gian thi giữa kỳ/cuối kỳ.",
    "HOI_LICH_HOC": "Hỏi về thời khóa biểu hoặc lịch học chính thức."
}

if not api_key:
    raise ValueError("GEMINI_API_KEY không được tìm thấy. Hãy kiểm tra file .env.")

client = genai.Client(api_key=api_key)
app = Flask(__name__)

# --- HÀM HỖ TRỢ DATABASE (Không đổi) ---

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
        history.append({"role": role, "text": row['message']}) 
        
    return history

# --- LOGIC XỬ LÝ Ý ĐỊNH VÀ TRUY VẤN DATABASE ---

def get_faq_answer(question):
    """
    Sử dụng Gemini để phân loại câu hỏi và truy vấn database FAQ.
    Trả về câu trả lời từ DB nếu ý định được nhận dạng, nếu không trả về None.
    """
    tool_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "intent": types.Schema(
                type=types.Type.STRING,
                description=f"Tên ý định được xác định từ câu hỏi của người dùng. Phải là một trong các giá trị sau: {list(FAQ_INTENTS.keys())}, hoặc 'CHUNG' nếu câu hỏi không thuộc phạm vi FAQ."
            ),
            "keyword": types.Schema(
                type=types.Type.STRING,
                description="Từ khóa/cụm từ chính để thực hiện truy vấn database (ví dụ: 'học kỳ này' hoặc 'lịch thi')."
            )
        },
        required=["intent", "keyword"]
    )
    
    intent_list = [f"'{k}' ({v})" for k, v in FAQ_INTENTS.items()]
    system_prompt_faq = f"""
    Bạn là một hệ thống phân loại câu hỏi cho Trường Đại học Giao thông Vận tải (UTH).
    Nhiệm vụ của bạn là phân tích câu hỏi của người dùng và xác định Ý định (Intent) của họ.
    
    Các Intent đã biết (FAQ) là: {", ".join(intent_list)}. Nếu không khớp, hãy dùng intent 'CHUNG'.
    
    Sau đó, tạo ra một JSON object tuân thủ schema đã cho. KHÔNG ĐƯỢC THÊM BẤT CẢNH VĂN BẢN NÀO NGOÀI JSON.
    """
    
    try:
        # SỬA LỖI ĐỊNH DẠNG: Sử dụng types.Part.from_text() rõ ràng
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Content(role="user", parts=[types.Part.from_text(question)]) 
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt_faq,
                response_mime_type="application/json",
                response_schema=tool_schema,
                temperature=0.0 
            )
        )
        
        json_data = json.loads(response.text)
        intent = json_data.get('intent', 'CHUNG')
        
        if intent in FAQ_INTENTS:
            conn = get_db()
            answer_row = conn.execute(
                "SELECT answer FROM faq WHERE intent_category = ?",
                (intent,)
            ).fetchone()
            conn.close()
            
            if answer_row:
                return answer_row['answer']
                
    except Exception as e:
        print(f"Lỗi phân loại ý định/truy vấn FAQ: {e}")
        pass
        
    return None 

def ask_gemini(question, history=None, system_prompt="Bạn là chatbot hỗ trợ sinh viên của Trường Đại học Giao thông Vận tải (UTH). Hãy trả lời câu hỏi một cách thân thiện, chính xác và bám sát vai trò hỗ trợ học tập."):
    """
    Hàm gọi API Gemini (Generative) để tạo câu trả lời khi không tìm thấy trong FAQ.
    """
    try:
        config = types.GenerateContentConfig(
            system_instruction=system_prompt, 
            temperature=0.7
        )
        
        gemini_history = []
        if history:
            for item in history:
                # SỬA LỖI VALIDATION: Tạo Content bằng types.Part.from_text() rõ ràng cho lịch sử
                gemini_history.append(
                    types.Content(
                        role=item['role'], 
                        parts=[types.Part.from_text(item['text'])] 
                    )
                )
        
        chat = client.chats.create(
            model="gemini-2.5-flash",
            history=gemini_history,
            config=config
        )
        
        response = chat.send_message(question)
        
        return response.text
        
    except Exception as e:
        print(f"LỖI CHI TIẾT KHI GỌI API: {e}")
        return "Đã xảy ra lỗi kết nối hoặc xác thực API. Vui lòng thử lại."


# --- ENDPOINTS FLASK (Giữ nguyên) ---

@app.route("/")
def index():
    return render_template("chat.html")

@app.route("/history")
def history():
    user_id = request.args.get("user_id", "guest_user")
    
    messages = get_history(user_id, limit=999) 
    
    history_list = [{"role": item['role'], "message": item['text']} for item in messages]
    
    return jsonify({"history": history_list})

@app.post("/chat")
def chat():
    try:
        data = request.get_json()
        user_id = data.get("user_id", "guest_user") 
        question = data.get("message")

        if not question:
            return jsonify({"error": "Thiếu nội dung tin nhắn"}), 400
        
        # LOGIC HYBRID
        answer = get_faq_answer(question)
        history = None 

        if answer is None:
            history = get_history(user_id, limit=5)
            answer = ask_gemini(question, history=history)
        
        # Lưu câu hỏi và trả lời
        save_message(user_id, 'user', question)
        save_message(user_id, 'assistant', answer)

        return jsonify({"answer": answer})

    except Exception as e:
        print(f"Lỗi trong endpoint /chat: {e}")
        return jsonify({"error": "Lỗi server nội bộ"}), 500

@app.post("/feedback")
def feedback():
    try:
        data = request.get_json()
        name = data.get("name", "Ẩn danh")
        rating = data.get("type", "Không đánh giá")
        message = data.get("message", "Không có nội dung")

        print("--- PHẢN HỒI MỚI ĐÃ ĐƯỢC NHẬN ---")
        print(f"Người gửi: {name}")
        print(f"Đánh giá: {rating}")
        print(f"Nội dung: {message}")
        print("---------------------------------")
        
        return jsonify({"status": "success", "message": "Cảm ơn bạn đã phản hồi!"})

    except Exception as e:
        print(f"Lỗi khi nhận phản hồi: {e}")
        return jsonify({"status": "error", "message": "Lỗi server khi xử lý phản hồi."}), 500

# --- CHẠY SERVER FLASK ---
if __name__ == "__main__":
    print("Đang chạy server Flask...")
    app.run(debug=True)