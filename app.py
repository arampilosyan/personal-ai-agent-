import uuid
import streamlit as st
from app.agent import AgentError, PersonalAgent
from app.config import settings
from app.document_reader import DocumentError, extract_text
from database.db import Database

settings.ensure_data_dir()
db = Database(settings.database_path)
agent = PersonalAgent(db)

st.set_page_config(page_title="Personal AI Agent", page_icon="🤖", layout="wide")
st.title("🤖 Personal AI Agent")
st.caption("Chat with your assistant, summarize PDF/TXT files, and manage tasks.")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "document_text" not in st.session_state:
    st.session_state.document_text = None
if "document_name" not in st.session_state:
    st.session_state.document_name = None

with st.sidebar:
    st.subheader("Session")
    st.code(st.session_state.session_id, language=None)
    st.caption("This session ID links chat history and tasks in the local SQLite database.")
    if st.button("New session"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.document_text = None
        st.session_state.document_name = None
        st.rerun()
    st.divider()
    st.subheader("Upload a document")
    uploaded = st.file_uploader("PDF or TXT", type=["pdf", "txt"])
    if uploaded and st.button("Summarize document", type="primary"):
        if uploaded.size > settings.max_upload_mb * 1024 * 1024:
            st.error(f"File is larger than {settings.max_upload_mb} MB.")
        else:
            try:
                doc_text = extract_text(uploaded.name, uploaded.getvalue(), settings.max_document_chars)
                st.session_state.document_text = doc_text
                st.session_state.document_name = uploaded.name
                with st.spinner("Summarizing..."):
                    summary = agent.summarize_document(st.session_state.session_id, uploaded.name, doc_text)
                st.success("Document summarized and saved to history.")
                st.markdown(summary)
            except (DocumentError, AgentError) as exc:
                st.error(str(exc))
    if st.session_state.document_name:
        st.caption(f"Current document: {st.session_state.document_name}")
    st.divider()
    st.subheader("Tasks")
    for task in db.list_tasks(st.session_state.session_id):
        label = f"#{task['id']} · {task['title']}"
        if task["status"] == "done":
            st.write("✅ " + label)
        else:
            col1, col2 = st.columns([4, 1])
            col1.write(label)
            if col2.button("Done", key=f"done_{task['id']}"):
                db.complete_task(st.session_state.session_id, task["id"])
                st.rerun()

for message in db.get_messages(st.session_state.session_id, limit=50):
    if message["role"] in {"user", "assistant"}:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

prompt = st.chat_input("Ask a question or give your assistant a task...")
if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        try:
            with st.spinner("Thinking..."):
                answer = agent.chat(st.session_state.session_id, prompt, document_text=st.session_state.document_text)
            st.markdown(answer)
        except AgentError as exc:
            st.error(str(exc))
        except ValueError as exc:
            st.warning(str(exc))
