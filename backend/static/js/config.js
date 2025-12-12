// File: backend/static/js/config.js
// Giao diện Xanh Lá UTH (Green Theme) - Logo chữ UTH

// --- CẤU HÌNH MÀU SẮC ---
const brandColor = "#047857"; // Xanh lá đậm (Emerald-700)
const bgGradientStart = "#ecfdf5"; 
const bgGradientEnd = "#d1fae5";   

const defaultConfig = {
    background_color: bgGradientStart, 
    surface_color: "#ffffff",
    text_color: "#1e293b", 
    primary_action_color: brandColor,
    secondary_action_color: "#059669", 
    font_family: "'Inter', system-ui, -apple-system, sans-serif",
    font_size: 15,
    app_title: "Hỗ trợ Sinh viên UTH",
    app_subtitle: "Hỏi đáp nhanh về học vụ, học phí & quy chế",
    chatbox_title: "Trợ lý ảo UTH",
    chatbox_placeholder: "Nhập câu hỏi của bạn...",
    feedback_title: "Đánh giá dịch vụ",
    feedback_submit_text: "Gửi đánh giá"
};

const domRefs = {
    body: document.body,
    chatHeader: document.getElementById("chat-header"),
    chatboxTitle: document.getElementById("chatbox-title"),
    sendButton: document.getElementById("send-button"),
    feedbackSubmit: document.getElementById("feedback-submit"),
    chatInput: document.getElementById("chat-input"),
    card: document.querySelector("main > section"),
    logoutBtn: document.querySelector("header button")
};

async function onConfigChange(config) {
    const cfg = config || defaultConfig;
    
    // 1. Màu nền & Font
    domRefs.body.style.background = `linear-gradient(135deg, ${bgGradientStart} 0%, ${bgGradientEnd} 100%)`;
    domRefs.body.style.backgroundAttachment = "fixed";
    domRefs.body.style.fontFamily = cfg.font_family;
    
    // 2. Header (Thay Icon mặc định bằng Logo chữ UTH)
    if (domRefs.chatHeader) {
        domRefs.chatHeader.style.background = `linear-gradient(to right, ${cfg.primary_action_color}, ${cfg.secondary_action_color})`;
        domRefs.chatHeader.className = "flex items-center gap-4 px-6 py-4 text-white shadow-md rounded-t-2xl";
        
        // Thay thế phần Icon cũ bằng chữ UTH
        const iconDiv = domRefs.chatHeader.querySelector("div.flex.items-center.justify-center");
        if (iconDiv) {
            // Xóa icon SVG cũ
            iconDiv.innerHTML = ""; 
            // Thêm chữ UTH (Font Serif như mẫu)
            iconDiv.className = "flex items-center justify-center w-12 h-12 rounded-full bg-white text-emerald-800 text-xl font-serif font-bold border-2 border-emerald-100 shadow-sm tracking-widest";
            iconDiv.textContent = "UTH";
        }
    }

    // 3. Nút Gửi (Xanh lá)
    if (domRefs.sendButton) {
        domRefs.sendButton.style.backgroundColor = cfg.primary_action_color;
        domRefs.sendButton.className = "inline-flex items-center justify-center gap-2 rounded-xl px-6 py-3 text-sm font-bold text-white shadow-lg hover:opacity-90 hover:-translate-y-0.5 transition-all duration-200";
    }

    // 4. Input (Viền xanh)
    if (domRefs.chatInput) {
        domRefs.chatInput.className = "w-full resize-none rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 placeholder-slate-400 focus:border-emerald-500 focus:ring-4 focus:ring-emerald-100 focus:outline-none transition-all";
    }

    // 5. Khung Chat
    if (domRefs.card) {
        domRefs.card.className = "w-full max-w-6xl bg-white shadow-2xl rounded-3xl border border-white/50 flex flex-col lg:flex-row overflow-hidden";
        domRefs.card.style.height = "85vh"; 
    }

    // 6. Nút Đăng xuất
    if (domRefs.logoutBtn) {
        domRefs.logoutBtn.className = "absolute top-5 right-6 bg-white text-emerald-700 text-xs font-bold px-4 py-2 rounded-full shadow-sm hover:shadow-md hover:bg-emerald-50 transition-all z-50 border border-emerald-100";
    }

    // 7. Nút Feedback
    if (domRefs.feedbackSubmit) {
        domRefs.feedbackSubmit.style.backgroundColor = cfg.primary_action_color;
        domRefs.feedbackSubmit.className = "w-full rounded-lg px-4 py-2.5 text-xs font-bold text-white shadow-md hover:opacity-90 transition-colors mt-2";
    }
    
    // Đổi màu icon thông báo bên phải
    const infoIcon = document.querySelector("aside h3 span.rounded-full");
    if(infoIcon) {
        infoIcon.style.backgroundColor = cfg.primary_action_color;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    onConfigChange(defaultConfig);
});

// Logic Feedback (Giữ nguyên)
const feedbackForm = document.getElementById("feedback-form");
const feedbackStatus = document.getElementById("feedback-status");
const feedbackSubmit = document.getElementById("feedback-submit");

if (feedbackForm) {
    feedbackForm.addEventListener("submit", async function (e) {
        e.preventDefault();
        const message = document.getElementById("feedback-message").value.trim();
        if (!message) return;
        feedbackSubmit.disabled = true;
        feedbackSubmit.textContent = "Đang gửi...";
        setTimeout(() => {
            feedbackSubmit.disabled = false;
            feedbackSubmit.textContent = defaultConfig.feedback_submit_text;
            feedbackForm.reset();
            feedbackStatus.textContent = "Cảm ơn đóng góp của bạn!";
            feedbackStatus.style.color = brandColor;
            setTimeout(() => feedbackStatus.textContent = "", 3000);
        }, 1000);
    });
}