// File: backend/static/js/chat.js

// 1. KIỂM TRA ĐĂNG NHẬP
const currentUser = JSON.parse(localStorage.getItem('currentUser'));
if (!currentUser) {
    window.location.href = '/login';
}

// 2. KHỞI TẠO BIẾN TOÀN CỤC & DOM ELEMENTS
let currentSessionId = null;
const chatHistory = document.getElementById("chat-history");
const sessionList = document.getElementById("session-list");
const userNameEl = document.getElementById('user-name');
const userMssvEl = document.getElementById('user-mssv');

// Hiển thị thông tin sinh viên lên giao diện
if (userNameEl) userNameEl.textContent = currentUser.name;
if (userMssvEl) userMssvEl.textContent = currentUser.mssv;

// ---------------------------------------------------------
// 3. TÍNH NĂNG: TIN TỨC TỰ ĐỘNG (AUTO CRAWL & SCROLL)
// ---------------------------------------------------------
async function loadNews() {
    // Tìm thẻ div chứa animation cuộn
    const newsContainer = document.querySelector('.animate-vertical-scroll');
    if (!newsContainer) return;

    try {
        // Gọi API lấy tin tức từ Server (Server đã cào từ web trường)
        const res = await fetch('/api/news');
        const data = await res.json();
        const newsList = data.news;

        if (newsList && newsList.length > 0) {
            newsContainer.innerHTML = ''; // Xóa nội dung "Đang tải..."

            // Hàm tạo HTML cho 1 thẻ tin tức (Có link click được)
            const createNewsItem = (item) => `
                <a href="${item.link}" target="_blank" class="block bg-white p-4 rounded-2xl border border-emerald-100 shadow-sm hover:shadow-md hover:border-emerald-300 transition group cursor-pointer mb-3">
                    <div class="flex justify-between items-start">
                        <p class="text-xs font-bold text-emerald-700 mb-1 group-hover:text-emerald-900 transition line-clamp-2">${item.title}</p>
                        <i class="fa-solid fa-arrow-up-right-from-square text-[10px] text-emerald-400 opacity-0 group-hover:opacity-100 transition flex-shrink-0 ml-2"></i>
                    </div>
                    <p class="text-xs text-slate-600 leading-relaxed">${item.desc}</p>
                </a>
            `;

            // HTML cho thẻ Telegram (Cố định, giao diện nét đứt)
            const telegramItem = `
                <div class="bg-emerald-50 p-4 rounded-2xl border border-dashed border-emerald-400 cursor-default select-none mb-3">
                    <p class="text-xs font-bold text-emerald-800 flex items-center gap-1.5 mb-1">
                        <i class="fa-brands fa-telegram"></i> Hỗ trợ qua Telegram
                    </p>
                    <p class="text-[11px] text-emerald-700">Tính năng đang được phát triển.</p>
                </div>
            `;

            // BƯỚC QUAN TRỌNG: Tạo nội dung
            // 1. Tạo danh sách tin tức từ dữ liệu API
            let originalContent = newsList.map(item => createNewsItem(item)).join('');
            
            // 2. Thêm thẻ Telegram vào cuối
            originalContent += telegramItem;

            // 3. NHÂN ĐÔI nội dung (Duplicate) để tạo vòng lặp cuộn vô tận không bị ngắt quãng
            // Khi animation chạy hết danh sách 1, nó sẽ nối tiếp ngay vào danh sách 2
            const finalHtml = originalContent + originalContent;

            // Gán vào giao diện
            newsContainer.innerHTML = finalHtml;
        }
    } catch (e) {
        console.error("Lỗi tải tin tức:", e);
        // Nếu lỗi, hiển thị thông báo tĩnh
        newsContainer.innerHTML = `
            <div class="bg-white p-4 rounded-2xl border border-red-100 text-center">
                <p class="text-xs text-red-500">Không thể tải tin tức mới.</p>
            </div>
        `;
    }
}

// ---------------------------------------------------------
// 4. TÍNH NĂNG: QUẢN LÝ SESSIONS (DANH SÁCH CHAT)
// ---------------------------------------------------------
async function loadSessions() {
    try {
        const res = await fetch(`/api/sessions?user_id=${currentUser.mssv}`);
        const data = await res.json();
        
        sessionList.innerHTML = ''; 
        
        if (data.sessions && data.sessions.length > 0) {
            data.sessions.forEach(session => {
                const div = document.createElement('div');
                const isActive = currentSessionId === session.id ? 'active' : '';
                
                div.className = `session-item p-3 rounded-lg cursor-pointer hover:bg-gray-50 text-sm text-gray-700 truncate transition mb-1 flex items-center gap-2 ${isActive}`;
                div.innerHTML = `<i class="fa-regular fa-message text-xs opacity-50"></i> ${session.title || "Cuộc trò chuyện"}`;
                div.onclick = () => switchSession(session.id);
                sessionList.appendChild(div);
            });
        } else {
            sessionList.innerHTML = '<p class="text-xs text-center text-gray-400 mt-4">Chưa có lịch sử</p>';
        }
    } catch (e) {
        console.error("Lỗi tải session:", e);
    }
}

async function switchSession(sessionId) {
    currentSessionId = sessionId;
    await loadSessions(); 
    await loadMessages(sessionId);
}

