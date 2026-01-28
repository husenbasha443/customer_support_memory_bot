import os
from datetime import datetime
from typing import List, Dict, Any

import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from memory_manager import (
    ensure_user_storage,
    list_conversations,
    create_new_conversation,
    get_conversation,
    append_message,
    search_conversations,
)
from chat_graph import build_chat_graph


load_dotenv()


def init_session_state():
    if "graph" not in st.session_state:
        try:
            st.session_state.graph = build_chat_graph()
        except Exception as e:
            st.session_state.graph = None
            st.session_state.graph_error = str(e)
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "current_conv_id" not in st.session_state:
        st.session_state.current_conv_id = None
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""


def login_view():
    st.markdown(
        "<h2 style='color:white;margin-top:2rem;'>Customer Support Bot</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:#9ca3af;'>Login with your User ID or create a new one.</p>",
        unsafe_allow_html=True,
    )

    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        with st.form("login_form"):
            st.markdown(
                "<div style='font-size:0.9rem;color:#9ca3af;margin-bottom:0.5rem;'>Welcome back · multi-user workspace</div>",
                unsafe_allow_html=True,
            )
            user_id = st.text_input("User ID", key="login_user_id")
            submitted = st.form_submit_button("Login")

        if submitted and user_id.strip():
            st.session_state.user_id = user_id.strip()
            ensure_user_storage(st.session_state.user_id)
            st.session_state.current_conv_id = None
            st.rerun()


def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div style='padding:0.5rem 0;'>
              <span style='background:#0f4c75;color:white;padding:0.2rem 0.6rem;border-radius:999px;font-size:0.75rem;font-weight:600;'>
                ASSIGNMENT 1
              </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            "<h3 style='margin-top:0.5rem;margin-bottom:0;'>Customer Support Bot</h3>",
            unsafe_allow_html=True,
        )
        st.caption("Multi-user memory-aware assistant.")

        st.markdown("---")
        st.markdown(f"**Logged in as:** `{st.session_state.user_id}`")

        if st.button("🔄 New chat", use_container_width=True):
            conv = create_new_conversation(
                st.session_state.user_id,
                title=f"Session – {datetime.utcnow().strftime('%H:%M:%S')}",
            )
            st.session_state.current_conv_id = conv["id"]
            st.rerun()

        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key not in ("graph", "graph_error"):
                    del st.session_state[key]
            st.session_state.user_id = None
            st.rerun()

        st.markdown("---")
        st.markdown("**Search your chats**")
        search_query = st.text_input(
            "Search", value=st.session_state.search_query, label_visibility="collapsed"
        )
        st.session_state.search_query = search_query

        if search_query.strip():
            conversations = search_conversations(st.session_state.user_id, search_query)
        else:
            conversations = list_conversations(st.session_state.user_id)

        st.markdown("**Chat history**")
        if not conversations:
            st.caption("No conversations yet. Start a new chat.")
        for conv in conversations:
            label = conv.get("title") or conv["id"][:8]
            ts = conv.get("updated_at", "")[:19].replace("T", " ")
            if st.button(
                f"💬  {label}  ·  {ts}",
                key=f"conv-{conv['id']}",
                use_container_width=True,
                help="Open this conversation",
            ):
                st.session_state.current_conv_id = conv["id"]
                st.rerun()


def render_conversation_messages(conv: Dict[str, Any]):
    st.markdown("### Conversation")
    for msg in conv.get("messages", []):
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            with st.chat_message("user"):
                st.markdown(content)
        else:
            with st.chat_message("assistant"):
                st.markdown(content)


def suggestion_buttons() -> List[str]:
    cols = st.columns(3)
    suggestions = [
        "Summarize my previous converstaions",
        "Show unresolved follow-ups",
        "What did we try last time?",
    ]
    clicked: List[str] = []
    for col, text in zip(cols, suggestions):
        with col:
            if st.button(text, key=f"suggest-{text}"):
                clicked.append(text)
    return clicked


