# Google MCP-style Python Server

A complete MCP (Model Context Protocol) style server in Python integrating Google Docs and Gmail. This server implements FastAPI endpoints to execute operations but requires manual approval in the terminal before performing any actions.

## 📁 Directory Structure

```text
google-mcp-server/
├── server.py          → FastAPI app with tool endpoints
├── auth.py            → Google OAuth authentication
├── docs_tool.py       → Google Docs tool (append content)
├── gmail_tool.py      → Gmail tool (create draft)
├── requirements.txt   → Python package dependencies
├── README.md          → Setup and usage instructions
├── credentials.json   → (NOT committed — download from Google Cloud Console)
└── token.json         → (NOT committed — auto-generated after first login)
```

---

## ⚙️ Setup Instructions

### 1. Google Cloud Console Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Enable the APIs:
   - Go to **APIs & Services > Library**.
   - Search for **Google Docs API** and click **Enable**.
   - Search for **Gmail API** and click **Enable**.
4. Configure the OAuth Consent Screen:
   - Go to **APIs & Services > OAuth consent screen**.
   - Choose **External** user type and click **Create**.
   - Fill in the required fields (App name, support email, developer contact info).
   - Under **Scopes**, add the following:
     - `https://www.googleapis.com/auth/documents`
     - `https://www.googleapis.com/auth/gmail.compose`
   - Under **Test users**, add your own Google email address (the one you intend to login with).
5. Create Credentials:
   - Go to **APIs & Services > Credentials**.
   - Click **+ Create Credentials > OAuth client ID**.
   - Choose **Desktop app** as the Application type.
   - Enter a name (e.g., `Google MCP Client`) and click **Create**.
   - Download the JSON credentials file by clicking the download icon next to the client ID.
   - Rename the file to `credentials.json` and place it in the `google-mcp-server/` directory.

### 2. Installation

Install all required dependencies using `pip`:

```bash
pip install -r requirements.txt
```

---

## 🚀 Running the Server

Start the server using `uvicorn` or by running the script directly:

```bash
python server.py
```

The server will start on `http://127.0.0.1:8000`.

---

## 💡 Usage & Authentication Flow

1. On the very first request to any endpoint, if `token.json` is missing:
   - The server will open a browser window requesting authorization to access your Google Docs and Gmail account.
   - Select your test user Google account and accept the scopes.
   - Once authorized, a `token.json` is generated, and subsequent calls will reuse the token automatically.
2. For every endpoint call, the server terminal will block and display the payload details, prompting for manual confirmation:
   ```text
   ==================================================
   PENDING ACTION APPROVAL
   Action: Append to Google Doc
   Payload:
     doc_id: 1234567890abcdef
     content: Hello Google Docs!
   ==================================================
   Approve? (y/n): 
   ```
   - Type `y` or `yes` to proceed.
   - Type `n` or `no` (or press Ctrl+C / send EOF) to reject. Rejections return a `403 Forbidden` response.

---

## 🧪 API Endpoints & Verification

### 1. Append to Google Doc

Appends text to the end of the specified Google Document.

* **URL**: `/append_to_doc`
* **Method**: `POST`
* **Content-Type**: `application/json`
* **Request Body**:
  ```json
  {
    "doc_id": "YOUR_GOOGLE_DOC_ID",
    "content": "Line of text to append to the document.\n"
  }
  ```

#### Example Curl Request:
```bash
curl -X POST http://127.0.0.1:8000/append_to_doc \
     -H "Content-Type: application/json" \
     -d "{\"doc_id\": \"YOUR_GOOGLE_DOC_ID\", \"content\": \"Added text via MCP Server!\n\"}"
```

---

### 2. Create Email Draft

Creates a draft email in your Gmail account.

* **URL**: `/create_email_draft`
* **Method**: `POST`
* **Content-Type**: `application/json`
* **Request Body**:
  ```json
  {
    "to": "recipient@example.com",
    "subject": "Hello from MCP Server",
    "body": "This draft was created using the Google MCP FastAPI Server."
  }
  ```

#### Example Curl Request:
```bash
curl -X POST http://127.0.0.1:8000/create_email_draft \
     -H "Content-Type: application/json" \
     -d "{\"to\": \"recipient@example.com\", \"subject\": \"Draft Subject\", \"body\": \"Draft message body.\"}"
```

---

## 🧪 Testing & Verification

A mock-based unit test suite is included to verify the endpoints, route validations, and manual approval logic without requiring active Google API credentials.

To run the test suite:
```bash
uv run python -m unittest test_server.py
```

