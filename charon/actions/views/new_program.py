import logging
import re

from slack_bolt.async_app import AsyncAck
from slack_sdk.web.async_client import AsyncWebClient

from charon.config import config
from charon.db.tables import Person
from charon.db.tables import Program
from charon.utils.logging import send_heartbeat
from charon.views.modals.new_program_submitted import get_new_program_submitted_modal

logger = logging.getLogger(__name__)


async def new_invite_program_modal(ack: AsyncAck, body: dict, client: AsyncWebClient):
    view = body["view"]
    values = view["state"]["values"]
    program_name = values["program_name"]["program_name"]["value"]
    program_managers = values["program_managers"]["program_managers"]["selected_users"]
    mcg_channels = values["mcg_channels"]["mcg_channels"]["selected_channels"]
    full_channels = values["full_channels"]["full_channels"]["selected_channels"]
    webhook = values["webhook"]["webhook"]["value"]
    checkboxes = values["checkboxes"]["checkboxes"]["selected_options"]
    custom_user_id = values["user_id"]["user_id"]["selected_user"]
    xoxc_token = values["xoxc_token"]["xoxc_token"]["value"]
    xoxd_token = values["xoxd_token"]["xoxd_token"]["value"]
    docs_read = "docs" in [c["value"] for c in checkboxes]
    verification_required = "verification" in [c["value"] for c in checkboxes]

    user_id = body["user"]["id"]
    errors = {}

    if not program_name:
        errors["program_name"] = "Program name is required."
    if not program_managers:
        errors["program_managers"] = "At least one program manager is required."
    elif user_id not in program_managers:
        errors["program_managers"] = "You must be a program manager."
    if not mcg_channels:
        errors["mcg_channels"] = "At least one MCG channel is required."
    if not full_channels:
        errors["full_channels"] = "At least one full channel is required."
    if not webhook:
        errors["webhook"] = "Webhook URL is required."
    if not re.match(
        r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)",
        webhook,
    ):
        errors["webhook"] = "Invalid webhook URL format."
    if xoxc_token and not xoxd_token:
        errors["xoxd_token"] = "XOXD token is required if XOXC token is provided."
    if xoxd_token and not xoxc_token:
        errors["xoxc_token"] = "XOXC token is required if XOXD token is provided."
    if custom_user_id and (not xoxc_token or not xoxd_token):
        errors["user_id"] = "Both XOXC and XOXD tokens are required for a custom user."
    if not custom_user_id and (xoxc_token or xoxd_token):
        errors["user_id"] = "You must select a custom user if providing tokens."
    if not docs_read:
        errors["checkboxes"] = (
            "You must read the documentation before creating a program."
        )

    if errors:
        await ack(response_action="errors", errors=errors)
        return

    unset_program = Program(
        name=program_name,
        mcg_channels=mcg_channels,
        full_channels=full_channels,
        verification_required=verification_required,
        webhook=webhook,
        user_id=custom_user_id or None,
        xoxc_token=xoxc_token or None,
        xoxd_token=xoxd_token or None,
        approved=False,
    )
    res = await Program.insert(unset_program)
    id = res[0]["id"]
    program = await Program.objects().where(Program.id == id).first()

    if not isinstance(program, Program):
        await ack(
            response_action="errors",
            errors={"program_name": "Failed to create program. Please try again."},
        )
        return

    managers = await Person.objects().where(Person.slack_id.is_in(program_managers))
    if not managers or len(managers) != len(program_managers):
        uncreated_managers = [
            slack_id
            for slack_id in program_managers
            if slack_id not in [m.slack_id for m in managers]
        ]
        logger.debug(
            f"Some program managers do not exist in the database: {uncreated_managers}"
        )
        managers = [Person(slack_id=slack_id) for slack_id in uncreated_managers]
        await Person.insert(*managers)
        managers = await Person.objects().where(Person.slack_id.is_in(program_managers))

    for manager in managers:
        await manager.add_m2m(program, m2m=Person.programs)

    await send_heartbeat(
        f":neodog_nom_stick: New program created: {program_name} (ID: {program.id})",
        client=client,
        production=True,
    )

    text = f"""
New program created: *{program_name}* (ID: {program.id})
Managers: {", ".join(f"<@{manager_slack_id}>" for manager_slack_id in program_managers)}
MCG Channels: {", ".join(f"<#{channel}>" for channel in mcg_channels)}
Full Channels: {", ".join(f"<#{channel}>" for channel in full_channels)}
Verification Required: {"Yes" if verification_required else "No"}
Webhook: {webhook}
Custom User: {"Yes" if xoxc_token and xoxd_token else "No"}
    """
    blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": text}},
        {"type": "divider"},
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Approve"},
                    "style": "primary",
                    "action_id": "approve_program",
                    "value": str(program.id),
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Reject"},
                    "style": "danger",
                    "action_id": "reject_program",
                    "value": str(program.id),
                },
            ],
        },
    ]
    await client.chat_postMessage(
        channel=config.slack.applications_channel,
        blocks=blocks,
        text=f"New program created: {program_name}",
        unfurl_links=False,
        unfurl_media=False,
    )

    await client.views_open(
        trigger_id=body["trigger_id"], view=get_new_program_submitted_modal()
    )
