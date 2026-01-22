import streamlit as st
import time

# 1. Page Configuration (Must be the first Streamlit command)
st.set_page_config(
    page_title="My Chat App",
    page_icon="💬",
    layout="centered"
)

# 2. Sidebar - Useful for settings or navigation
with st.sidebar:
    st.header("⚙️ Settings")
    st.write("This is a critical layout component.")
    
    # Button to clear history
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# 3. Main Title
st.title("💬 Simple Streamlit Chat")
st.caption("A demo of critical Streamlit components.")

# 4. Session State - CRITICAL for chat
# Streamlit reruns the whole script on every interaction. 
# Without session_state, variables reset every time you press enter.
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am a dummy bot. Type anything to see how I work."}
    ]

# 5. Display History
# We loop through the saved messages and render them on screen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. Chat Input - The main entry point
if prompt := st.chat_input("What is up?"):
    # A. Display User Message immediately
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # B. Add User Message to State
    st.session_state.messages.append({"role": "user", "content": prompt})

    # C. Generate Dummy Response (Simulate "thinking")
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Simulate a stream of data
        dummy_response = f"I received your message: '{prompt}'. This is a dummy response!"
        
        for chunk in dummy_response.split():
            full_response += chunk + " "
            time.sleep(0.05)
            # Add a blinking cursor to simulate typing
            message_placeholder.markdown(full_response + "▌")
        
        message_placeholder.markdown(full_response)
    
    # D. Add Bot Response to State
    st.session_state.messages.append({"role": "assistant", "content": full_response})