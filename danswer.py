# This file is used to demonstrate how to use the backend APIs directly
# In this case, the equivalent of asking a question in Danswer Chat in a new chat session
import argparse
import json
import os
from typing import Optional, Dict
import requests
from creds import danswer_url,login_data

#TRAVEL
persona_id = 2
prompt_id = 5

#Ecommerce
#persona_id = 3
#prompt_id = 6


#As Monaco
#persona_id = 4
#prompt_id = 7

headers = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded"
}


# Define the login function
def login() -> requests.Session:
    login_endpoint = danswer_url + "/api/auth/login"
    # Headers to be sent with the request

    session = requests.Session()
    
    response = session.post(login_endpoint, data=login_data, headers=headers)
    
    return session


def create_new_chat_session(danswer_url: str, session: requests.Session) -> int:
    session_endpoint = danswer_url + "/api/chat/create-chat-session"

    response = session.post(
        session_endpoint,
        json={"persona_id": persona_id},  # Global default Persona/Assistant ID
    )

    new_session_id = response.json()["chat_session_id"]
    return new_session_id


def process_question(danswer_url: str, question: str, session: requests.Session, chat_session_id: str | None,     previous_message: Optional[Dict] = None):
    message_endpoint = danswer_url + "/api/chat/send-message"
    if chat_session_id is None:
        chat_session_id = create_new_chat_session(danswer_url, session)
        print(f"Created new session ID {chat_session_id}")
    else: 
        print(f"Use chat_session id {chat_session_id}")
    
    data = {
        "message": question,
        "chat_session_id": chat_session_id,
        "parent_message_id": previous_message.get("parent_message_id"),
        # Default Question Answer prompt
        "prompt_id": prompt_id,
        "search_doc_ids": None,
        "file_descriptors": [],
        "retrieval_options": {
            "run_search": "auto",
            "real_time": True,
            "filters": {
            "source_type": None,
            "document_set": None,
            "time_cutoff": None,
            "tags": []
            }
        },
        "prompt_override": None,
        "llm_override": None   
    }

    response_text = ""
    message_id = None
    parent_message_id = None
    top_documents = []
    headers = {}
    with session.post(message_endpoint, headers={}, json=data) as response:
        for packet in response.iter_lines():
            response_json = json.loads(packet.decode())
            
            # Extracting necessary fields
            if not message_id:
                message_id = response_json.get("message_id")
            if not parent_message_id:
                parent_message_id = response_json.get("parent_message")
            if "top_documents" in response_json:
                top_documents.extend(response_json["top_documents"])
            if "message" in response_json:
                response_text =response_json["message"]
           
            #new_token = response_json.get("answer_piece")
            #if new_token:
            #    response_text += new_token

    return response, response_text, message_id, parent_message_id, top_documents



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sample API Usage")
    parser.add_argument(
        "--danswer-url",
        type=str,
        default="http://localhost:4000",
        help="Danswer URL, should point to Danswer nginx.",
    )
    parser.add_argument(
        "--test-question",
        type=str,
        default="What is Danswer?",
        help="Test question for new Chat Session.",
    )

    # Not needed if Auth is disabled
    # Or for Danswer MIT API key must be replaced with session cookie
    api_key = os.environ.get("DANSWER_API_KEY")

    args = parser.parse_args()
    process_question(
        danswer_url=args.danswer_url, question=args.test_question, api_key=api_key
    )
