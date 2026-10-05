# Main concept

We are developing a RAG system with Telegram bot as a frontend for interaction.
The system consists of database, system prompts and assistants. Assistants is the specific prompt and specific database. You can create multiple assistants on top of existed data and prompts for any purpose. Assistants can be created only by authorized users.
When user asks an assistant, system retrieves relevant to the query data from specified database and sends it to LLM with a system prompt.
Collection -- a virtual portion of data inside database application united by some kind of meaning.
System prompt -- text data used as system prompt for LLM
Assistant -- configuration that unites a database and a system prompt

Every message instead of command should be sent to specified assistant or if not specified message "Please use /assistants to see available assistants, then specify which one you want to query with /assist assistant_name"

# Commands

## Public commands

## /help
returns help from help.md as formatted md text using telegram formatted feature

## /start
gives welcome message and short description how this bot works

## /auth <password>
gives ability to user to use private commands.
when authorized, save telegram id to system database. 

## /assistants
returns a list of already configured assistants

## /assist <name>
Choose assistant by name for main RAG logic.

## Private commands

When user tries to use private command, check if User exists in system db with this telegram ID, if not tell that authorization is needed.

### /collections
returns a list of existing collections in database


### /collection_create <name>
creates new collection (in qdrant and adds it to system DB)
params: name
creates new collection then saves data to system database

### /prompts
return a list of existed prompt names, data create, date update, authors telegram username

### /prompt_create 
creates new prompt. Interactive command that asks prompt name, then asks to send prompt text
when name is given saves to system database before prompt text provided
save this data to system database

### /prompt_show <prompt_name>
returns a prompt data 

### /prompt_update <name>
updates prompt data. Interactive command that sends original name, asks if user wants to change it, then sends prompt data and asks to send new or cancel
updates data in system database

### /assistant_create
create new assistant. Interactive command asks assistant name, collection name and prompt name
saves assistant to system database

### /data_add_bulk <collection_name>
Interactive command to send bult files to load to the qdrant collection. Before start tell user to send /done when all files uploaded. When /done sent load every file as individual embedding

### /data_list <collection_name>
returns records list with ids and filenames as formated telegram table from cpecifien collection

### /data_remove <collection_name> <uuid>
Removes specified record from specified collection. Should confirm deletion.

### /data_remove_all <collection_name>
Removes all data from collections. Should confirm deletion

### /data_show <collection_name> <uuid>
return formatted telegram text contains
uuid
filename
payload

# System design

System should be implemented as main logic, business logic and api.
Main logic -- high-level logic
business logic -- bot commands implemented as python functions
api -- low level functions such as create telegram message, check auth etc.
All commands should be registered in telegram using setMyCommands api.

## System Data Objects
User:
- telegram_id: pk
- authorized: boolean

SystemPrompt:
- id: pk
- prompt_data: text

Assistant:
- id: pk
- name: string 255
- SystemPrompt.id
- collection.id
- score_threshold (default 0.6)

Collections:
- id: pk
- name: text (name of collection in Qdrant)
- description

## Qdrand Data Objects

PointStruct:
- id: uuid4 string, primary key
- filename: string
- embedding: vector
- payload: text

## Infrastructure
programming language -- python
using docker compose for environment setup; specify versions of images, latest is restricted
system should be able to use proxy server for telegram requests is configured

libraries:
  - requests

databases:
  - qdrant: RAG embeddings store
  - postgresql: system data

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
