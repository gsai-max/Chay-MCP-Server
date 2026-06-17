from googleapiclient.discovery import build
from auth import get_credentials

def append_to_doc(doc_id: str, content: str, creds=None):
    """Appends content to the end of a Google Doc body.
    
    Args:
        doc_id (str): The ID of the Google Doc.
        content (str): The text content to append.
        creds: Google API credentials (optional). If not provided, retrieved via auth.py.
        
    Returns:
        dict: The response from the batchUpdate API call.
    """
    if not creds:
        creds = get_credentials()
        
    service = build('docs', 'v1', credentials=creds)
    
    requests = [
        {
            'insertText': {
                'text': content,
                'endOfSegmentLocation': {
                    'segmentId': ''  # Empty string refers to the document body
                }
            }
        }
    ]
    
    response = service.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': requests}
    ).execute()
    
    return response
