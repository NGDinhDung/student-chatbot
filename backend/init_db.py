# File: backend/init_db.py

import sqlite3

DATABASE = 'backend/chatbot.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # --- 1. CẤU TRÚC BẢNG ---

    # Bảng người dùng (Sinh viên)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        mssv TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        major TEXT -- Ngành học
    )
    """)

    # Bảng lịch sử hội thoại
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        role TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Bảng FAQ (Ngân hàng câu hỏi)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS faq (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        intent_category TEXT 
    )
    """)

    # Bảng Thời khóa biểu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mssv TEXT NOT NULL,
        student_name TEXT,
        schedule_info TEXT,
        FOREIGN KEY(mssv) REFERENCES users(mssv)
    )
    """)

    # --- 2. DỮ LIỆU MẪU (SEED DATA) ---

    # A. Dữ liệu Sinh viên (Dùng để đăng nhập)
    students = [
        ('2251120276', 'Nguyễn Đình Dũng', '2251120276@ut.edu.vn', 'Công nghệ thông tin'),
        ('2251120001', 'Trần Thị Mai', '2251120001@ut.edu.vn', 'Logistics'),
        ('2251120002', 'Lê Văn Hùng', '2251120002@ut.edu.vn', 'Kinh tế vận tải')
    ]
    cursor.executemany("INSERT OR IGNORE INTO users (mssv, name, email, major) VALUES (?, ?, ?, ?)", students)

    # B. Dữ liệu Thời khóa biểu (Cá nhân hóa từng SV)
    schedules = [
        ('2251120276', 'Nguyễn Đình Dũng', 'Thứ 2: Lập trình Web (T1-3, B102); Thứ 4: Trí tuệ nhân tạo (T7-9, C201); Thứ 6: Đồ án tốt nghiệp.'),
        ('2251120001', 'Trần Thị Mai', 'Thứ 3: Quản trị chuỗi cung ứng (T1-3, A404); Thứ 5: Tiếng Anh chuyên ngành (T4-6).'),
        ('2251120002', 'Lê Văn Hùng', 'Thứ 2: Kinh tế vĩ mô (T4-6); Thứ 6: Pháp luật đại cương (T1-3).')
    ]
    cursor.executemany("INSERT OR IGNORE INTO schedules (mssv, student_name, schedule_info) VALUES (?, ?, ?)", schedules)

    # C. Dữ liệu FAQ (Mở rộng phong phú các chủ đề)
    faqs = [
        # Chủ đề: Học vụ & Đào tạo
        ('Học kỳ này có bao nhiêu học phần?', 'Thông tin chi tiết về số lượng học phần và tín chỉ được công bố trên cổng đào tạo tín chỉ (sv.uth.edu.vn). Bạn hãy đăng nhập để xem chương trình khung nhé.', 'HOI_HOC_PHAN'),
        ('Một năm có mấy học kỳ?', 'Trường UTH tổ chức đào tạo theo 2 học kỳ chính (HK1, HK2) và 1 học kỳ phụ (Học kỳ hè) dành cho sinh viên học lại hoặc học vượt.', 'HOI_HOC_VU'),
        ('Điều kiện để được xét tốt nghiệp là gì?', 'Sinh viên cần tích lũy đủ số tín chỉ theo chương trình đào tạo, điểm trung bình chung tích lũy >= 2.0, có chứng chỉ GDQP, GDTC và chuẩn đầu ra Tiếng Anh/Tin học.', 'HOI_TOT_NGHIEP'),
        ('Cách tính điểm rèn luyện như thế nào?', 'Điểm rèn luyện được đánh giá qua việc tham gia các hoạt động phong trào, chấp hành nội quy. Bạn có thể xem chi tiết bảng điểm tại website Phòng Công tác Sinh viên.', 'HOI_REN_LUYEN'),
        
        # Chủ đề: Lịch thi & Thời khóa biểu
        ('Khi nào có lịch thi cuối kỳ?', 'Lịch thi chính thức thường được công bố trước kỳ thi 2-3 tuần trên website Phòng Đào tạo và trong tài khoản cá nhân của sinh viên.', 'HOI_LICH_THI'),
        ('Xem thời khóa biểu ở đâu?', 'Bạn vui lòng đăng nhập cổng thông tin sinh viên (sv.uth.edu.vn) -> Chọn mục "Thời khóa biểu cá nhân".', 'HOI_LICH_HOC'),
        ('Tôi bị trùng lịch thi phải làm sao?', 'Nếu bị trùng lịch thi, bạn cần làm đơn xin hoãn thi hoặc dự thi ghép tại Phòng Đào tạo ít nhất 1 tuần trước ngày thi.', 'HOI_TRUNG_LICH'),

        # Chủ đề: Tài chính & Học phí
        ('Học phí một tín chỉ là bao nhiêu?', 'Mức học phí tín chỉ tùy thuộc vào ngành học và hệ đào tạo (Đại trà/Chất lượng cao). Bạn vui lòng xem trong thông báo thu học phí đầu kỳ.', 'HOI_HOC_PHI'),
        ('Đóng học phí qua ngân hàng nào?', 'Sinh viên có thể đóng học phí qua các ngân hàng đối tác như Vietcombank, BIDV, Agribank hoặc qua ứng dụng Viettel Money. Nhớ ghi rõ MSSV và Họ tên.', 'HOI_DONG_TIEN'),
        
        # Chủ đề: Thủ tục hành chính
        ('Xin giấy xác nhận sinh viên ở đâu?', 'Bạn có thể xin giấy xác nhận sinh viên trực tiếp tại Phòng Công tác Sinh viên hoặc đăng ký trực tuyến trên cổng thông tin.', 'HOI_GIAY_TO'),
        ('Thẻ bảo hiểm y tế nhận ở đâu?', 'Thẻ BHYT thường được phát tại Trạm Y tế của trường hoặc qua Khoa quản lý vào đầu năm học. Vui lòng theo dõi thông báo.', 'HOI_BHYT')
    ]
    cursor.executemany("INSERT OR IGNORE INTO faq (question, answer, intent_category) VALUES (?, ?, ?)", faqs)

    conn.commit()
    conn.close()
    print(f"Database {DATABASE} đã được khởi tạo với dữ liệu Sinh viên, TKB và FAQ mở rộng.")

if __name__ == "__main__":
    init_db()