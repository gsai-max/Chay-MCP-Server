# Deployment Plan — Deploying Google MCP Server to Railway

This document details the configuration updates, container patterns, and step-by-step procedures to deploy the Google Docs & Gmail MCP-style Python server to [Railway](https://railway.app/).

---

## 1. Cloud Architecture & Ephemeral Storage

Railway deploys applications inside isolated containers. Because these containers use **ephemeral filesystems** (changes to local files like `token.json` are lost on restart or redeployment), we must migrate file storage to **Environment Variables**.

```
   ┌──────────────────────────────────────────────┐
   │             Railway Dashboard Env            │
   │  ┌──────────────────┐  ┌──────────────────┐  │
   │  │ GOOGLE_CREDS_JSON│  │ GOOGLE_TOKEN_JSON│  │
   │  └────────┬─────────┘  └────────┬─────────┘  │
   └───────────┼─────────────────────┼────────────┘
               │ (Loads config)      │ (Bypasses local OAuth flow)
               ▼                     ▼
   ┌──────────────────────────────────────────────┐
   │            FastAPI Server Container          │
   │                                              │
   │  * Host: 0.0.0.0                             │
   │  * Port: $PORT (Assigned by Railway)         │
   │  * Interactive prompt -> Bypassed via key    │
   └──────────────────────────────────────────────┘
```

### Proposed Code Updates

To make this server cloud-native, we will implement environment fallbacks for files:
1. **Google Credentials & Token**: `auth.py` will first check if `GOOGLE_CREDENTIALS_JSON` and `GOOGLE_TOKEN_JSON` env variables exist. If so, they will load config dictionaries directly without looking for local files on disk.
2. **Terminal Approval Workaround**: Since Railway environments are non-interactive, the blocking console `input("Approve? (y/n)")` will fail with an `EOFError` or hang. We will implement a `BYPASS_APPROVAL_KEY` environment variable. If requests include this key in their headers (e.g. `X-Approval-Key`), the request is approved automatically.

---

## 2. Code Changes Required

### A. Update `auth.py` (OAuth via Env variables)
Modify the credential resolver to parse string configurations:
```python
import json
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# ... scopes and paths ...

def get_credentials():
    creds = None
    
    # 1. Attempt loading token from Env Variable first (Railway / Cloud deployment)
    token_env = os.environ.get("GOOGLE_TOKEN_JSON")
    if token_env:
        try:
            token_data = json.loads(token_env)
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        except Exception as e:
            print(f"Error parsing GOOGLE_TOKEN_JSON: {e}")

    # Fallback to local token.json
    if not creds and os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
        else:
            # 2. Attempt loading client secrets from Env Variable
            creds_env = os.environ.get("GOOGLE_CREDENTIALS_JSON")
            if creds_env:
                client_config = json.loads(creds_env)
                flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                # Note: Interactive local server login is not supported in headless environments
                raise ValueError("Credentials expired on host; please refresh token.json locally and update GOOGLE_TOKEN_JSON.")
            
            # Local file fallback
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError("credentials.json is missing.")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
            
    return creds
```

### B. Update `server.py` (Port binding & Header key approval)
```python
import os
from fastapi import Header, FastAPI, HTTPException

# ... schemas ...

@app.post("/append_to_doc")
def append_to_doc_endpoint(payload: AppendDocPayload, x_approval_key: str = Header(None)):
    # If a bypass key is set in environments, check if the client supplied it
    bypass_key = os.environ.get("BYPASS_APPROVAL_KEY")
    if bypass_key and x_approval_key == bypass_key:
        approved = True
    else:
        approved = get_terminal_approval("Append to Google Doc", payload.model_dump())
        
    if not approved:
        raise HTTPException(status_code=403, detail="Action rejected by user")
    
    # ... call api ...
```
Modify uvicorn boot parameters at the bottom of `server.py`:
```python
if __name__ == "__main__":
    import uvicorn
    # Bind to host 0.0.0.0 and dynamically resolve port from Railway
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

---

## 3. Container Configuration (`Dockerfile`)

Create a `Dockerfile` inside `google-mcp-server/` to configure the running environment:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server files
COPY . .

# Run uvicorn
ENV PORT=8000
EXPOSE 8000

CMD ["python", "server.py"]
```

---

## 4. Railway Deployment Steps

### Step 1: Push Project to GitHub
1. Make sure your `credentials.json` and `token.json` are listed in your `.gitignore` so they are not committed to Git.
2. Initialize a repository and push your server code to GitHub.

### Step 2: Create a Railway Project
1. Log into [Railway](https://railway.app/).
2. Click **New Project** > **Deploy from GitHub repo**.
3. Select your repository and folder `google-mcp-server/`.

### Step 3: Configure Environment Variables
In the **Variables** tab on your Railway service dashboard, add the following key-values:

| Variable Name | Value | Purpose |
|---|---|---|
| `PORT` | `8000` | Exposes the application port. |
| `GOOGLE_CREDENTIALS_JSON` | *Paste contents of credentials.json* | Cloud client configuration. |
| `GOOGLE_TOKEN_JSON` | *Paste contents of token.json* | Pre-authorized User OAuth token (skips browser authentication). |
| `BYPASS_APPROVAL_KEY` | *Choose a secure token (e.g. `mcpserver_secret_123`)* | Authenticates incoming client API calls without terminal interaction. |

### Step 4: Verify Deployment
1. Railway will automatically build the docker container and deploy it.
2. Under the **Settings** tab, click **Generate Domain** to get a public URL (e.g., `https://google-mcp-production.up.railway.app`).
3. Verify the deployment using curl, passing the bypass header:
   ```bash
   curl -X POST https://your-app-domain.up.railway.app/create_email_draft \
        -H "Content-Type: application/json" \
        -H "X-Approval-Key: mcpserver_secret_123" \
        -d "{\"to\": \"recipient@example.com\", \"subject\": \"Railway Deployed!\", \"body\": \"This draft was created from Railway.\"}"
   ```
