import logging

from charon.db.tables import Person
from charon.views.home.components import navbar
from charon.views.home.components.programs import get_programs

logger = logging.getLogger(__name__)


async def get_programs_view(user: Person | None, slack_id: str):
    btns = navbar.get_buttons(user, "programs")
    own_program_cards, other_program_cards = await get_programs(user)

    return {
        "type": "home",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":rac_woah: Invite Programs",
                    "emoji": True,
                },
            },
            btns,
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Looking for something new? Create it!",
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": ":miiverse-yeah: Create Program",
                        "emoji": True,
                    },
                    "action_id": "create_program",
                },
            },
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Your Programs!",
                    "emoji": True,
                },
            },
            *own_program_cards,
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Everything Else!",
                    "emoji": True,
                },
            },
            *other_program_cards,
        ],
    }
