// File: backend/static/js/chat.js

// 1. KIỂM TRA ĐĂNG NHẬP
const currentUser = JSON.parse(localStorage.getItem('currentUser'));

if (!currentUser) {
    // Nếu chưa đăng nhập, đá về trang login
    window.location.href = '/login';
}

// Cập nhật giao diện với tên sinh viên
const headerTitle = document.getElementById("chatbox-title");
if (headerTitle && currentUser) {
    headerTitle.innerHTML = `Xin chào, ${currentUser.name} <span class="text-xs font-normal block text-sky-200">MSSV: ${currentUser.mssv}</span>`;
}

// ... (Giữ nguyên các biến DOM elements: chatForm, chatInput...) ...
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatHistory = document.getElementById("chat-history");
const sendButton = document.getElementById("send-button");
const chatHeader = document.getElementById("chat-header");

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

function addBotMessage(text) {
    const wrapper = document.createElement("div");
    wrapper.className = "flex items-start gap-3";
    wrapper.innerHTML = `
        <div class="flex items-center justify-center w-8 h-8 rounded-full bg-sky-600 text-white flex-shrink-0 text-xs font-semibold">HT</div>
        <div class="max-w-[80%] bg-sky-50 border border-sky-100 rounded-2xl rounded-tl-sm px-3.5 py-2.5 text-sm text-slate-800">
            ${text} </div>
    `;
    chatHistory.appendChild(wrapper);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// HÀM GỬI YÊU CẦU (Đã cập nhật user_id)
async function sendChatRequest(message) {
    try {
        if(chatHeader) chatHeader.classList.add('bg-orange-500');

        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                user_id: currentUser.mssv, // GỬI MSSV ĐANG ĐĂNG NHẬP
                user_name: currentUser.name,
                message: message 
            })
        });

        const data = await response.json();
        
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
        console.error('Lỗi:', error);
        addBotMessage(`Lỗi kết nối.`);
    } finally {
        if(sendButton) sendButton.disabled = false;
    }
}

async function loadHistory() {
    if (!currentUser) return;
    try {
        // Tải lịch sử của user cụ thể
        const res = await fetch(`/history?user_id=${currentUser.mssv}`);
        const data = await res.json();
        
        // Xóa tin nhắn chào mặc định
        chatHistory.innerHTML = ''; 

        if (data.history && data.history.length > 0) {
            data.history.forEach(item => {
                if (item.role === 'user') addUserMessage(item.message);
                else addBotMessage(item.message);
            });
        } else {
            addBotMessage(`Chào <b>${currentUser.name}</b>! Mình có thể giúp gì cho bạn hôm nay?`);
        }
    } catch (error) {
        console.error("Lỗi history:", error);
    }
}

// Nút Đăng xuất (Thêm vào HTML sau nếu cần, hoặc chạy lệnh này ở console)
function logout() {
    localStorage.removeItem('currentUser');
    window.location.href = '/login';
}

// ... (Giữ nguyên logic event listener submit/keydown) ...
if (chatForm) {
    chatForm.addEventListener("submit", function (e) {
        e.preventDefault();
        const text = chatInput.value.trim();
        if (!text) return;
        addUserMessage(text);
        chatInput.value = "";
        if(sendButton) sendButton.disabled = true;
        sendChatRequest(text);
    });
}

if (chatInput) {
    chatInput.addEventListener("keydown", function (e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            if(chatForm) chatForm.dispatchEvent(new Event("submit"));
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    loadHistory();
});