async function createNewChat() {
    currentSessionId = null;
    chatHistory.innerHTML = '';
    addBotMessage(`Chào <b>${currentUser.name}</b>! Mình có thể giúp gì cho bạn hôm nay?`);
    
    const activeItems = document.querySelectorAll('.session-item.active');
    activeItems.forEach(item => item.classList.remove('active'));
}

async function clearHistory() {
    if (!currentSessionId) {
        chatHistory.innerHTML = '';
        addBotMessage(`Đã làm mới khung chat!`);
        return;
    }
    
    if(!confirm("Bạn có chắc muốn XÓA VĨNH VIỄN cuộc trò chuyện này không?")) return;

    try {
        const res = await fetch('/api/delete_session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: currentSessionId, user_id: currentUser.mssv })
        });
        const data = await res.json();
        
        if (data.success) {
            createNewChat();
            loadSessions();
        } else {
            alert(data.message || "Không thể xóa.");
        }
    } catch (e) {
        alert("Lỗi kết nối server");
    }
}

// ---------------------------------------------------------
// 5. TÍNH NĂNG: XỬ LÝ TIN NHẮN (MESSAGES)
// ---------------------------------------------------------
async function loadMessages(sessionId) {
    chatHistory.innerHTML = '';
    try {
        const res = await fetch(`/api/messages?session_id=${sessionId}`);
        const data = await res.json();
        
        if (data.messages && data.messages.length > 0) {
            data.messages.forEach(msg => {
                if (msg.role === 'user') addUserMessage(msg.message);
                else addBotMessage(msg.message);
            });
        }
    } catch (e) {
        console.error("Lỗi tải tin nhắn:", e);
    }
}

function addUserMessage(text) {
    if (!text) return;
    const div = document.createElement('div');
    div.className = "flex justify-end animate-fade-in";
    div.innerHTML = `<div class="bg-emerald-600 text-white px-5 py-2.5 rounded-2xl rounded-tr-none max-w-[85%] text-sm shadow-md leading-relaxed">${text}</div>`;
    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function addBotMessage(text) {
    if (!text) return;
    const div = document.createElement('div');
    div.className = "flex justify-start items-start gap-3 animate-fade-in";
    div.innerHTML = `
        <div class="w-9 h-9 bg-white border border-emerald-100 rounded-full flex items-center justify-center text-emerald-700 font-bold text-xs shadow-sm flex-shrink-0">HT</div>
        <div class="bg-white border border-gray-100 text-gray-800 px-5 py-3 rounded-2xl rounded-tl-none max-w-[85%] text-sm shadow-sm leading-relaxed">${text}</div>
    `;
    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// Xử lý khi nhấn nút Gửi (Chat)
const chatForm = document.getElementById('chat-form');
if (chatForm) {
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const input = document.getElementById('chat-input');
        const text = input.value.trim();
        if (!text) return;

        addUserMessage(text);
        input.value = '';

        try {
            const res = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: currentUser.mssv,
                    user_name: currentUser.name,
                    message: text,
                    session_id: currentSessionId
                })
            });
            
            const data = await res.json();
            
            if (data.answer) {
                addBotMessage(data.answer);
                if (!currentSessionId && data.session_id) {
                    currentSessionId = data.session_id;
                    loadSessions();
                }
            }
        } catch (e) {
            addBotMessage("Xin lỗi, tôi đang gặp sự cố kết nối.");
        }
    });
}

// ---------------------------------------------------------
// 6. TÍNH NĂNG: GỬI FEEDBACK (GÓP Ý)
// ---------------------------------------------------------
const fbForm = document.getElementById('feedback-form');
const fbSubmit = document.getElementById('fb-submit');
const fbStatus = document.getElementById('fb-status');

if (fbForm) {
    fbForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const content = document.getElementById('fb-content').value.trim();
        const name = document.getElementById('fb-name').value.trim();

        if (!content) {
            fbStatus.textContent = "Vui lòng nhập nội dung";
            fbStatus.classList.add('text-red-500');
            return;
        }

        fbSubmit.disabled = true;
        fbSubmit.textContent = "...";

        try {
            const res = await fetch('/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name, message: content })
            });
            
            const data = await res.json();
            if(data.status === 'success') {
                fbStatus.textContent = "Đã gửi thành công!";
                fbStatus.classList.remove('text-red-500');
                fbStatus.classList.add('text-emerald-600');
                fbForm.reset();
            } else {
                fbStatus.textContent = "Lỗi gửi tin.";
            }
        } catch (err) {
            fbStatus.textContent = "Lỗi kết nối";
        } finally {
            setTimeout(() => {
                fbSubmit.disabled = false;
                fbSubmit.textContent = "Gửi phản hồi";
                fbStatus.textContent = "";
            }, 3000);
        }
    });
}

function logout() {
    localStorage.removeItem('currentUser');
    window.location.href = '/login';
}

// ---------------------------------------------------------
// 7. KHỞI CHẠY KHI TRANG LOAD XONG
// ---------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
    loadSessions();    // Tải lịch sử chat
    createNewChat();   // Khởi tạo khung chat mới
    loadNews();        // Tải tin tức tự động
});