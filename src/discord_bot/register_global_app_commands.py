import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

application_id = os.getenv('APPLICATION_ID')
bot_token = os.getenv('DISCORD_BOT_TOKEN')

if application_id is None or bot_token is None:
    raise KeyError("Could not read application id or bot token env variables")

url = f"https://discord.com/api/v10/applications/{application_id}/commands"

chat_commands = [
    {
        "name": "index",
        "type": 1,
        "description": "index a database",
        "options": [
            {
                "name": "github_url",
                "description": "the github url to index before querying",
                "required": True,
                "type": 3 # option type 3 is string
            },
        ]
    },
    {
        "name": "query",
        "type": 1,
        "description": "query a database",
        "options": [
            {
                "name": "question",
                "description": "the question to ask",
                "required": True,
                "type": 3
            },
            {
                "name": "github_url",
                "description": "the github url to query",
                "required": False,
                "type": 3,
            },

        ]
    }
]

headers = {
    "Authorization": f"Bot {bot_token}"
}

for cmd in chat_commands:
    print(cmd['name'], ":", end='')
    r = requests.post(url, headers=headers, json=cmd)
    if r.status_code >= 300:
        print("Recieved non-ok response: ", json.dumps(r.json(), indent=4))
    else:
        print("Success")
