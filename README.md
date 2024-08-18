## Description

The POC (Proof of Concept) aims to showcase an example of a customer service chatbot by integrating two open-source projects via API and webhooks.

1. **[Danswer](https://github.com/danswer-ai/danswer):** An open-source RAG (Retrieval-Augmented Generation) system that allows users to set up connectors to different sources and load data into a vector database. It uses advanced RAG techniques to retrieve relevant information based on a user's query and sends it to an LLM (Large Language Model) to generate an answer.

2. **[Chatwoot](https://github.com/chatwoot/chatwoot):** An open-source live chat solution that powers customer support for websites. It displays a chat window on the website where visitors can interact with customer support. Additionally, it offers a back-office platform to manage tickets created by users and allows agents to conduct discussions.

This POC aims to use Danswer as an AI agent for Chatwoot. The flow is that users joining the chat are redirected to the AI agent in Danswer.

- They can ask generic questions about the website.
- Or they can inquire about finding products (e.g., in an e-commerce setting).

## How it Works

1. **Configure a Danswer Instance and a Persona:**
    - A persona in Danswer has a prompt and a set of documents it has access to.
    - For instance, you can have a single Danswer instance with multiple scraped websites, and then create a persona for each website with access only to relevant documents/web pages for that website.

2. **Load the Website in Danswer:**
    - Loading data is simplified using the web connector and its recursive feature. Custom connectors might be needed to better clean up documents.
    - However, for the purpose of this POC, the generic web connector suffices.

3. **Configure an Agent Bot on Chatwoot:**
    - You can refer to these links for configuring and understanding the message types that can be sent to Chatwoot (e.g., cards, simple messages, select boxes):
      - [How to Use Agent Bots](https://www.chatwoot.com/hc/user-guide/articles/1677497472-how-to-use-agent-bots)
      - [Interactive Messages Documentation](https://www.chatwoot.com/docs/product/others/interactive-messages)

4. **Parameters Configuration in This Repository:**
    - Update the `login_data` in `creds.py` with your own credentials to connect to your Danswer instance.
    - `chatwoot_bot_token`: Token generated when adding the bot in the Chatwoot interface.
    - `chatwoot_url, danswer_url`: URLs of the servers hosting the Chatwoot and Danswer apps (In this example, both were running on a single VM with 16GB RAM, 4 CPU cores, using Docker Compose).
    - Using the inspection tool in the Danswer web app, you can find the `persona_id` and the `prompt_id` created for the specific persona. You need to input these in `danswer.py` (check the API call to `send-message`).

5. **Tweak the Persona:**
    - In this POC, the LLM is prompted to detect the intent of the conversation to handle three scenarios:
        - **Recommendation:** When the user asks for a product recommendation, this triggers a search request on the vector database to retrieve relevant products (documents).
        - **Generic:** The LLM replies with general knowledge without document search.
        - **Agent:** Chatwoot allows switching the ticket between the bot and a human agent. If the LLM detects a request for human assistance, it disconnects and switches the ticket status to `pending`.

**Note:** Ensure the persona prompt specifies the output message format, as it should include these patterns for parsing in `parse_response_text` to work correctly:

```python
response_pattern = r"<Response>([\s\S]*?)</Response>"
intent_pattern = r"<Intent>([\s\S]*?)</Intent>"
suggestions_pattern = r"<Suggestions>\[([\s\S]*?)\]</Suggestions>"
