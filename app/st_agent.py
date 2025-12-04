import streamlit as st

from agent import OverTheHedgeAgent
from ingest import DataLoader


agent = OverTheHedgeAgent()
# dl = DataLoader()

st.set_page_config(layout="wide") # Optional: uses the full screen width
st.title("Hedge Fund Intelligence Agent 🧠")
st.markdown("---")


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [] 

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("How Can I Help?"):
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_stream = agent.call(st.session_state.messages, prompt)
        response = st.write_stream(response_stream)
        
    # IMPORTANT: Add the final response to history after streaming
    st.session_state.messages.append({"role": "assistant", "content": response})