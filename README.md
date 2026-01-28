## Customer Support Bot with Memory (Azure OpenAI + LangGraph + Streamlit)

This is a multi-user customer support assistant that remembers previous issues and conversations across sessions.

- **Stack**: Streamlit, LangChain, LangGraph, Azure OpenAI.
- **Memory**: Per-user JSON files under `data/users/<user_id>/conversations.json`.
- **Multi-user**: Each user logs in with a `user_id` and only sees their own chats.
- **Features**:
  - Persistent conversation history across logins.
  - Multiple conversations (sessions) per user.
  - Sidebar chat history and **New chat** button.
  - Search across your own chats.
  - Simple smart suggestions and LangGraph-based conversational flow.

### 1. Setup

```bash
cd d:\\assignments\\memory_bot
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

### 2. Configure Azure OpenAI

Set the following environment variables (for example via a `.env` file in the project root):

```bash
AZURE_OPENAI_API_KEY="your-key"
AZURE_OPENAI_ENDPOINT="https://your-resource-name.openai.azure.com"
AZURE_OPENAI_DEPLOYMENT="your-chat-deployment-name"
AZURE_OPENAI_API_VERSION="2024-06-01"
```

### 3. Run the app

```bash
streamlit run app.py
```

Then open the URL shown in the terminal (usually `http://localhost:8501`).

### 4. Usage

- On the login screen, enter a **User ID** (e.g. `user01`, `user02`).
- After login:
  - Use **New chat** to start a new conversation.
  - The sidebar shows your **chat history**; click any entry to reopen it.
  - Use the **Search** box to find chats containing specific text.
  - Type messages in the chat input or click a **suggestion** button.
- Click **Logout** to end the session. When you log in again with the same user ID, all your conversations are still available.

## Customer Support Bot with Memory (Azure OpenAI + LangGraph + Streamlit)

This is a multi-user customer support assistant that remembers previous issues and conversations across sessions.

- **Stack**: Streamlit, LangChain, LangGraph, Azure OpenAI, PostgreSQL.
- **Memory**: Per-user conversations and messages stored safely in PostgreSQL (tables `conversations` and `messages`).
- **Multi-user**: Each user logs in with a `user_id` and only sees their own chats.
- **Features**:
  - Persistent conversation history across logins.
  - Multiple conversations (sessions) per user.
  - Sidebar chat history and **New chat** button.
  - Search across your own chats.
  - Simple smart suggestions and LangGraph-based conversational flow.

### 1. Setup

```bash
cd d:\\assignments\\memory_bot
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

### 2. Configure Azure OpenAI and PostgreSQL

Create a `.env` file in the project root with values similar to:

```bash
AZURE_OPENAI_API_KEY="your-key"
AZURE_OPENAI_ENDPOINT="https://your-resource-name.openai.azure.com"
AZURE_OPENAI_DEPLOYMENT="your-chat-deployment-name"
AZURE_OPENAI_API_VERSION="2024-06-01"

DATABASE_URL=postgresql://user:password@localhost:5432/customer_bot
```

On first run, SQLAlchemy will automatically create the `conversations` and `messages` tables in the `customer_bot` database.

### 3. Run the app

```bash
streamlit run app.py
```

Then open the URL shown in the terminal (usually `http://localhost:8501`).

### 4. Usage

- On the login screen, enter a **User ID** (e.g. `user01`, `user02`). Each user’s chats are stored under their own `user_id` in PostgreSQL.
- After login:
  - Use **New chat** to start a new conversation.
  - The sidebar shows your **chat history**; click any entry to reopen it.
  - Use the **Search** box to find chats containing specific text across all of your conversations.
  - Type messages in the chat input or click a **Smart suggestion** button.
- Click **Logout** to end the session. When you log in again with the same user ID, all your conversations are still available from the database.

