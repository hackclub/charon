import json

from charon.db.tables import Person
from charon.db.tables import Program


async def get_update_program_modal(program_id: str) -> dict:
    program = await Program.objects().where(Program.id == int(program_id)).first()
    if not program:
        raise ValueError("Program not found")

    t_managers = await program.get_m2m(Program.managers) or []
    managers = [m for m in t_managers if isinstance(m, Person)]

    checkboxes = [
        {
            "text": {
                "type": "mrkdwn",
                "text": "*I have read the Charon docs*",
            },
            "value": "docs",
        },
        {
            "text": {
                "type": "mrkdwn",
                "text": "*I want all users to be verified through IDV before promotion* (this may be overridden with mandatory Slack verification)",
            },
            "value": "verification",
        },
    ]
    checkboxes_initial = []
    checkboxes_initial.append(checkboxes[0])
    if program.verification_required:
        checkboxes_initial.append(checkboxes[1])

    custom_user = {
        "type": "input",
        "block_id": "user_id",
        "optional": True,
        "element": {
            "type": "users_select",
            "placeholder": {"type": "plain_text", "text": "Select a user"},
            "action_id": "user_id",
        },
        "label": {
            "type": "plain_text",
            "text": "Slack user to use for inviting (must be an admin)",
        },
    }
    if program.user_id:
        custom_user["element"]["initial_user"] = program.user_id

    return {
        "type": "modal",
        "callback_id": "update_program_modal",
        "title": {
            "type": "plain_text",
            "text": "Update Invite Program",
        },
        "submit": {"type": "plain_text", "text": "Submit"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            {
                "type": "input",
                "block_id": "program_name",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "program_name",
                    "placeholder": {"type": "plain_text", "text": "Arcade"},
                    "initial_value": program.name,
                },
                "label": {"type": "plain_text", "text": "What is your program name?"},
            },
            {
                "type": "input",
                "block_id": "program_managers",
                "element": {
                    "type": "multi_users_select",
                    "placeholder": {"type": "plain_text", "text": "Select users"},
                    "action_id": "program_managers",
                    "initial_users": [m.slack_id for m in managers],
                },
                "label": {
                    "type": "plain_text",
                    "text": "Who should be able to manage your program?",
                },
            },
            {
                "type": "input",
                "block_id": "mcg_channels",
                "element": {
                    "type": "multi_channels_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select channels",
                    },
                    "action_id": "mcg_channels",
                    "initial_channels": json.loads(program.mcg_channels),
                },
                "label": {
                    "type": "plain_text",
                    "text": "Default MCG channels",
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "_all new users invited from your program will join these channels as a multi channel guest_",
                    }
                ],
            },
            {
                "type": "input",
                "block_id": "full_channels",
                "element": {
                    "type": "multi_channels_select",
                    "placeholder": {"type": "plain_text", "text": "Select channels"},
                    "action_id": "full_channels",
                    "initial_channels": json.loads(program.full_channels),
                },
                "label": {"type": "plain_text", "text": "Default full user channels"},
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "_all new users invited from your program will join these channels when they get promoted to a full user_",
                    }
                ],
            },
            {
                "type": "input",
                "block_id": "webhook",
                "element": {
                    "type": "url_text_input",
                    "action_id": "webhook",
                    "initial_value": program.webhook,
                },
                "label": {
                    "type": "plain_text",
                    "text": "Charon-compatible API endpoint for onboarding flow trigger",
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "_this URL is hit whenever a member joins Slack having been invited from your program. It should launch your onboarding flow in Slack_",
                    }
                ],
            },
            {
                "type": "input",
                "block_id": "checkboxes",
                "element": {
                    "type": "checkboxes",
                    "options": checkboxes,
                    "initial_options": checkboxes_initial,
                    "action_id": "checkboxes",
                },
                "label": {
                    "type": "plain_text",
                    "text": "Now..",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "If you would like to have a custom user such as <@U078MRX71TJ> inviting members, please enter their XOXC and XOXD below. The user must be an admin and the XOXD must be URL-decoded.",
                },
            },
            custom_user,
            {
                "type": "input",
                "block_id": "user_token",
                "optional": True,
                "element": {
                    "type": "plain_text_input",
                    "action_id": "user_token",
                    "initial_value": program.user_token or "",
                },
                "label": {
                    "type": "plain_text",
                    "text": "XOXP token (user token)",
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "_this will be used to add users to your program if they're already in Slack. Please make sure it has the scopes `channels:write.invites` and `groups:write.invites`. It must be generated by an admin user (the same that the XOXC/XOXD is for)._",
                    }
                ],
            },
            {
                "type": "input",
                "block_id": "xoxc_token",
                "optional": True,
                "element": {
                    "type": "plain_text_input",
                    "action_id": "xoxc_token",
                    "initial_value": program.xoxc_token or "",
                },
                "label": {
                    "type": "plain_text",
                    "text": "XOXC token",
                },
            },
            {
                "type": "input",
                "block_id": "xoxd_token",
                "optional": True,
                "element": {
                    "type": "plain_text_input",
                    "action_id": "xoxd_token",
                    "initial_value": program.xoxd_token or "",
                },
                "label": {
                    "type": "plain_text",
                    "text": "XOXD token",
                },
            },
        ],
        "private_metadata": str(program.id),
    }
