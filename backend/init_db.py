# File: backend/init_db.py

import sqlite3

DATABASE = 'backend/chatbot.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # --- 1. TẠO BẢNG ---
    cursor.execute("CREATE TABLE IF NOT EXISTS users (mssv TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL, major TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS chat_sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, title TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES users(mssv))")
    cursor.execute("CREATE TABLE IF NOT EXISTS conversations (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER, user_id TEXT, role TEXT, message TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(session_id) REFERENCES chat_sessions(id))")
    cursor.execute("CREATE TABLE IF NOT EXISTS faq (id INTEGER PRIMARY KEY AUTOINCREMENT, question TEXT NOT NULL, answer TEXT NOT NULL, intent_category TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS schedules (id INTEGER PRIMARY KEY AUTOINCREMENT, mssv TEXT, student_name TEXT, schedule_info TEXT, FOREIGN KEY(mssv) REFERENCES users(mssv))")

    # --- 2. KHO DỮ LIỆU CHUẨN (CẬP NHẬT LINK CHÍNH THỨC) ---
    faqs = [
        # === CỔNG THÔNG TIN & ĐĂNG KÝ MÔN (PORTAL) ===
        ('đăng ký môn học ở đâu', 'Sinh viên đăng ký môn học chính thức tại Cổng thông tin sinh viên: https://portal.ut.edu.vn/. Hãy đăng nhập để xem lịch đăng ký cụ thể.', 'HOI_DKMH'),
        ('xem thời khóa biểu ở đâu', 'Bạn đăng nhập vào https://portal.ut.edu.vn/ -> Chọn mục "Thời khóa biểu" để xem lịch học cá nhân chi tiết.', 'HOI_LICH_HOC'),
        ('xem điểm thi ở đâu', 'Kết quả học tập được cập nhật tại https://portal.ut.edu.vn/. Điểm thường có sau khi thi 1-2 tuần.', 'HOI_DIEM'),
        ('quên mật khẩu portal', 'Bạn sử dụng chức năng "Quên mật khẩu" ngay trên trang https://portal.ut.edu.vn/. Nếu không được, vui lòng liên hệ Tổ CNTT tại Cơ sở 1.', 'HOI_KY_THUAT'),
        ('web trường bị sập', 'Vào giờ cao điểm đăng ký môn, trang Portal có thể bị chậm. Bạn hãy kiên nhẫn nhấn F5 hoặc truy cập lại sau ít phút tại https://portal.ut.edu.vn/.', 'HOI_KY_THUAT'),

        # === TÀI CHÍNH & HỌC PHÍ (PAYMENT) ===
        ('đóng học phí ở đâu', 'Bạn có thể đóng học phí trực tuyến qua cổng thanh toán chính thức: https://payment.ut.edu.vn/. Ngoài ra có thể đóng tại quày cơ sở 1.', 'HOI_HOC_PHI'),
        ('trang web đóng tiền trường', 'Trang thanh toán chính thức của UTH là: https://payment.ut.edu.vn/. Sinh viên lưu ý không truy cập các đường link lạ giả mạo.', 'HOI_HOC_PHI'),
        ('học phí năm 2024 2025', 'Năm học 2024-2025, học phí hệ đại trà khoảng 450.000đ/tín chỉ, hệ chất lượng cao khoảng 980.000đ/tín chỉ. Chi tiết xem tại Portal.', 'HOI_HOC_PHI'),
        ('quên đóng học phí', 'Quá hạn đóng học phí sẽ bị hủy kết quả đăng ký môn học và cấm thi. Hãy kiểm tra công nợ thường xuyên trên https://payment.ut.edu.vn/.', 'HOI_HOC_PHI'),

        # === CHƯƠNG TRÌNH ĐÀO TẠO & HỌC VỤ ===
        ('bao nhiêu tín chỉ ra trường', 'Tùy ngành, thường từ 120-150 tín chỉ. Bạn xem Khung chương trình đào tạo trong Sổ tay sinh viên trên Portal.', 'HOI_CT_DAO_TAO'),
        ('điều kiện tốt nghiệp', 'Sinh viên cần: 1. Tích lũy đủ tín chỉ; 2. ĐTB tích lũy >= 2.0; 3. Có chứng chỉ GDQP-AN & GDTC; 4. Đạt chuẩn Ngoại ngữ & Tin học.', 'HOI_CT_DAO_TAO'),
        ('cảnh báo học vụ', 'Bị cảnh báo nếu ĐTB học kỳ 1 < 0.8; các HK sau < 1.0; hoặc ĐTB tích lũy < 1.2 (năm 1). Bị 3 lần liên tiếp sẽ buộc thôi học.', 'HOI_HOC_VU'),
        ('bảo lưu kết quả', 'Sinh viên được xin bảo lưu (tối đa 2 năm) vì lý do sức khỏe hoặc nghĩa vụ quân sự. Nộp đơn tại Phòng Đào tạo.', 'HOI_HOC_VU'),

        # === THÔNG TIN NHÀ TRƯỜNG & LIÊN HỆ ===
        ('trường có mấy cơ sở', 'UTH có 3 cơ sở: CS1 (Bình Thạnh), CS2 (Thủ Đức) và CS3 (Quận 12 - Học GDQP).', 'HOI_NHA_TRUONG'),
        ('liên hệ phòng đào tạo', 'Phòng Đào tạo: Tầng trệt Khu A, Cơ sở 1 (Số 2 Võ Oanh). SĐT: 028.3512.6902. Email: pdt@uth.edu.vn.', 'HOI_LIEN_HE'),
        ('lịch nghỉ tết 2025', 'Dự kiến nghỉ Tết từ 20/01/2025 đến 09/02/2025. Theo dõi thông báo chính thức trên Portal.', 'HOI_LICH_HOC')
    ]
    
    cursor.executemany("INSERT OR IGNORE INTO faq (question, answer, intent_category) VALUES (?, ?, ?)", faqs)

    conn.commit()
    conn.close()
    print("Database đã cập nhật Link Portal & Payment mới nhất.")

if __name__ == "__main__":
    init_db()