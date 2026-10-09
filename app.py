import streamlit as st
import streamlit.components.v1 as components
import json
import os
import io
import base64
import html
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from PIL import Image

# ============================================================
# CONFIG
# ============================================================
ACCESS_CODES = {
    "baby": "Khadus",
    "pagal": "pagal",
}

CHAT_FILE = "chat_data.json"
TYPING_FILE = "typing_status.json"
REFRESH_MS = 3000
MAX_IMG_WIDTH = 900

st.set_page_config(page_title="System Status", page_icon="🔧", layout="wide", initial_sidebar_state="collapsed")

# ------------------------------------------------------------
# Helper functions - Messaging & Typing Logic
# ------------------------------------------------------------
def load_messages():
    if os.path.exists(CHAT_FILE):
        try:
            with open(CHAT_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            return []
    return []

def save_message(sender, msg_type="text", text=None, data=None, mime=None):
    messages = load_messages()
    entry = {
        "sender": sender,
        "type": msg_type,
        "time": datetime.now().strftime("%H:%M"),
    }
    if text:
        entry["text"] = text
    if msg_type == "image":
        entry["data"] = data
        entry["mime"] = mime
    messages.append(entry)
    with open(CHAT_FILE, "w") as f:
        json.dump(messages, f)

def load_typing_status():
    if os.path.exists(TYPING_FILE):
        try:
            with open(TYPING_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            return {}
    return {}

def save_typing_status(username, is_typing):
    status = load_typing_status()
    if is_typing:
        status[username] = time.time()
    else:
        status.pop(username, None)
    with open(TYPING_FILE, "w") as f:
        json.dump(status, f)

def is_user_typing(username):
    status = load_typing_status()
    last_time = status.get(username)
    if not last_time:
        return False
    if time.time() - last_time > 5:
        status.pop(username, None)
        with open(TYPING_FILE, "w") as f:
            json.dump(status, f)
        return False
    return True

def compress_image(uploaded_file, max_width=MAX_IMG_WIDTH, quality=72):
    img = Image.open(uploaded_file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    if img.width > max_width:
        ratio = max_width / float(img.width)
        img = img.resize((max_width, int(img.height * ratio)))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return base64.b64encode(buf.getvalue()).decode(), "image/jpeg"

# ------------------------------------------------------------
# Session state
# ------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None

# ============================================================
# GATE PAGE
# ============================================================
if not st.session_state.authenticated:
    st.markdown(
        """
        <style>
        * { box-sizing: border-box; }
        html, body, [class*="css"], button, input { font-family: Inter, sans-serif; }
        #MainMenu, header, footer { visibility: hidden; }
        .stApp { background: #f5f7f8; }
        .block-container { width: min(100% - 28px, 460px); margin: 0 auto; padding: 4rem 0 2rem !important; }
        .gate-icon { font-size: 42px; text-align: center; margin-bottom: 5px; }
        .gate-title { text-align: center; font-size: 25px; font-weight: 700; color: #202124; }
        .gate-sub { text-align: center; color: #74777a; font-size: 14px; margin-bottom: 22px; }
        div[data-testid="stForm"] { border-radius: 16px !important; padding: 14px !important; background: white !important; box-shadow: 0 10px 28px rgba(0,0,0,.07) !important; border: 1px solid rgba(0,0,0,.1) !important;}
        </style>
        <div class="gate-icon">🔧</div>
        <div class="gate-title">System Status</div>
        <div class="gate-sub">Maintenance mode. Enter access token.</div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("gate_form", clear_on_submit=True):
        code = st.text_input("Access token", type="password", label_visibility="collapsed", placeholder="Access token")
        submitted = st.form_submit_button("Verify", use_container_width=True)
    if submitted:
        if code in ACCESS_CODES:
            st.session_state.authenticated = True
            st.session_state.username = ACCESS_CODES[code]
            st.rerun()
        else:
            st.error("Invalid token.")
    st.stop()

# ============================================================
# CHAT PAGE
# ============================================================
st_autorefresh(interval=REFRESH_MS, key="chat_refresh")

me = st.session_state.username
other = [n for n in ACCESS_CODES.values() if n != me][0]
avatar_letter = other[0].upper()
typing_now = is_user_typing(other)

def update_typing_status():
    text = st.session_state.get("message_input", "").strip()
    save_typing_status(me, bool(text))

st.markdown(
    f"""
    <style>
    * {{ box-sizing: border-box !important; }}
    html, body, [class*="css"], button, input, textarea {{ font-family: Inter, sans-serif !important; }}
    #MainMenu, header, footer {{ visibility: hidden !important; }}
    .stApp {{ min-height: 100dvh !important; background: #f5f7f8 !important; }}
    .block-container {{ width: min(100%, 980px) !important; margin: 0 auto !important; padding: 12px 12px 18px !important; }}

    .chat-header {{
        width: 100% !important; min-height: 74px; display: flex; align-items: center; gap: 13px; padding: 12px 17px;
        color: #ffffff; background: linear-gradient(135deg, #075E54 0%, #128C7E 100%);
        border-radius: 18px 18px 0 0; box-shadow: 0 5px 18px rgba(0,0,0,.10);
    }}
    .chat-avatar {{ width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,.18); font-weight: 700; }}
    .chat-header-name {{ font-size: 20px; font-weight: 700; }}
    .chat-header-sub {{ font-size: 12px; opacity: .84; }}

    .chat-window {{
        position: relative !important; isolation: isolate; width: 100% !important; height: min(calc(100dvh - 205px), 690px);
        min-height: 360px; overflow-x: hidden !important; overflow-y: auto !important;
        display: flex; flex-direction: column; padding: 16px; background-color: #efe7df; border-radius: 0 0 18px 18px;
    }}

    .chat-window::before {{
        content: ""; position: absolute; inset: 0; z-index: -2; pointer-events: none;
        background: linear-gradient(rgba(239, 231, 223, 0.86), rgba(239, 231, 223, 0.86)),
        url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220' viewBox='0 0 220 220'%3E%3Cg fill='none' stroke='%23000000' stroke-opacity='0.045' stroke-width='2'%3E%3Ccircle cx='58' cy='54' r='29'/%3E%3Cpath d='M38 77l40 40M78 77l-40 40'/%3E%3C/g%3E%3C/svg%3E");
        background-repeat: repeat; background-size: 220px 220px;
    }}

    .love-credits {{
        position: absolute; inset: 0; z-index: -1; overflow: hidden; pointer-events: none;
        display: flex; flex-direction: column; align-items: center; justify-content: flex-end;
        text-align: center; color: rgba(170, 35, 72, 0.15); font-size: clamp(24px, 4vw, 46px);
        font-weight: 800; line-height: 1.8; animation: loveCreditsScroll 22s linear infinite;
    }}
    .love-credits div {{ margin: 24px 0; }}

    @keyframes loveCreditsScroll {{
        0% {{ transform: translateY(110%); }}
        100% {{ transform: translateY(-150%); }}
    }}

    .chat-row {{ width: 100%; display: flex; flex-direction: column; margin-bottom: 2px; }}
    .chat-bubble-me, .chat-bubble-other {{
        width: fit-content; max-width: 76%; padding: 9px 12px; margin: 3px 0; border-radius: 14px;
        font-size: 14.5px; word-break: break-word; box-shadow: 0 1px 2px rgba(0,0,0,.10);
    }}
    .chat-bubble-me {{ align-self: flex-end; background: #DCF8C6; border-bottom-right-radius: 3px; }}
    .chat-bubble-other {{ align-self: flex-start; background: #FFFFFF; border-bottom-left-radius: 3px; }}
    .msg-time {{ margin-top: 4px; text-align: right; font-size: 10px; color: #777; }}

    .typing-row {{ width: 100%; display: flex; justify-content: flex-start; margin-top: 5px; }}
    .typing-indicator {{ display: flex; align-items: center; gap: 4px; padding: 9px 12px; border-radius: 14px; border-bottom-left-radius: 3px; background: #ffffff; box-shadow: 0 1px 2px rgba(0,0,0,.1); }}
    .typing-indicator span {{ width: 6px; height: 6px; border-radius: 50%; background: #777; animation: typingDots 1.2s infinite ease-in-out; }}
    .typing-indicator span:nth-child(2) {{ animation-delay: .15s; }}
    .typing-indicator span:nth-child(3) {{ animation-delay: .3s; }}
    .typing-indicator b {{ margin-left: 5px; color: #777; font-size: 11px; }}

    @keyframes typingDots {{
        0%, 60%, 100% {{ transform: translateY(0); opacity: .45; }}
        30% {{ transform: translateY(-4px); opacity: 1; }}
    }}

    div[data-testid="stForm"] {{ border-radius: 18px !important; background: white !important; box-shadow: 0 6px 18px rgba(0,0,0,.08) !important; border: 1px solid rgba(0,0,0,.13) !important; padding: 5px !important; }}
    div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] {{ display: grid !important; grid-template-columns: 44px 1fr 44px !important; gap: 6px !important; align-items: center !important; }}
    div[data-testid="stForm"] input[type="text"] {{ border-radius: 23px !important; height: 44px !important; }}
    div[data-testid="stForm"] button[kind="formSubmit"] {{ border-radius: 50% !important; background: #25D366 !important; width: 44px !important; height: 44px !important; color: transparent !important; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E%3Cpath d='M2 21l21-9L2 3v7l15 2-15 2z'/%3E%3C/svg%3E") !important; background-repeat: no-repeat !important; background-position: center !important; background-size: 19px !important; }}
    
    @media (prefers-color-scheme: dark) {{
        .stApp {{ background: #101514 !important; }}
        .chat-window::before {{ background: linear-gradient(rgba(32, 38, 36, 0.90), rgba(32, 38, 36, 0.90)); }}
        .love-credits {{ color: rgba(255, 120, 160, 0.18); }}
        .chat-bubble-other {{ background: #2B302F; color: #f4f5f4; }}
        .chat-bubble-me {{ background: #145c43; color: #ffffff; }}
        .typing-indicator {{ background: #2b302f; }}
        .typing-indicator span, .typing-indicator b {{ background: #b8bfbd; color: #b8bfbd; }}
    }}
    </style>

    <div class="chat-header">
        <div class="chat-avatar">{avatar_letter}</div>
        <div>
            <div class="chat-header-name">{other}</div>
            <div class="chat-header-sub">private chat</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

messages = load_messages()
chat_html = """<div class='chat-window' id='chat-window-box'>
    <div class='love-credits'>
        <div>I Love You Cheshmesh ❤️❤️</div>
        <div>Forever & Always 💕</div>
        <div>Our Little Private World ✨</div>
    </div>"""

for msg in messages:
    bubble_class = "chat-bubble-me" if msg["sender"] == me else "chat-bubble-other"
    if msg.get("type") == "image":
        content = f"<img src='data:{msg.get('mime')};base64,{msg['data']}' style='max-width:100%;border-radius:10px'/><br>{html.escape(msg.get('text', ''))}"
    else:
        content = html.escape(msg.get("text", ""))
    chat_html += f"<div class='chat-row'><div class='{bubble_class}'>{content}<div class='msg-time'>{msg['time']}</div></div></div>"

if typing_now:
    chat_html += """<div class="typing-row"><div class="typing-indicator"><span></span><span></span><span></span><b>typing...</b></div></div>"""
chat_html += "</div>"
st.markdown(chat_html, unsafe_allow_html=True)

# Auto-scroll component
components.html("<script>window.parent.document.getElementById('chat-window-box').scrollTop = 999999;</script>", height=0)

with st.form("send_form", clear_on_submit=True):
    col1, col2, col3 = st.columns([1, 5, 1])
    with col1:
        photo = st.file_uploader("img", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    with col2:
        new_msg = st.text_input("msg", label_visibility="collapsed", placeholder="Type a message...", key="message_input", on_change=update_typing_status)
    with col3:
        send = st.form_submit_button("S")

if send:
    save_typing_status(me, False)
    if photo:
        b64, mime = compress_image(photo)
        save_message(me, "image", text=new_msg.strip(), data=b64, mime=mime)
        st.rerun()
    elif new_msg.strip():
        save_message(me, "text", text=new_msg.strip())
        st.rerun()

if st.button("Log out"):
    st.session_state.authenticated = False
    st.rerun()
