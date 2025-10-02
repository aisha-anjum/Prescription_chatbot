
import streamlit as st
import re
import difflib


st.markdown("""
<style>
.main > div { display: flex; justify-content: center; }
.block-container { max-width: 60%; margin: auto; }
</style>
""", unsafe_allow_html=True)


st.set_page_config(page_title="Prescription Chatbot", layout="wide")
st.title("💊 Rule-based Prescription Chatbot")
# ------------------ Knowledge Base ------------------
DB = {
    "fever": {
        "keywords": ["fever", "high temperature", "temperature", "flu", "shivering"],
        "medicines": ["Paracetamol 500-1000 mg as needed"],
        "advice": "Rest, hydrate. See doctor if fever > 3 days or temp >= 39°C."
    },
    "headache": {
        "keywords": ["headache", "migraine", "head pain"],
        "medicines": ["Ibuprofen 200-400 mg", "Paracetamol 500-1000 mg"],
        "advice": "Rest in a quiet place. See doctor if severe or new neurological signs."
    },
    "sore throat": {
        "keywords": ["sore throat", "throat pain", "scratchy throat"],
        "medicines": ["Lozenges or throat spray", "Paracetamol for pain"],
        "advice": "Gargle with warm salt water and stay hydrated."
    },
    "cough": {
        "keywords": ["cough", "dry cough", "productive cough", "phlegm"],
        "medicines": ["Dextromethorphan (dry cough)", "Guaifenesin (productive cough)"],
        "advice": "Hydrate well. See a doctor if cough > 2 weeks or blood is present."
    },
    "stomach pain": {
        "keywords": ["stomach pain", "abdominal pain", "stomach ache"],
        "medicines": ["Antacid for mild indigestion"],
        "advice": "Avoid heavy meals. See doctor for severe/persistent pain."
    }
}

# Emergency keywords
EMERGENCY = [
    "chest pain", "severe difficulty breathing", "loss of consciousness", "unconscious",
    "severe bleeding", "blood in vomit", "blood in stool", "blue lips", "anaphylaxis"
]

# --------- Helper Functions ---------
def preprocess(text):
    t = text.lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def check_emergency(text):
    t = preprocess(text)
    for e in EMERGENCY:
        if e in t:
            return e
    return None

# Precompute single keywords for fuzzy matching
single_word_keys = []
key_to_disease = {}
for disease, info in DB.items():
    for kw in info["keywords"]:
        if " " not in kw:
            single_word_keys.append(kw)
            key_to_disease[kw] = disease


def find_matches(text):
    text_p = preprocess(text)
    tokens = text_p.split()
    matches = []

    # 1. Exact match
    for disease, info in DB.items():
        for kw in info["keywords"]:
            if " " in kw and kw in text_p and disease not in matches:
                matches.append(disease)
            elif kw in tokens and disease not in matches:
                matches.append(disease)

    # 2. Fuzzy match for typos
    for token in tokens:
        close = difflib.get_close_matches(token, single_word_keys, n=1, cutoff=0.75)
        if close:
            d = key_to_disease[close[0]]
            if d not in matches:
                matches.append(d)

    return matches

def format_reply(matches):
    if not matches:
        return "🤔 I couldn't confidently match your symptom. Try adding more detail (e.g., 'sore throat', 'fever 2 days')."
    lines = []
    for d in matches[:2]:
        info = DB[d]
        lines.append(f"<b>Condition:</b> {d.capitalize()}")
        for med in info["medicines"]:
            lines.append(f"• <b>Medicine:</b> {med}")
        lines.append(f"<b>Advice:</b> {info['advice']}")
        lines.append("")
    return "<br>".join(lines)

# ------------------ UI Styling ------------------
chat_css = """
<style>
.chat-container { display:flex; flex-direction:column; gap:8px; padding:6px;  }
.bubble { max-width:70%; padding:10px 12px; border-radius:12px; font-size:14px; line-height:1.4; display:inline-block; }
.bubble-flex-user { display:flex; justify-content:flex-end; width:100%;}
.bubble-flex-bot { display:flex; justify-content:flex-start; width:100%;}
.user { align-self:flex-end; background:#dcf8c6; border-bottom-right-radius:2px;  }
.bot { align-self:flex-start; background:#f1f0f0; border-bottom-left-radius:2px; margin-bottom: 15px }
.small { font-size:12px; color:#555;  }
</style>
"""
st.markdown(chat_css, unsafe_allow_html=True)

# ------------------ Chat Session ------------------
if "history" not in st.session_state:
    st.session_state.history = []   # will store pairs: [(user_msg, bot_msg), ...]

st.markdown("### 💬 Chat")

# ------------------ Process new message first ------------------
if "new_msg" in st.session_state and st.session_state.new_msg.strip():
    msg = st.session_state.new_msg.strip()
    clean_msg = msg.replace("<", "&lt;").replace(">", "&gt;")

    # Generate bot reply
    em = check_emergency(msg)
    if em:
        bot_text = f"<b>🚨 EMERGENCY:</b> '{em}'. Please seek immediate medical care."
    else:
        matches = find_matches(msg)
        bot_text = format_reply(matches)

    # Save as a pair (user + bot together)
    st.session_state.history.append((clean_msg, bot_text))
    st.session_state.new_msg = ""  # clear after processing

# ------------------ Input Form (always at bottom) ------------------
with st.form("msg_form", clear_on_submit=False):
    st.text_input("Type your symptom here...", key="new_msg")
    st.form_submit_button("Send")
# Small tip at bottom
st.markdown("<div class='small'>💡 Tip: Try typing symptoms like 'headache', 'dry cough', or 'stomach pain'.</div>", unsafe_allow_html=True)



# ------------------ Show Chat (latest first) ------------------
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for user_msg, bot_msg in reversed(st.session_state.history):  # latest first
    st.markdown(f'<div class="bubble-flex-user"><div class="bubble user">{user_msg}</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="bubble-flex-bot"><div class="bubble bot">{bot_msg}</div></div>', unsafe_allow_html=True)
    
st.markdown('</div>', unsafe_allow_html=True)




