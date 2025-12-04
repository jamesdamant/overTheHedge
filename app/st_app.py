import streamlit as st
import pandas as pd

from ingest import DataLoader
from database import Database

from agent import OverTheHedgeAgent

st.set_page_config(layout="wide", page_title="Hedge Fund Intelligence Tool")
st.title("Hedge Fund Intelligence Tool 🧠")
st.logo(
    "./data/Citi-logo.png", 
    size="large"
)
st.markdown("---")

data_loader = DataLoader()
db = Database()
agent = OverTheHedgeAgent()

DEFAULT_CIK = "1000045"

# Initialize Session State
if 'filing_df' not in st.session_state:
    st.session_state.filing_df = pd.DataFrame()
if 'filing_metadata' not in st.session_state:
    st.session_state.filing_metadata = {}
if "messages" not in st.session_state:
    st.session_state.messages = [] 


col_agent, col_importer = st.columns(2)


with col_agent:
    st.header("🤖 Intelligence Agent")
    st.markdown("Ask questions about the holdings data in the database.")
    
    chat_container = st.container(height=500, border=True)

    # Display chat messages from history inside the container
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])


    if prompt := st.chat_input("How Can I Help?", key="chat_input_agent"):
        
        # Display user message
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

        with chat_container:
            with st.chat_message("assistant"):
                response_stream = agent.call(st.session_state.messages, prompt)
                response = st.write_stream(response_stream)
                
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages.append({"role": "assistant", "content": response})


with col_importer:
    st.header("📊 Data Importer")
    st.markdown("Fetch, preview, and import 13F-HR filings into the database.")

    # Setup and Input
    cik_input = st.text_input(
        "Enter Fund CIK (e.g., 1000045):", 
        value=DEFAULT_CIK, 
        max_chars=10,
        key="importer_cik_input"
    ).strip()

    message_placeholder = st.empty()

    button_col1, button_col2 = st.columns(2)

    with button_col1:
        # 1. Fetch Filing Metadata
        if st.button("1. Fetch Latest 13F Metadata", use_container_width=True, key="btn_fetch_meta"):
            if cik_input:
                with st.spinner(f"Searching for latest 13F filing for CIK {cik_input}..."):
                    metadata = data_loader.get_latest_sub(cik_input)
                    
                    if metadata:
                        st.session_state.filing_metadata = metadata
                        acc_num = metadata.get("accessionNumber")
                        message_placeholder.success(
                            f"Found latest 13F filing for **{metadata['name']}** (CIK: {cik_input}). Accession Number: `{acc_num}` | Filing Date: **{metadata['filingDate']}**"
                        )
                    else:
                        message_placeholder.error(f"Could not find a recent 13F-HR filing for CIK {cik_input}.")
                        st.session_state.filing_metadata = {}
                        st.session_state.filing_df = pd.DataFrame()
            else:
                message_placeholder.warning("Please enter a CIK number.")

    with button_col2:
        # 2. Fetch Infotable DataFrame
        if st.session_state.filing_metadata:
            metadata = st.session_state.filing_metadata
            acc_num = metadata.get("accessionNumber")

            if st.button(f"2. Fetch Holdings (Acc: {acc_num[:10]}...)", use_container_width=True, key="btn_fetch_data"):
                with st.spinner(f"Fetching XML data for {acc_num}..."):
                    try:
                        df = data_loader.get_infotable(cik_input, acc_num.replace("-",""), metadata)
                        st.session_state.filing_df = df
                        message_placeholder.success(f"Successfully fetched **{len(df)}** holding records into the DataFrame.")
                    except Exception as e:
                        message_placeholder.error(f"An error occurred while fetching infotable: {e}")
                        st.session_state.filing_df = pd.DataFrame()
        else:
            st.button("2. Fetch Holdings", disabled=True, use_container_width=True, key="btn_fetch_data_disabled")

    

    if not st.session_state.filing_df.empty:
        st.subheader("Data Preview (Top 20 Holdings)")
        
        # 3. Display Data Preview
        df_preview = st.session_state.filing_df.head(20).copy()
        df_preview['value'] = df_preview['value'].apply(lambda x: f"${x:,}")
        st.dataframe(df_preview, use_container_width=True, height=250)
        
        st.markdown(f"**Total Records Fetched**: {len(st.session_state.filing_df):,} | **Report Date**: {st.session_state.filing_metadata.get('reportDate')}")

        # 4. Insert into Database
        if st.button("3. Insert All Holdings into Database", type="primary", use_container_width=True, key="btn_insert_db"):
            with st.spinner("Inserting data into SQLite database..."):
                try:
                    db.insert_dataframe(st.session_state.filing_df)
                    message_placeholder.success(f"Successfully inserted **{len(st.session_state.filing_df)}** records for **{st.session_state.filing_metadata.get('name')}** into `holdings` table.")
                    
                    # Clear state to prepare for next import
                    st.session_state.filing_df = pd.DataFrame()
                    st.session_state.filing_metadata = {}
                except Exception as e:
                    message_placeholder.error(f"Failed to insert data into database: {e}")

    # Database Status
    st.subheader("Database Status")
    try:
        count_q = db.cursor.execute("SELECT COUNT(*) FROM holdings")
        total_records = count_q.fetchone()[0]
        st.info(f"Database (`hedgefund.db`) initialized. Current holdings count: **{total_records:,}**")
    except Exception as e:
        st.error(f"Could not connect or query database: {e}")