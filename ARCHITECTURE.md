# Main concept

We developing RAG System with telegram bot as a frontend for interaction. 
The systems consists of database, system prompts and assistants. Assistans is the specific prompt and specific database. You can create multiple assistants on top of existed data and promps for any purpose. Assistans can be create only by authorized users.
When user asks an assistant, system retrieves relevand to the query data from specified database and sends it to LLM with a system prompt.

Database -- a virtual portion of data inside database application united by some king of meaning.

System prompt -- text data used as system prompt for LLM

Assistant -- configuration that unites a database and a system prompt

# Commands

## Public commands

/start -- gives welcome message and short description how this bot works

/auth <password> -- gives ability to user to configure the system

/list-assistants -- returns a list of already configured assistants

## Private commands
/database-list -- returns a list of existed databases
/database-create -- creates new database
/propmt-list -- return a list of existed promprts
/propmt-create -- creates new prompt
/prompt-show -- returns a prompt data
/prompt-update -- updates prompt data

# System design

System should be implemented as main logic, business logic and api. 
Main logic -- highlevel login
businss logic -- bot commands implemented as python functions
api -- low level functions such as (create telegram message, check auth etc.)

## Infrastructure
programming language -- python
using docker compose for environment setup; specify versions of images, latest is restricted
system should be able to use proxy server for telegram requests is configured

libraries:
  - requests
databases:
  - qdrant
models:
  - minimax  
  - BAAI/bge-m3 [embedding]
## Configuration
TELEGRAM_BOT_API
LLM_APIKEY
LLM_ENDPOINT
PROXY_URL
## Telegram
The system should be able to use webhooks or polling. This ability is configured with config.py
