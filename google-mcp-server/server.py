import os
import sys
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from auth import get_credentials
from docs_tool import append_to_doc
from gmail_tool import create_email_draft

app = FastAPI(
    title="Google Docs & Gmail MCP Server",
    description="A complete MCP-style server for interacting with Google Docs and Gmail with terminal approval.",
    version="1.0.0"
)

# Request Payloads
class AppendDocPayload(BaseModel):
    doc_id: str
    content: str

class CreateEmailDraftPayload(BaseModel):
    to: str
    subject: str
    body: str

def get_terminal_approval(action_name: str, payload: dict) -> bool:
    """Prints action details to the terminal and waits for manual user approval.
    
    Since FastAPI runs standard synchronous handlers (defined with `def` rather than `async def`)
    in a thread pool, this blocking input operation will not block the main event loop.
    """
    print("\n" + "=" * 50)
    print("PENDING ACTION APPROVAL")
    print(f"Action: {action_name}")
    print("Payload:")
    for key, value in payload.items():
        print(f"  {key}: {value}")
    print("=" * 50)
    
    while True:
        try:
            response = input("Approve? (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Invalid input. Please enter 'y' or 'n'.")
        except (KeyboardInterrupt, EOFError):
            print("\nAction cancelled or terminal input unavailable.")
            return False

@app.post("/append_to_doc")
def append_to_doc_endpoint(payload: AppendDocPayload, x_approval_key: str = Header(None)):
    bypass_key = os.environ.get("BYPASS_APPROVAL_KEY")
    if bypass_key and x_approval_key == bypass_key:
        approved = True
    else:
        # Print the action details and request console approval
        approved = get_terminal_approval("Append to Google Doc", payload.model_dump())
        
    if not approved:
        raise HTTPException(status_code=403, detail="Action rejected by user")
    
    try:
        # Retrieves credentials (will trigger browser OAuth if credentials.json is present and token.json is not)
        creds = get_credentials()
        response = append_to_doc(payload.doc_id, payload.content, creds)
        return {"status": "success", "response": response}
    except FileNotFoundError as fnf_err:
        raise HTTPException(status_code=400, detail=str(fnf_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to append to document: {str(e)}")

@app.post("/create_email_draft")
def create_email_draft_endpoint(payload: CreateEmailDraftPayload, x_approval_key: str = Header(None)):
    bypass_key = os.environ.get("BYPASS_APPROVAL_KEY")
    if bypass_key and x_approval_key == bypass_key:
        approved = True
    else:
        # Print the action details and request console approval
        approved = get_terminal_approval("Create Gmail Draft", payload.model_dump())
        
    if not approved:
        raise HTTPException(status_code=403, detail="Action rejected by user")
        
    try:
        # Retrieves credentials
        creds = get_credentials()
        response = create_email_draft(payload.to, payload.subject, payload.body, creds)
        return {"status": "success", "response": response}
    except FileNotFoundError as fnf_err:
        raise HTTPException(status_code=400, detail=str(fnf_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create email draft: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting Google MCP Server on http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
