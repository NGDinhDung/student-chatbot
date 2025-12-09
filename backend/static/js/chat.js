// File: backend/static/js/chat.js
// Logic xử lý chat và gọi API Gemini

const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatHistory = document.getElementById("chat-history");
const sendButton = document.getElementById("send-button");
const chatHeader = document.getElementById("chat-header");

// Hàm hiển thị tin nhắn của người dùng (Tailwind)
function addUserMessage(text) {
    const wrapper = document.createElement("div");
    wrapper.className = "flex items-start justify-end gap-3";
    wrapper.innerHTML = `
        <div class="max-w-[80%] bg-sky-600 text-white rounded-2xl rounded-tr-sm px-3.5 py-2.5 text-sm">
            ${text}
        </div>
        <div class="flex items-center justify-center w-8 h-8 rounded-full bg-sky-200 text-sky-800 flex-shrink-0 text-xs font-semibold">SV</div>
    `;
    chatHistory.appendChild(wrapper);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// Hàm hiển thị tin nhắn của Bot (Tailwind)
function addBotMessage(text) {
    const wrapper = document.createElement("div");
    wrapper.className = "flex items-start gap-3";
    wrapper.innerHTML = `
        <div class="flex items-center justify-center w-8 h-8 rounded-full bg-sky-600 text-white flex-shrink-0 text-xs font-semibold">HT</div>
        <div class="max-w-[80%] bg-sky-50 border border-sky-100 rounded-2xl rounded-tl-sm px-3.5 py-2.5 text-sm text-slate-800">
            ${text}
        </div>
    `;
    chatHistory.appendChild(wrapper);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// -----------------
// LOGIC GỌI API GEMINI
// -----------------

async function sendChatRequest(message) {
    try {
        // Cập nhật trạng thái kết nối trên header
        if(chatHeader) {
            chatHeader.classList.remove('bg-sky-600');
            chatHeader.classList.remove('bg-red-600');
            chatHeader.classList.add('bg-orange-500'); // Màu cam khi đang xử lý
        }

        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: 'guest_user', message: message })
        });

        const data = await response.json();
        
        // Trở lại màu xanh khi thành công
        if(chatHeader) {
            chatHeader.classList.remove('bg-orange-500');
            chatHeader.classList.add('bg-sky-600'); 
        }

        if (data.answer) {
            addBotMessage(data.answer);
        } else if (data.error) {
            addBotMessage(`Lỗi: ${data.error}`);
        }

    } catch (error) {
        console.error('Lỗi kết nối server:', error);
        addBotMessage(`Lỗi: Không thể kết nối tới máy chủ Flask.`);
        if(chatHeader) {
            chatHeader.classList.remove('bg-orange-500');
            chatHeader.classList.add('bg-red-600'); // Báo lỗi đỏ
        }
    } finally {
        if(sendButton) sendButton.disabled = false;
    }
}

// Tải lịch sử hội thoại khi load trang
async function loadHistory() {
    const userId = 'guest_user';
    try {
        const res = await fetch(`/history?user_id=${userId}`);
        const data = await res.json();

        // Xóa tin nhắn chào mừng mặc định của HTML
        const defaultGreeting = chatHistory.querySelector('.flex-1.px-5.py-4.space-y-3.overflow-y-auto.scroll-area.bg-white > div');
        
        if (data.history && data.history.length > 0) {
            if (defaultGreeting) defaultGreeting.remove();
            data.history.forEach(item => {
                if (item.role === 'user') {
                    addUserMessage(item.message);
                } else {
                    addBotMessage(item.message);
                }
            });
        } else {
            // Giữ tin nhắn chào mừng mặc định của HTML nếu không có lịch sử
            if (!defaultGreeting) {
                 addBotMessage('Xin chào 👋 Mình là trợ lý Hỗ trợ Học tập. Bạn có thể hỏi về các thông tin trong phạm vi hỗ trợ nhé!');
            }
        }
    } catch (error) {
        console.error("Lỗi khi tải lịch sử:", error);
    }
}


// Xử lý sự kiện gửi tin nhắn
if (chatForm) {
    chatForm.addEventListener("submit", function (e) {
        e.preventDefault();
        const text = chatInput.value.trim();
        if (!text) return;

        addUserMessage(text);
        chatInput.value = "";
        if(sendButton) sendButton.disabled = true;

        // Gửi yêu cầu API
        sendChatRequest(text);
    });
}


// Gửi khi nhấn Enter
if (chatInput) {
    chatInput.addEventListener("keydown", function (e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            if(chatForm) chatForm.dispatchEvent(new Event("submit"));
        }
    });
}

// Khởi chạy khi DOM đã sẵn sàng
document.addEventListener("DOMContentLoaded", () => {
    loadHistory();
});