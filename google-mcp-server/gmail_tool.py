import base64
from email.message import EmailMessage
from googleapiclient.discovery import build
from auth import get_credentials

def create_email_draft(to: str, subject: str, body: str, creds=None):
    """Creates an email draft in Gmail.
    
    Args:
        to (str): Recipient email address.
        subject (str): Email subject.
        body (str): Email body content.
        creds: Google API credentials (optional). If not provided, retrieved via auth.py.
        
    Returns:
        dict: The response from the Gmail drafts.create API call.
    """
    if not creds:
        creds = get_credentials()
        
    service = build('gmail', 'v1', credentials=creds)
    
    # Construct the message
    message = EmailMessage()
    message.set_content(body)
    message['To'] = to
    message['Subject'] = subject
    
    # Encode the message in URL-safe base64
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    create_body = {
        'message': {
            'raw': raw_message
        }
    }
    
    response = service.users().drafts().create(
        userId='me',
        body=create_body
    ).execute()
    
    return response
