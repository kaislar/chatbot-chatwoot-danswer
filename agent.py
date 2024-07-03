from flask import Flask, request, jsonify
import requests
from danswer import create_new_chat_session, process_question, login
import re 
from utils import get_images


chatwoot_url = 'http://163.172.176.163:3000'
chatwoot_bot_token = ""
danswer_url = "http://163.172.176.163:4000"
conversations = {}




card_format = {
    "content": "card message",
    "content_type":"cards",
    "content_attributes":{
        "items":[
            
        ],
    },
    "private":False
}


app = Flask(__name__)

def send_to_chatwoot(account, conversation, data):
    url = f"{chatwoot_url}/api/v1/accounts/{account}/conversations/{conversation}/messages"
    headers = {"Content-Type": "application/json",
               "Accept": "application/json",
               "api_access_token": f"{chatwoot_bot_token}"}

    r = requests.post(url,json=data, headers=headers)
    return r.json()

def parse_response_text(text):
    response_pattern = r"<Response>([\s\S]*?)</Response>"
    intent_pattern = r"<Intent>([\s\S]*?)</Intent>"
    suggestions_pattern = r"<Suggestions>\[([\s\S]*?)\]</Suggestions>"
    suggestions_pattern = r"<Suggestions>(?:\[([\s\S]*?)\]|\[\[([\d\s,]*)\]\])</Suggestions>"

    response_match = re.search(response_pattern, text)
    intent_match = re.search(intent_pattern, text)
    suggestions_match = re.search(suggestions_pattern, text)
    response = response_match.group(1) if response_match else None
    intent = intent_match.group(1) if intent_match else None
    # Define the combined regex pattern
    
    suggestions=None
    matches = re.search(suggestions_pattern, text)
    if matches:
        # Check which capturing group matched
        if matches.group(1):
            suggestions = matches.group(1).strip()
        elif matches.group(2):
            suggestions = matches.group(2).strip()
    if suggestions:
        try:
            suggestions = [int(s) for s in suggestions.split(", ")] if suggestions else []
        except:
            pass
    else:
        suggestions = []

    return  response, intent, suggestions

def give_hand_to_agent(account, conversation):
    url = f"{chatwoot_url}/api/v1/accounts/{account}/conversations/{conversation}/toggle_status/"


    # Set the headers
    headers = {"Content-Type": "application/json; charset=utf-8",
            "api_access_token": f"{chatwoot_bot_token}"
            }

    # Define the payload to update the status
    payload = {
        "status": "open"
    }
    # Send the PUT request to update the conversation status
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

def build_chatwoot_cards(intent, suggestions,top_documents):
    if intent=="Reco": 
        list_cards=[]
        if top_documents:
            for i in suggestions:
                current_doc = top_documents[i-1]
                card_item = {
                "media_url":get_images(current_doc["link"]),
                "title":current_doc["semantic_identifier"],
                "description":"",#current_doc["match_highlights"][0],
                "actions":[
                    {
                    "type":"link",
                    "text":"View More",
                    "uri":current_doc["link"]
                    },
                 ]
                }
                list_cards.append(card_item)
            if list_cards:
                card_format["content_attributes"]["items"] = list_cards
                return card_format
    return None

session=login()

@app.route('/webhook-bot', methods=['POST']) # type: ignore
def test():
    print(f"list conversations {conversations}")
    chatwoot_msg = ''
    data = request.get_json()
    message_type = data.get('message_type')
    try: 
        bot_response = not(conversations[data.get('conversation')['id']]["forwarded_agent"]) 
    except:
        bot_response = True

    if message_type == 'incoming' and bot_response:
        message = data.get('content')
        conversation = data.get('conversation')['id']
        contact = data['sender']['id']
        account = data['account']['id']

        if conversation in conversations: 
            print("existant conversation")
            chat_session_id = conversations[conversation]["chat_session_id"]
        else:
            print("creating new conversation")
            chat_session_id = create_new_chat_session(danswer_url, session) 
            conversations[conversation]= {"chat_session_id": chat_session_id}
            conversations[conversation].update({"parent_message_id": None})

        response, response_text, message_id, parent_message_id, top_documents = process_question(danswer_url, question = message, session = session, chat_session_id = chat_session_id, previous_message = conversations[conversation])
        conversations[conversation]["parent_message_id"] = message_id
        print("response_text" , response_text)

        response, intent, suggestions = parse_response_text(response_text)

        print("-"*100)
        print("response_text" , response_text)
        print("this message id:",message_id)
        print("parent message:", parent_message_id)
        print("top_documents:", top_documents)
        print("HERE IS FINAL RESPONSE:",response)
        print("HERE IS FINAL INTENT:",intent)
        print("HERE IS FINAL LIST SUGGESTIONS:", suggestions)
        print("-"*100)

        chatwood_cards=build_chatwoot_cards(intent,suggestions, top_documents)
        chatwoot_msg = send_to_chatwoot(account, conversation, {'content': response})
        if chatwood_cards:
            send_to_chatwoot(account, conversation, chatwood_cards)
        if intent == 'Talk_agent':
            conversations[conversation]["forwarded_agent"]=True
            give_hand_to_agent(account, conversation)

    return chatwoot_msg

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3010)
