# File: backend/view_history.py

import sqlite3

DATABASE = 'backend/chatbot.db'

def view_history():
    """In toàn bộ lịch sử hội thoại ra Terminal."""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()

        # Lấy tất cả tin nhắn, sắp xếp theo thời gian
        cursor.execute("SELECT timestamp, user_id, role, message FROM conversations ORDER BY timestamp ASC")
        messages = cursor.fetchall()

        print("\n--- LỊCH SỬ HỘI THOẠI ĐÃ LƯU ---")

        if not messages:
            print("Database trống. Hãy gửi tin nhắn đầu tiên!")
            return

        for msg in messages:
            role = "BOT" if msg['role'] == 'model' or msg['role'] == 'assistant' else "USER"
            print(f"[{msg['timestamp'].split('.')[0]}] {role}: {msg['message']}")

        print("---------------------------------")

    except sqlite3.OperationalError:
        print(f"LỖI: Không tìm thấy database {DATABASE}. Hãy chạy lại 'python backend/init_db.py'.")
    except Exception as e:
        print(f"Lỗi đọc database: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    view_history()