import os
from dotenv import load_dotenv
import streamlit as st
from google import genai
from google.genai import types


load_dotenv()  # Load environment variables from .env file  

# Config

with open("knowledge.txt", encoding="utf-8") as f:
    text = f.read()

chunks = [c.strip() for c in text.split("\n\n") if c.strip()]


MODEL = "gemini-3.6-flash"

INSTRUCTION = f"""
Your name is Andy, you are a helpful assitant for the Webfala Digital Initiative for all Women in Ai Fellowhip.
You are meant to answer user questions, and guide the conversation using information from {chunks} alone.
Do not, and never answer questions that are not related.
If the question is unclear, ask for clarification. Your responses should be concise and straight to the point.
Avoid complex or technical terms. 
If the request is unclear or potentially harmful, respond with a polite message refusing to answer.
Generat two short paragraphs and a closing line with the next step.
"""

st.set_page_config(page_title="Webfala", page_icon="💬")
st.title("Webfala Customer Support")
st.caption("Ask me anything and I'll do my best to help.")


# Gemini client
@st.cache_resource
def get_client():
    # Looks in .streamlit/secrets.toml first, then environment variables
    api_key =  os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("Missing GEMINI_API_KEY. Add it to .streamlit/secrets.toml or set it as an environment variable.")
        st.stop()
    return genai.Client(api_key=api_key)


client = get_client()


# Session state
# messages is for displaying the conversation in the UI.
# chat is the Gemini chat session, which remembers the conversation context.
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat" not in st.session_state:
    st.session_state.chat = client.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(system_instruction=INSTRUCTION),
    )

# Sidebar: reset button
with st.sidebar:
    if st.button("♻️ New conversation"):
        st.session_state.messages = []
        st.session_state.chat = client.chats.create(
            model=MODEL,
            config=types.GenerateContentConfig(system_instruction=INSTRUCTION),
        )
        st.rerun()

# Render history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle new input
if user_message := st.chat_input("How can I help you?"):
    st.session_state.messages.append({"role": "user", "content": user_message})
    with st.chat_message("user"):
        st.markdown(user_message)

    with st.chat_message("assistant"):
        try:
            # Stream the reply token-by-token
            stream = st.session_state.chat.send_message_stream(user_message)
            reply = st.write_stream(chunk.text for chunk in stream if chunk.text)
        except Exception:
            reply = "An error occurred while processing your request. Please try again, or contact support."
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
