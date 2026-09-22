import streamlit as st
import streamlit.components.v1 as components
import json
import os
import io
import base64
import html
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from PIL import Image

# ============================================================
# CONFIG - ithe tumche 2 secret codes ani names set kara
# ============================================================
ACCESS_CODES = {
    "khadus": "Khadus",     # tumcha code + naav
    "pagal": "pagal",     # tumcha friend cha code + naav
}

CHAT_FILE = "chat_data.json"
REFRESH_MS = 3000  # dar 3 sec la naveen messages check honar
MAX_IMG_WIDTH = 900  # photo compress karnyasathi

st.set_page_config(page_title="System Status", page_icon="🔧", layout="centered")


# ------------------------------------------------------------
# Helper functions - message store (simple JSON file) [LOGIC UNCHANGED]
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


def compress_image(uploaded_file, max_width=MAX_IMG_WIDTH, quality=72):
    """Photo cha size kami karun base64 madhe convert karto, jya mule JSON file
    fugat nahi ani chat fast rahto."""
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
# Session state init [LOGIC UNCHANGED]
# ------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None


# ============================================================
# GATE PAGE - code na takta koni link ughadli tar he distay
# [AUTH LOGIC UNCHANGED - fakt styling professional keli]
# ============================================================
if not st.session_state.authenticated:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        #MainMenu, footer, header {visibility: hidden;}
        .block-container { padding-top: 4rem; max-width: 480px; }
        .gate-icon { font-size: 42px; text-align: center; margin-bottom: 4px; }
        .gate-title { text-align: center; font-size: 22px; font-weight: 600; color: #2c2c2c; }
        .gate-sub { text-align: center; color: #8a8a8a; font-size: 14px; margin-bottom: 22px; }
        @media (max-width: 480px) {
            .block-container { padding-left: 1.2rem; padding-right: 1.2rem; }
        }
        </style>
        <div class="gate-icon">🔧</div>
        <div class="gate-title">System Status</div>
        <div class="gate-sub">This service is currently undergoing scheduled maintenance.<br>
        Please check back later, or enter your access token below if provided.</div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("gate_form", clear_on_submit=True):
        code = st.text_input(
            "Access token",
            type="password",
            label_visibility="collapsed",
            placeholder="Access token",
        )
        submitted = st.form_submit_button("Verify", use_container_width=True)

    if submitted:
        if code in ACCESS_CODES:
            st.session_state.authenticated = True
            st.session_state.username = ACCESS_CODES[code]
            st.rerun()
        else:
            st.error("Invalid or expired token.")

    st.stop()


# ============================================================
# CHAT PAGE - fakt correct code takla tarch ithe yenar
# [AUTH / REFRESH / STORAGE LOGIC UNCHANGED - UI professional + photo add keli]
# ============================================================
st_autorefresh(interval=REFRESH_MS, key="chat_refresh")

me = st.session_state.username
other = [n for n in ACCESS_CODES.values() if n != me][0]
avatar_letter = other[0].upper()

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
    #MainMenu, footer, header {{visibility: hidden;}}
    .block-container {{ padding-top: 1rem; padding-bottom: 1rem; max-width: 640px; }}
    :root {{ --bar-size: 42px; --bar-icon: 20px; }}
    @media (min-width: 480px) {{ :root {{ --bar-size: 46px; --bar-icon: 21px; }} }}
    @media (min-width: 900px) {{
        :root {{ --bar-size: 52px; --bar-icon: 23px; }}
        .block-container {{ max-width: 760px; }}
    }}

    /* ---- header bar (WhatsApp style) ---- */
    .chat-header {{
        display: flex;
        align-items: center;
        gap: 12px;
        background: linear-gradient(135deg, #075E54, #128C7E);
        padding: 12px 16px;
        border-radius: 14px 14px 0 0;
        color: white;
    }}
    .chat-avatar {{
        width: 42px; height: 42px;
        border-radius: 50%;
        background: #ffffff33;
        display: flex; align-items: center; justify-content: center;
        font-weight: 600; font-size: 18px;
        flex-shrink: 0;
    }}
    .chat-header-name {{ font-weight: 600; font-size: 16px; line-height: 1.1; }}
    .chat-header-sub {{ font-size: 12px; opacity: 0.85; }}

    /* ---- chat window (WhatsApp doodle background) ---- */
    .chat-window {{
        background-color: #E5DDD5;
        background-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220' viewBox='0 0 220 220'%3E%3Cg fill='none' stroke='%23000000' stroke-opacity='0.045' stroke-width='2'%3E%3Cpath d='M20 30c8-10 20-10 28 0s6 22-2 28-24 2-30-8-4-14 4-20z'/%3E%3Ccircle cx='120' cy='40' r='14'/%3E%3Cpath d='M100 50l16 16M116 50l-16 16'/%3E%3Cpath d='M170 25c10 4 14 16 8 26s-20 12-28 4'/%3E%3Cpath d='M30 110h30M45 95v30'/%3E%3Ccircle cx='110' cy='120' r='10'/%3E%3Cpath d='M160 100c6 12-2 26-16 28s-24-8-22-20 14-20 24-16 12 6 14 8z'/%3E%3Cpath d='M40 170c6-8 18-8 24 2s0 20-10 22-20-4-20-14 2-8 6-10z'/%3E%3Cpath d='M120 175l14 14M134 175l-14 14'/%3E%3Ccircle cx='185' cy='165' r='12'/%3E%3Cpath d='M0 60h14M7 53v14'/%3E%3Cpath d='M200 60h14M207 53v14'/%3E%3Cpath d='M0 190h14M7 183v14'/%3E%3Cpath d='M200 190h14M207 183v14'/%3E%3C/g%3E%3C/svg%3E");
        background-repeat: repeat;
        background-size: 220px 220px;
        padding: 16px;
        border-radius: 0 0 14px 14px;
        min-height: 62vh;
        height: 62vh;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
    }}
    @media (max-width: 600px) {{
        .chat-window {{ min-height: 68vh; height: 68vh; }}
    }}
    .chat-row {{ display: flex; flex-direction: column; margin-bottom: 2px; }}
    .chat-bubble-me {{
        background-color: #DCF8C6;
        padding: 8px 12px;
        border-radius: 14px 14px 2px 14px;
        margin: 3px 0;
        max-width: 75%;
        align-self: flex-end;
        width: fit-content;
        word-wrap: break-word;
        box-shadow: 0 1px 1px rgba(0,0,0,0.08);
        font-size: 14.5px;
    }}
    .chat-bubble-other {{
        background-color: #FFFFFF;
        padding: 8px 12px;
        border-radius: 14px 14px 14px 2px;
        margin: 3px 0;
        max-width: 75%;
        align-self: flex-start;
        width: fit-content;
        word-wrap: break-word;
        box-shadow: 0 1px 1px rgba(0,0,0,0.08);
        font-size: 14.5px;
    }}
    .chat-bubble-me img, .chat-bubble-other img {{
        max-width: 100%;
        border-radius: 10px;
        display: block;
        margin-bottom: 4px;
    }}
    .msg-time {{
        font-size: 10px;
        color: #8a8a8a;
        margin-top: 2px;
        text-align: right;
    }}

    /* ---- responsive tweaks for phones ---- */
    @media (max-width: 600px) {{
        .block-container {{ padding-left: 0.6rem; padding-right: 0.6rem; }}
        .chat-bubble-me, .chat-bubble-other {{ max-width: 88%; font-size: 14px; }}
        .chat-header {{ padding: 10px 12px; }}
    }}

    /* ---- everything in the send-form: safe box model, no overflow ---- */
    div[data-testid="stForm"], div[data-testid="stForm"] * {{
        box-sizing: border-box !important;
    }}
    div[data-testid="stForm"] {{
        width: 100% !important;
        overflow: hidden !important;
        padding: 8px !important;
    }}
    div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] {{
        display: flex !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        width: 100% !important;
        gap: 6px !important;
    }}
    /* attach (col 1) and send (col 3): size to their fixed-size child only, never shrink/grow */
    div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(1),
    div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(3) {{
        flex: 0 0 auto !important;
        width: auto !important;
        min-width: 0 !important;
        padding: 0 !important;
    }}
    /* textbox (col 2): takes remaining space, allowed to shrink so the row never overflows */
    div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(2) {{
        flex: 1 1 auto !important;
        min-width: 0 !important;
        padding: 0 !important;
    }}

    /* ---- WhatsApp-style attach icon: real SVG paperclip, same on every device ---- */
    [data-testid="stFileUploader"] {{ width: var(--bar-size) !important; }}
    [data-testid="stFileUploader"] section {{
        padding: 0 !important;
        border: none !important;
        background: transparent !important;
    }}
    [data-testid="stFileUploaderDropzoneInstructions"] {{ display: none !important; }}
    [data-testid="stFileUploaderDropzone"] svg {{ display: none !important; }}
    [data-testid="stFileUploaderDropzone"] {{
        position: relative !important;
        width: var(--bar-size) !important;
        height: var(--bar-size) !important;
        min-height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
        border-radius: 50% !important;
        background-color: transparent !important;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2354656F' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21.44 11.05l-9.19 9.19a5.5 5.5 0 0 1-7.78-7.78l9.19-9.19a3.5 3.5 0 0 1 4.95 4.95l-9.2 9.19a1.5 1.5 0 0 1-2.12-2.12l8.49-8.48'/%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        background-size: var(--bar-icon) var(--bar-icon) !important;
        overflow: hidden !important;
    }}
    [data-testid="stFileUploaderDropzone"]:hover {{ background-color: #00000010 !important; }}
    [data-testid="stFileUploaderDropzone"] button {{
        position: absolute !important;
        inset: 0 !important;
        width: 100% !important;
        height: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
        opacity: 0 !important;
        cursor: pointer !important;
        z-index: 2 !important;
    }}
    /* once a file is picked, keep the little file-chip from stretching the row */
    [data-testid="stFileUploaderFile"] {{
        font-size: 0 !important;
        max-width: var(--bar-size) !important;
        padding: 0 !important;
    }}

    /* ---- send button: real SVG paper-plane on a WhatsApp-green circle ---- */
    div[data-testid="stForm"] button[kind="formSubmit"] {{
        border-radius: 50% !important;
        width: var(--bar-size) !important;
        height: var(--bar-size) !important;
        min-width: var(--bar-size) !important;
        padding: 0 !important;
        margin: 0 !important;
        background-color: #25D366 !important;
        border: none !important;
        font-size: 0 !important;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E%3Cpath d='M2 21l21-9L2 3v7l15 2-15 2z'/%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        background-size: var(--bar-icon) var(--bar-icon) !important;
    }}

    /* rounder text input like WhatsApp's message bar, height matches the icons */
    div[data-testid="stForm"] input[type="text"] {{
        border-radius: 20px !important;
        height: var(--bar-size) !important;
        padding: 0 14px !important;
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

chat_html = "<div class='chat-window' id='chat-window-box'>"
for msg in messages:
    bubble_class = "chat-bubble-me" if msg["sender"] == me else "chat-bubble-other"

    if msg.get("type") == "image" and msg.get("data"):
        caption = html.escape(msg.get("text", "")) if msg.get("text") else ""
        caption_html = f"<div>{caption}</div>" if caption else ""
        content = (
            f"<img src='data:{msg.get('mime','image/jpeg')};base64,{msg['data']}' />"
            f"{caption_html}"
        )
    else:
        content = html.escape(msg.get("text", ""))

    chat_html += (
        "<div class='chat-row'>"
        f"<div class='{bubble_class}'>{content}"
        f"<div class='msg-time'>{msg['time']}</div>"
        "</div></div>"
    )
chat_html += "</div>"

st.markdown(chat_html, unsafe_allow_html=True)

# auto-scroll to the latest message
components.html(
    """
    <script>
        try {
            const doc = window.parent.document;
            const box = doc.getElementById('chat-window-box');
            if (box) { box.scrollTop = box.scrollHeight; }
        } catch (e) {}
    </script>
    """,
    height=0,
)

# ------------------------------------------------------------
# Message input box [SEND FORM LOGIC SAME IDEA, photo path added]
# ------------------------------------------------------------
with st.form("send_form", clear_on_submit=True):
    col1, col2, col3 = st.columns([1, 5, 1])
    with col1:
        photo = st.file_uploader(
            "🐭",
            type=["png", "jpg", "jpeg", "gif", "webp"],
            label_visibility="collapsed",
            key="photo_uploader",
        )
    with col2:
        new_msg = st.text_input(
            "Type a message",
            label_visibility="collapsed",
            placeholder="Type a message...",
        )
    with col3:
        send = st.form_submit_button("➤", use_container_width=True)

if send:
    if photo is not None:
        b64data, mime = compress_image(photo)
        save_message(me, msg_type="image", data=b64data, mime=mime, text=new_msg.strip())
        st.rerun()
    elif new_msg.strip():
        save_message(me, msg_type="text", text=new_msg.strip())
        st.rerun()

# Logout
if st.button("Log out", key="logout"):
    st.session_state.authenticated = False
    st.session_state.username = None
    st.rerun()