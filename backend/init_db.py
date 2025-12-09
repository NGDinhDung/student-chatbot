# File: backend/init_db.py

import sqlite3

DATABASE = 'backend/chatbot.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Bảng lưu trữ lịch sử hội thoại
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        role TEXT NOT NULL,           -- 'user' hoặc 'assistant'
        message TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Bảng lưu trữ thông tin thường gặp (FAQ)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS faq (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        intent_category TEXT 
    )
    """)

    # Thêm dữ liệu mẫu vào FAQ (cho mục đích demo sau này)
    cursor.execute("INSERT OR IGNORE INTO faq (id, question, answer, intent_category) VALUES (1, 'Học kỳ này có bao nhiêu học phần?', 'Sinh viên có thể tra cứu thông tin học phần chính thức trên cổng thông tin sinh viên.', 'General')")

    conn.commit()
    conn.close()
    print(f"Database {DATABASE} đã được khởi tạo và thêm dữ liệu mẫu.")

if __name__ == "__main__":
    init_db()