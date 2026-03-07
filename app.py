import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="History-taking practice bot", page_icon="🩺")

st.title("🩺 History-taking practice bot")

# --- Read the API key from Streamlit Secrets ---
# In Streamlit Community Cloud you'll add this in App → Settings → Secrets
# Locally you can create .streamlit/secrets.toml (but do NOT commit it).
api_key = st.secrets["OPENAI_API_KEY"]

client = OpenAI(api_key=api_key)

SYSTEM_INSTRUCTIONS = """
You are a helpful paediatric history-taking tutor.
Ask one question at a time, keep it practical, and give brief feedback.
"""

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! Select the patient’s age and the system you would like."}
    ]

# Display chat so far
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

# New user input
selected_age = st.selectbox("Choose age group", ["Neonate", "Infant","1-5 years", "6-10 years", "11-19 years"])
if prompt := st.chat_input("Type your response…"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)

    # Call OpenAI Responses API
    response = client.responses.create(
        model="gpt-4.1-mini",
        instructions=SYSTEM_INSTRUCTIONS,
        input=st.session_state.messages,
    )

    assistant_text = response.output_text
    # Reset button
if st.button("Reset conversation"):
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! Tell me the patient’s age and the main complaint."}
    ]
    st.rerun()

    st.session_state.messages.append({"role": "assistant", "content": assistant_text})

    with st.chat_message("assistant"):
        st.write(assistant_text)
