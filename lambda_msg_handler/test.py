import json
import logging
import re
import os

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from msg_handlers.tag_user_handler import handler as tag_user_handler

# SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
# slack = WebClient(token=SLACK_BOT_TOKEN)

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)

test_slack_event = '''{
    "token": "xxxxxxxxxxxx", 
    "team_id": "TCH9UHD61", 
    "context_team_id": "TCH9UHD61", 
    "context_enterprise_id": null, 
    "api_app_id": "A06V5GNDGCE", 
    "event": {
        "user": "U02NHEM6VHA",
        "type": "message",
        "ts": "1718961204.606759",
        "client_msg_id": "735777ef-21f9-4a87-9882-a4a7b4e3e5e7",
        "text": "<mailto:xu_yangbo@tech.gov.sg|xu_yangbo@tech.gov.sg>; <mailto:xu_yangbo@gmail.com|xu_yangbo@gmail.com>",
        "team": "TCH9UHD61",
        "blocks": [
            {
                "type": "rich_text",
                "block_id": "4iy6T",
                "elements": [
                    {
                        "type": "rich_text_section",
                        "elements": [
                            {
                                "type": "link",
                                "url": "mailto:xu_yangbo@tech.gov.sg",
                                "text": "xu_yangbo@tech.gov.sg",
                                "unsafe": true
                            }
                        ]
                    }
                ]
            }
        ],
        "channel": "C078QG853F1",
        "event_ts": "1718961204.606759",
        "channel_type": "channel"
    }, 
    "type": "event_callback", 
    "event_id": "Ev079267TA3X", 
    "event_time": 1718956300, 
    "authorizations": [
        {"enterprise_id": null, "team_id": "TCH9UHD61", "user_id": "U06UXKBULKH", "is_bot": true, "is_enterprise_install": false}
    ], 
    "is_ext_shared_channel": false, 
    "event_context": "4-eyJldCI6Im1lc3NhZ2UiLCJ0aWQiOiJUQ0g5VUhENjEiLCJhaWQiOiJBMDZWNUdOREdDRSIsImNpZCI6IkMwNzhRRzg1M0YxIn0"
}
'''

if __name__ == "__main__":
    tag_user_handler(json.loads(test_slack_event))
