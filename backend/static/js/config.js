// File: backend/static/js/config.js
// Logic cấu hình và cập nhật UI (Demo)

const defaultConfig = {
    background_color: "#0ea5e9",
    surface_color: "#ffffff",
    text_color: "#0f172a",
    primary_action_color: "#0284c7",
    secondary_action_color: "#0369a1",
    font_family: "system-ui",
    font_size: 14,
    app_title: "Hỗ trợ Học tập",
    app_subtitle: "Chatbot tư vấn chương trình đào tạo & thông tin nhà trường",
    chatbox_title: "Trợ lý ảo Hỗ trợ Học tập",
    chatbox_placeholder: "Nhập câu hỏi...",
    feedback_title: "Góp ý về trải nghiệm chatbox",
    feedback_submit_text: "Gửi phản hồi"
};

const domRefs = {
    body: document.body,
    mainWrapper: document.querySelector(".app-wrapper"),
    card: document.querySelector("main > section"),
    chatHeader: document.getElementById("chat-header"),
    chatboxTitle: document.getElementById("chatbox-title"),
    sendButton: document.getElementById("send-button"),
    feedbackTitle: document.getElementById("feedback-title"),
    feedbackSubmit: document.getElementById("feedback-submit"),
    header: document.querySelector("header"),
    footerSubtitle: document.getElementById("app-subtitle-footer"),
    chatInput: document.getElementById("chat-input")
};

async function onConfigChange(config) {
    const cfg = config || defaultConfig;
    const bg = cfg.background_color || defaultConfig.background_color;
    const surface = cfg.surface_color || defaultConfig.surface_color;
    const txt = cfg.text_color || defaultConfig.text_color;
    const primary = cfg.primary_action_color || defaultConfig.primary_action_color;
    const secondary = cfg.secondary_action_color || defaultConfig.secondary_action_color;
    const fontFamily = cfg.font_family || defaultConfig.font_family;
    const baseFontSize = Number(cfg.font_size) || defaultConfig.font_size;
    const fontStack = `${fontFamily}, system-ui, -apple-system, sans-serif`;

    domRefs.body.style.background = bg;
    domRefs.mainWrapper.style.background = "transparent";
    domRefs.card.style.backgroundColor = surface;
    domRefs.card.style.color = txt;

    const headerEl = domRefs.header;
    headerEl.innerHTML = "";
    
    const headerInner = document.createElement("div");
    headerInner.className = "w-full max-w-6xl mx-auto px-4 pt-4 pb-1 flex items-center justify-between gap-3";
    
    const titleBlock = document.createElement("div");
    titleBlock.className = "flex items-center gap-3";
    
    const iconWrap = document.createElement("div");
    iconWrap.className = "w-9 h-9 rounded-full flex items-center justify-center text-white";
    iconWrap.style.backgroundColor = secondary;
    iconWrap.innerHTML = `<svg viewBox="0 0 24 24" fill="none" class="w-5 h-5"><path d="M4 5a2 2 0 0 1 2-2h8.5a2 2 0 0 1 1.6.8l3.5 4.667a2 2 0 0 1 .4 1.2V19a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5Z" fill="currentColor"/></svg>`;

    const textWrap = document.createElement("div");
    const h1 = document.createElement("h1");
    h1.textContent = cfg.app_title || defaultConfig.app_title;
    h1.className = "font-semibold tracking-tight";
    h1.style.color = "#f9fafb";
    h1.style.fontSize = (baseFontSize * 1.6) + "px";
    
    const pSub = document.createElement("p");
    pSub.textContent = cfg.app_subtitle || defaultConfig.app_subtitle;
    pSub.className = "opacity-90";
    pSub.style.color = "#e5f2ff";
    pSub.style.fontSize = (baseFontSize * 0.9) + "px";

    textWrap.appendChild(h1);
    textWrap.appendChild(pSub);
    titleBlock.appendChild(iconWrap);
    titleBlock.appendChild(textWrap);
    headerInner.appendChild(titleBlock);
    headerEl.appendChild(headerInner);
    
    headerEl.style.background = `linear-gradient(135deg, ${bg}, ${secondary})`;
    headerEl.style.borderBottom = "1px solid rgba(15,23,42,0.05)";

    if (domRefs.chatboxTitle) domRefs.chatboxTitle.textContent = cfg.chatbox_title || defaultConfig.chatbox_title;
    if (domRefs.chatInput) domRefs.chatInput.placeholder = cfg.chatbox_placeholder || defaultConfig.chatbox_placeholder;
    if (domRefs.sendButton) domRefs.sendButton.style.backgroundColor = primary;
    if (domRefs.feedbackTitle) domRefs.feedbackTitle.textContent = cfg.feedback_title || defaultConfig.feedback_title;
    if (domRefs.feedbackSubmit) domRefs.feedbackSubmit.textContent = cfg.feedback_submit_text || defaultConfig.feedback_submit_text;
    if (domRefs.feedbackSubmit) domRefs.feedbackSubmit.style.backgroundColor = primary;
    
    domRefs.body.style.fontFamily = fontStack;
    domRefs.body.style.fontSize = baseFontSize + "px";
}

document.addEventListener("DOMContentLoaded", () => {
    onConfigChange(defaultConfig);
});

const feedbackForm = document.getElementById("feedback-form");
const feedbackStatus = document.getElementById("feedback-status");
const feedbackSubmit = document.getElementById("feedback-submit");

if (feedbackForm) {
    feedbackForm.addEventListener("submit", async function (e) {
        e.preventDefault();
        const name = document.getElementById("feedback-name").value.trim();
        const type = document.getElementById("feedback-type").value;
        const message = document.getElementById("feedback-message").value.trim();

        if (!message) {
            feedbackStatus.textContent = "Vui lòng nhập nội dung.";
            feedbackStatus.style.color = "#b91c1c";
            return;
        }

        feedbackSubmit.disabled = true;
        feedbackStatus.textContent = "Đang gửi...";
        feedbackStatus.style.color = "#6b7280";

        try {
            const response = await fetch('/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, type, message })
            });

            const data = await response.json();

            if (data.status === 'success') {
                feedbackStatus.textContent = "Đã gửi thành công. Cảm ơn bạn!";
                feedbackStatus.style.color = "#15803d";
                feedbackForm.reset();
            } else {
                feedbackStatus.textContent = data.message || "Lỗi server khi gửi phản hồi.";
                feedbackStatus.style.color = "#b91c1c";
            }
        } catch (error) {
            feedbackStatus.textContent = "Lỗi kết nối mạng.";
            feedbackStatus.style.color = "#b91c1c";
        } finally {
            feedbackSubmit.disabled = false;
        }
    });
}