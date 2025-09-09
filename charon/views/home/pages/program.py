from charon.db.tables import Person
from charon.db.tables import Program
from charon.views.home.components import navbar
from charon.views.home.error import get_error_view


async def get_program_view(user: Person | None, id: str):
    program = await Program.objects().where(Program.id == int(id)).first()
    if not program:
        return get_error_view("Program not found")

    btns = navbar.get_buttons(user, "programs")

    toggle_invites = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"Invites are currently {':green_heart: *enabled*' if program.enabled else ':red-x: *disabled*'}",
        },
    }
    if user:
        managers_table = await program.get_m2m(Program.managers) or []
        managers = [
            manager for manager in managers_table if isinstance(manager, Person)
        ]
        is_manager = user and user.slack_id in [m.slack_id for m in managers]
        if user.admin or is_manager:
            toggle_invites["accessory"] = {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Disable" if program.enabled else "Enable",
                    "emoji": True,
                },
                "value": id,
                "action_id": "toggle_invites",
                "style": "danger" if program.enabled else "primary",
            }

    return {
        "type": "home",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": program.name, "emoji": True},
            },
            btns,
            {"type": "divider"},
            toggle_invites,
            {
                "type": "image",
                "title": {
                    "type": "plain_text",
                    "text": "Joins over time",
                    "emoji": True,
                },
                "image_url": "https://assets3.thrillist.com/v1/image/1682388/size/tl-horizontal_main.jpg",
                "alt_text": "Joins over time",
            },
            {"type": "divider"},
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "More Info!", "emoji": True},
            },
            {
                "type": "section",
                "text": {
                    "text": "_:rac_question: does everything look good?_",
                    "type": "mrkdwn",
                },
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*Recent Joins*\n-<@U054VC2KM9P> - _2 mins ago_\n-<@U054VC2KM9P> - _2 mins ago_\n-<@U054VC2KM9P> - _2 mins ago_\n-<@U054VC2KM9P> - _2 mins ago_\n-<@U054VC2KM9P> - _2 mins ago_",
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Recent Promotions*\n-<@U054VC2KM9P> - _2 mins ago_\n-<@U054VC2KM9P> - _2 mins ago_\n-<@U054VC2KM9P> - _2 mins ago_\n-<@U054VC2KM9P> - _2 mins ago_\n-<@U054VC2KM9P> - _2 mins ago_",
                    },
                ],
            },
        ],
    }
