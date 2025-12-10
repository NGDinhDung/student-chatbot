# File: backend/init_db.py (ĐÃ SỬA NỘI DUNG FAQ VÀ TÊN TRƯỜNG)

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

    # Thêm dữ liệu mẫu vào FAQ (Đã sửa lỗi cú pháp và nội dung)
    
    # Intent: HOI_HOC_PHAN
    cursor.execute("INSERT OR IGNORE INTO faq (id, question, answer, intent_category) VALUES (1, 'Học kỳ này có bao nhiêu học phần?', 'Thông tin chi tiết về số lượng học phần, tín chỉ và nội dung môn học được công bố chính thức trên cổng thông tin sinh viên của Trường Đại học Giao thông Vận tải (UTH).', 'HOI_HOC_PHAN')")
    
    # Intent: HOI_LICH_THI
    cursor.execute("INSERT OR IGNORE INTO faq (id, question, answer, intent_category) VALUES (2, 'Khi nào có lịch thi cuối kỳ?', 'Lịch thi chính thức sẽ được Phòng Đào tạo công bố trên cổng thông tin sinh viên trước 2 tuần so với ngày thi đầu tiên của Trường Đại học Giao thông Vận tải (UTH).', 'HOI_LICH_THI')")
    
    # Intent: HOI_LICH_HOC
    cursor.execute("INSERT OR IGNORE INTO faq (id, question, answer, intent_category) VALUES (3, 'Thời khóa biểu của em ở đâu?', 'Bạn vui lòng đăng nhập vào cổng thông tin sinh viên, chọn mục \"Thời khóa biểu cá nhân\" để xem chi tiết lịch học của Trường Đại học Giao thông Vận tải (UTH).', 'HOI_LICH_HOC')")


    conn.commit()
    conn.close()
    print(f"Database {DATABASE} đã được khởi tạo và thêm dữ liệu mẫu.")

if __name__ == "__main__":
    init_db()