def chat_view():
    render_sidebar()

    header_col, sugg_col = st.columns([3, 2])
    with header_col:
        st.markdown(
            "<h2 style='margin-bottom:0.2rem;'>Customer Support Bot</h2>",
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <p style='color:#e5e7eb;font-size:0.95rem;'>
             A user-friendly chat system that remembers past conversations for each user.
            </p>
            """,
            unsafe_allow_html=True,
        )
    with sugg_col:
        st.markdown("#### Smart suggestions")
        suggestion_clicked = suggestion_buttons()
        default_suggestion = suggestion_clicked[0] if suggestion_clicked else ""

    if "graph_error" in st.session_state and st.session_state.graph is None:
        st.error(
            "LangGraph could not be initialized. "
            f"Check your Azure OpenAI settings.\n\n{st.session_state.graph_error}"
        )
        return

    if st.session_state.current_conv_id is None:
        # Auto-create first conversation
        conv = create_new_conversation(
            st.session_state.user_id,
            title=f"Session – {datetime.utcnow().strftime('%H:%M:%S')}",
        )
        st.session_state.current_conv_id = conv["id"]

    conv = get_conversation(st.session_state.user_id, st.session_state.current_conv_id)
    if conv is None:
        st.warning("Conversation not found. Creating a new one.")
        conv = create_new_conversation(
            st.session_state.user_id,
            title=f"Session – {datetime.utcnow().strftime('%H:%M:%S')}",
        )
        st.session_state.current_conv_id = conv["id"]

    render_conversation_messages(conv)

    user_input = st.chat_input("Ask something about your support issues...")
    if suggestion_clicked and not user_input:
        user_input = default_suggestion

    if user_input:
        # Append user message to JSON memory first
        append_message(st.session_state.user_id, conv["id"], "user", user_input)
        conv = get_conversation(st.session_state.user_id, conv["id"]) or conv

        # Build memory from all conversations for this user (not just current chat),
        # so that new chats can still leverage previous context.
        history_messages = [
            SystemMessage(
                content=(
                    "You are a customer support assistant. "
                    "You are given the full history of this user's conversations "
                    "across multiple sessions. Use this history as memory to "
                    "answer the user's latest question accurately."
                )
            )
        ]
        for conv_item in reversed(list_conversations(st.session_state.user_id)):
            for msg in conv_item.get("messages", []):
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    history_messages.append(HumanMessage(content=content))
                else:
                    history_messages.append(AIMessage(content=content))

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking with your history..."):
                stream = st.session_state.graph.stream(
                    {"messages": history_messages}, stream_mode="values"
                )
                full_response = ""
                placeholder = st.empty()
                for chunk in stream:
                    msgs = chunk.get("messages") or []
                    if not msgs:
                        continue
                    last_msg = msgs[-1]
                    if isinstance(last_msg, AIMessage):
                        full_response = last_msg.content
                        placeholder.markdown(full_response)

        append_message(
            st.session_state.user_id,
            conv["id"],
            "assistant",
            full_response,
        )


def main():
    st.set_page_config(
        page_title="Customer Support Bot with Memory",
        layout="wide",
        page_icon="💬",
    )
    init_session_state()

    # Dark-ish background styling to resemble the screenshot
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #020617;
            color: #f9fafb;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        section[data-testid="stSidebar"] {
            background-color: #020617;
            border-right: 1px solid #111827;
        }
        /* Generic button styling */
        .stButton > button {
            background: linear-gradient(135deg, #111827, #020617);
            color: #e5e7eb;
            border-radius: 0.7rem;
            border: 1px solid #111827;
            padding: 0.5rem 0.9rem;
            font-size: 0.9rem;
            text-align: center;
        }
        .stButton > button:hover {
            border-color: #38bdf8;
            box-shadow: 0 0 0 1px rgba(56,189,248,0.5);
        }
        /* Login form styling */
        form[data-testid="stForm"] {
            background: #020617;
            border-radius: 1rem;
            padding: 2rem 2.5rem 1.5rem 2.5rem;
            border: 1px solid #111827;
            box-shadow: 0 24px 60px rgba(15,23,42,0.75);
        }
        form[data-testid="stForm"] input[type="text"] {
            background-color: #020617;
            border-radius: 0.6rem;
            border: 1px solid #111827;
            color: #e5e7eb;
        }
        /* Sidebar search box */
        [data-testid="stSidebar"] input[type="text"] {
            background-color: #020617;
            border-radius: 0.6rem;
            border: 1px solid #111827;
            color: #e5e7eb;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.user_id is None:
        login_view()
    else:
        chat_view()


if __name__ == "__main__":
    main()

