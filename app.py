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

st.set_page_config(page_title="System Status", page_icon="🔧", layout="wide", initial_sidebar_state="collapsed")


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
        * { box-sizing: border-box; }
        html, body, [class*="css"], button, input { font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
        #MainMenu, header, footer { visibility: hidden; }

        .stApp {
            background: #f5f7f8;
        }

        .block-container {
            width: min(100% - 28px, 460px);
            margin: 0 auto;
            padding: 4rem 0 2rem !important;
        }

        .gate-icon {
            font-size: 42px;
            text-align: center;
            margin-bottom: 5px;
        }

        .gate-title {
            text-align: center;
            font-size: clamp(21px, 5vw, 25px);
            font-weight: 700;
            color: #202124;
        }

        .gate-sub {
            text-align: center;
            color: #74777a;
            font-size: 14px;
            line-height: 1.55;
            margin: 0 auto 22px;
            max-width: 420px;
        }

        div[data-testid="stForm"] {
            border: 1px solid rgba(0,0,0,.10) !important;
            border-radius: 16px !important;
            padding: 14px !important;
            background: rgba(255,255,255,.96) !important;
            box-shadow: 0 10px 28px rgba(0,0,0,.07) !important;
        }

        @media (max-width: 480px) {
            .block-container {
                width: calc(100% - 22px);
                padding-top: 2.6rem !important;
            }
        }

        @media (prefers-color-scheme: dark) {
            .stApp { background: #101514; }
            .gate-title { color: #f3f5f4; }
            .gate-sub { color: #aeb6b3; }
            div[data-testid="stForm"] {
                background: #1a201f !important;
                border-color: rgba(255,255,255,.10) !important;
            }
        }
        </style>

        <div class="gate-icon">🔧</div>
        <div class="gate-title">System Status</div>
        <div class="gate-sub">
            This service is currently undergoing scheduled maintenance.<br>
            Please check back later, or enter your access token below if provided.
        </div>
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
    /* ==========================================================
       SYSTEM STATUS — RESPONSIVE CHAT UI
       ========================================================== */
    * {{ box-sizing: border-box !important; }}

    html, body, [class*="css"], button, input, textarea {{
        font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
    }}

    #MainMenu, header, footer {{
        visibility: hidden !important;
    }}

    .stApp {{
        min-height: 100dvh !important;
        background: #f5f7f8 !important;
    }}

    .block-container {{
        width: min(100%, 980px) !important;
        max-width: 980px !important;
        margin: 0 auto !important;
        padding: 12px 12px 18px !important;
    }}

    /* Prevent any Streamlit child from creating horizontal overflow. */
    .block-container > div,
    .block-container [data-testid="stVerticalBlock"],
    .block-container [data-testid="stHorizontalBlock"] {{
        min-width: 0 !important;
        max-width: 100% !important;
    }}

    /* ==========================================================
       HEADER
       ========================================================== */
    .chat-header {{
        width: 100% !important;
        min-height: 74px;
        display: flex;
        align-items: center;
        gap: 13px;
        padding: 12px 17px;
        color: #ffffff;
        background: linear-gradient(135deg, #075E54 0%, #128C7E 100%);
        border-radius: 18px 18px 0 0;
        box-shadow: 0 5px 18px rgba(0,0,0,.10);
    }}

    .chat-avatar {{
        width: 48px;
        height: 48px;
        min-width: 48px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(255,255,255,.18);
        border: 1px solid rgba(255,255,255,.16);
        font-size: 20px;
        font-weight: 700;
    }}

    .chat-header-name {{
        font-size: clamp(16px, 2.1vw, 20px);
        line-height: 1.15;
        font-weight: 700;
        letter-spacing: -.01em;
    }}

    .chat-header-sub {{
        margin-top: 4px;
        font-size: 12px;
        line-height: 1.1;
        opacity: .84;
    }}

    /* ==========================================================
       CHAT WINDOW
       ========================================================== */
    .chat-window {{
        width: 100% !important;
        height: min(calc(100dvh - 205px), 690px);
        min-height: 360px;
        overflow-x: hidden !important;
        overflow-y: auto !important;
        display: flex;
        flex-direction: column;
        padding: 16px;
        background-color: #efe7df;
        background-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220' viewBox='0 0 220 220'%3E%3Cg fill='none' stroke='%23000000' stroke-opacity='0.045' stroke-width='2'%3E%3Ccircle cx='58' cy='54' r='29'/%3E%3Cpath d='M38 77l40 40M78 77l-40 40'/%3E%3Cpath d='M128 35c12 14 12 33-1 45s-34 13-48 0'/%3E%3Ccircle cx='172' cy='55' r='26'/%3E%3Cpath d='M154 76l36 36M190 76l-36 36'/%3E%3Cpath d='M14 128h34M31 111v34'/%3E%3Ccircle cx='111' cy='145' r='14'/%3E%3Cpath d='M160 130h34M177 113v34'/%3E%3Ccircle cx='71' cy='185' r='11'/%3E%3Cpath d='M97 177c12 12 31 12 42 0s10-30-1-42'/%3E%3C/g%3E%3C/svg%3E");
        background-repeat: repeat;
        background-size: 220px 220px;
        border-radius: 0 0 18px 18px;
        box-shadow: inset 0 1px rgba(255,255,255,.25);
        overscroll-behavior: contain;
        -webkit-overflow-scrolling: touch;
    }}

    .chat-row {{
        width: 100%;
        display: flex;
        flex-direction: column;
        margin-bottom: 2px;
    }}

    .chat-bubble-me,
    .chat-bubble-other {{
        width: fit-content;
        max-width: min(76%, 560px);
        padding: 9px 12px;
        margin: 3px 0;
        border-radius: 14px;
        font-size: 14.5px;
        line-height: 1.38;
        word-break: break-word;
        overflow-wrap: anywhere;
        white-space: pre-wrap;
        box-shadow: 0 1px 2px rgba(0,0,0,.10);
    }}

    .chat-bubble-me {{
        align-self: flex-end;
        background: #DCF8C6;
        border-bottom-right-radius: 3px;
    }}

    .chat-bubble-other {{
        align-self: flex-start;
        background: #FFFFFF;
        border-bottom-left-radius: 3px;
    }}

    .chat-bubble-me img,
    .chat-bubble-other img {{
        display: block;
        width: auto;
        max-width: 100%;
        max-height: min(55dvh, 420px);
        object-fit: contain;
        border-radius: 10px;
        margin-bottom: 4px;
    }}

    .msg-time {{
        margin-top: 4px;
        text-align: right;
        font-size: 10px;
        line-height: 1;
        color: #777;
    }}

    /* ==========================================================
       COMPOSER — robust against changing Streamlit column DOM
       ========================================================== */
    div[data-testid="stForm"] {{
        width: 100% !important;
        max-width: 100% !important;
        margin: 10px 0 0 !important;
        padding: 5px !important;
        border: 1px solid rgba(0,0,0,.13) !important;
        border-radius: 18px !important;
        background: rgba(255,255,255,.98) !important;
        box-shadow: 0 6px 18px rgba(0,0,0,.08) !important;
        overflow: visible !important;
    }}

    div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] {{
        width: 100% !important;
        display: grid !important;
        grid-template-columns: 44px minmax(0, 1fr) 44px !important;
        gap: 6px !important;
        align-items: center !important;
        margin: 0 !important;
        padding: 0 !important;
    }}

    div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] > div,
    div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] > [data-testid="column"],
    div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
        flex: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }}

    div[data-testid="stForm"] [data-testid="stVerticalBlock"] {{
        gap: 0 !important;
    }}

    /* Hide Enter-to-submit helper text that appears underneath the input. */
    div[data-testid="stForm"] [data-testid="InputInstructions"],
    div[data-testid="stForm"] small {{
        display: none !important;
        visibility: hidden !important;
    }}

    /* ==========================================================
       ATTACHMENT
       ========================================================== */
    div[data-testid="stForm"] [data-testid="stFileUploader"] {{
        width: 44px !important;
        min-width: 44px !important;
        max-width: 44px !important;
        margin: 0 !important;
    }}

    div[data-testid="stForm"] [data-testid="stFileUploader"] section {{
        width: 44px !important;
        height: 44px !important;
        min-height: 44px !important;
        padding: 0 !important;
        margin: 0 !important;
        border: 0 !important;
        background: transparent !important;
    }}

    div[data-testid="stForm"] [data-testid="stFileUploaderDropzone"] {{
        position: relative !important;
        width: 44px !important;
        height: 44px !important;
        min-height: 44px !important;
        padding: 0 !important;
        margin: 0 !important;
        border: 0 !important;
        border-radius: 50% !important;
        background: transparent !important;
        overflow: hidden !important;
        cursor: pointer !important;
    }}

    div[data-testid="stForm"] [data-testid="stFileUploaderDropzone"]::before {{
        content: "📎";
        position: absolute;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        line-height: 1;
        pointer-events: none;
        z-index: 1;
    }}

    div[data-testid="stForm"] [data-testid="stFileUploaderDropzoneInstructions"],
    div[data-testid="stForm"] [data-testid="stFileUploaderFileName"],
    div[data-testid="stForm"] [data-testid="stFileUploaderFile"] {{
        display: none !important;
    }}

    div[data-testid="stForm"] [data-testid="stFileUploaderDropzone"] svg {{
        display: none !important;
    }}

    div[data-testid="stForm"] [data-testid="stFileUploaderDropzone"] button {{
        position: absolute !important;
        inset: 0 !important;
        z-index: 3 !important;
        width: 100% !important;
        height: 100% !important;
        min-height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        opacity: 0 !important;
        border: 0 !important;
        cursor: pointer !important;
    }}

    /* ==========================================================
       INPUT
       ========================================================== */
    div[data-testid="stForm"] input[type="text"] {{
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
        height: 44px !important;
        margin: 0 !important;
        padding: 0 15px !important;
        border-radius: 23px !important;
        font-size: 14px !important;
        line-height: 44px !important;
        box-sizing: border-box !important;
    }}

    /* ==========================================================
       SEND BUTTON
       ========================================================== */
    div[data-testid="stForm"] button[kind="formSubmit"] {{
        width: 44px !important;
        min-width: 44px !important;
        max-width: 44px !important;
        height: 44px !important;
        min-height: 44px !important;
        padding: 0 !important;
        margin: 0 !important;
        border: 0 !important;
        border-radius: 50% !important;
        font-size: 0 !important;
        line-height: 0 !important;
        background: #25D366 !important;
        color: transparent !important;
        box-shadow: 0 3px 9px rgba(37,211,102,.25) !important;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E%3Cpath d='M2 21l21-9L2 3v7l15 2-15 2z'/%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        background-size: 19px 19px !important;
    }}

    div[data-testid="stForm"] button[kind="formSubmit"]:hover {{
        transform: translateY(-1px);
        filter: brightness(.98);
    }}

    /* ==========================================================
       LOGOUT
       ========================================================== */
    div[data-testid="stButton"] button,
    button[data-testid="stBaseButton-secondary"] {{
        min-height: 40px !important;
        border-radius: 11px !important;
        margin-top: 8px !important;
    }}

    /* ==========================================================
       PHONE
       ========================================================== */
    @media (max-width: 600px) {{
        .stApp {{
            background: #f5f7f8 !important;
        }}

        .block-container {{
            width: 100% !important;
            max-width: 100% !important;
            padding: 6px 6px 12px !important;
        }}

        .chat-header {{
            min-height: 62px;
            padding: 8px 11px;
            gap: 10px;
            border-radius: 13px 13px 0 0;
        }}

        .chat-avatar {{
            width: 40px;
            height: 40px;
            min-width: 40px;
            font-size: 17px;
        }}

        .chat-header-name {{
            font-size: 16px;
        }}

        .chat-header-sub {{
            font-size: 11px;
        }}

        .chat-window {{
            height: calc(100dvh - 196px);
            min-height: 300px;
            padding: 10px;
            background-size: 190px 190px;
            border-radius: 0 0 13px 13px;
        }}

        .chat-bubble-me,
        .chat-bubble-other {{
            max-width: 88%;
            font-size: 13.5px;
            padding: 8px 10px;
        }}

        .chat-bubble-me img,
        .chat-bubble-other img {{
            max-height: 280px;
        }}

        div[data-testid="stForm"] {{
            margin-top: 7px !important;
            padding: 4px !important;
            border-radius: 15px !important;
        }}

        div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] {{
            grid-template-columns: 40px minmax(0, 1fr) 40px !important;
            gap: 4px !important;
        }}

        div[data-testid="stForm"] [data-testid="stFileUploader"],
        div[data-testid="stForm"] [data-testid="stFileUploader"] section,
        div[data-testid="stForm"] [data-testid="stFileUploaderDropzone"] {{
            width: 40px !important;
            min-width: 40px !important;
            max-width: 40px !important;
            height: 40px !important;
            min-height: 40px !important;
        }}

        div[data-testid="stForm"] [data-testid="stFileUploaderDropzone"]::before {{
            font-size: 20px;
        }}

        div[data-testid="stForm"] input[type="text"] {{
            height: 40px !important;
            padding: 0 13px !important;
            font-size: 13.5px !important;
            line-height: 40px !important;
        }}

        div[data-testid="stForm"] button[kind="formSubmit"] {{
            width: 40px !important;
            min-width: 40px !important;
            max-width: 40px !important;
            height: 40px !important;
            min-height: 40px !important;
            background-size: 18px 18px !important;
        }}
    }}

    @media (max-width: 360px) {{
        .block-container {{
            padding-left: 4px !important;
            padding-right: 4px !important;
        }}

        .chat-window {{
            height: calc(100dvh - 191px);
            min-height: 285px;
            padding: 8px;
        }}

        div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] {{
            grid-template-columns: 36px minmax(0, 1fr) 36px !important;
        }}

        div[data-testid="stForm"] [data-testid="stFileUploader"],
        div[data-testid="stForm"] [data-testid="stFileUploader"] section,
        div[data-testid="stForm"] [data-testid="stFileUploaderDropzone"] {{
            width: 36px !important;
            min-width: 36px !important;
            max-width: 36px !important;
            height: 36px !important;
            min-height: 36px !important;
        }}

        div[data-testid="stForm"] input[type="text"],
        div[data-testid="stForm"] button[kind="formSubmit"] {{
            height: 36px !important;
            min-height: 36px !important;
        }}

        div[data-testid="stForm"] button[kind="formSubmit"] {{
            width: 36px !important;
            min-width: 36px !important;
            max-width: 36px !important;
        }}
    }}

    /* ==========================================================
       DARK MODE
       ========================================================== */
    @media (prefers-color-scheme: dark) {{
        .stApp {{
            background: #101514 !important;
        }}

        .chat-window {{
            background-color: #202624;
            background-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220' viewBox='0 0 220 220'%3E%3Cg fill='none' stroke='%23ffffff' stroke-opacity='0.035' stroke-width='2'%3E%3Ccircle cx='58' cy='54' r='29'/%3E%3Cpath d='M38 77l40 40M78 77l-40 40'/%3E%3Cpath d='M14 128h34M31 111v34'/%3E%3Ccircle cx='111' cy='145' r='14'/%3E%3Cpath d='M160 130h34M177 113v34'/%3E%3C/g%3E%3C/svg%3E");
        }}

        .chat-bubble-other {{
            background: #2B302F;
            color: #f4f5f4;
        }}

        .chat-bubble-me {{
            background: #145c43;
            color: #ffffff;
        }}

        .msg-time {{
            color: #b8bfbd;
        }}

        div[data-testid="stForm"] {{
            background: #1c2221 !important;
            border-color: rgba(255,255,255,.12) !important;
            box-shadow: 0 6px 18px rgba(0,0,0,.28) !important;
        }}

        div[data-testid="stForm"] input[type="text"] {{
            color: #f4f5f4 !important;
            background: #29302e !important;
            border-color: #444b49 !important;
        }}

        div[data-testid="stForm"] input[type="text"]::placeholder {{
            color: #aeb7b4 !important;
            opacity: 1 !important;
        }}

        div[data-testid="stForm"] [data-testid="stFileUploaderDropzone"]::before {{
            filter: grayscale(1) brightness(1.7);
        }}
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

# ------------------------------------------------------------
# AUTO-SCROLL - always show the newest message
# Works after initial load, refresh, incoming message and send.
# ------------------------------------------------------------
components.html(
    """
    <script>
    (() => {
        const parentDoc = window.parent.document;

        const scrollToLatest = () => {
            try {
                const box = parentDoc.getElementById("chat-window-box");
                if (!box) return false;

                // Multiple passes handle Streamlit's async DOM rendering.
                const doScroll = () => {
                    box.scrollTop = box.scrollHeight;
                };

                doScroll();
                requestAnimationFrame(doScroll);
                setTimeout(doScroll, 60);
                setTimeout(doScroll, 180);
                setTimeout(doScroll, 350);
                return true;
            } catch (e) {
                return false;
            }
        };

        // Try repeatedly because Streamlit can render the markdown container
        // a little after the component itself is mounted.
        let tries = 0;
        const timer = setInterval(() => {
            tries += 1;
            if (scrollToLatest() || tries >= 50) {
                clearInterval(timer);
            }
        }, 100);

        // When new messages are inserted/updated, jump to the bottom again.
        const observerTimer = setInterval(() => {
            try {
                const box = parentDoc.getElementById("chat-window-box");
                if (!box) return;

                clearInterval(observerTimer);

                let lastHeight = box.scrollHeight;

                const observer = new MutationObserver(() => {
                    const newHeight = box.scrollHeight;
                    if (newHeight !== lastHeight) {
                        lastHeight = newHeight;
                        scrollToLatest();
                    }
                });

                observer.observe(box, {
                    childList: true,
                    subtree: true,
                    characterData: true
                });

                // Also handle image layout finishing after the message is rendered.
                box.querySelectorAll("img").forEach((img) => {
                    img.addEventListener("load", scrollToLatest, { once: true });
                });
            } catch (e) {}
        }, 100);

        // Extra fallback for browser/keyboard viewport changes.
        window.addEventListener("load", scrollToLatest, { once: true });
        window.addEventListener("resize", () => setTimeout(scrollToLatest, 80));
    })();
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
            "Attach photo",
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