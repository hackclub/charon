import logging
import re

from slack_bolt.async_app import AsyncAck
from slack_sdk.web.async_client import AsyncWebClient

from charon.actions.events.app_home_opened import open_app_home
from charon.config import config
from charon.db.tables import Person
from charon.db.tables import PersonProgramLink
from charon.db.tables import Program
from charon.utils.logging import send_heartbeat
from charon.views.modals.new_program_submitted import get_new_program_submitted_modal

logger = logging.getLogger(__name__)


async def upsert_invite_program_modal(
    ack: AsyncAck, body: dict, client: AsyncWebClient
):
    view = body["view"]
    values = view["state"]["values"]
    program_name = values["program_name"]["program_name"]["value"]
    program_managers = values["program_managers"]["program_managers"]["selected_users"]
    mcg_channels = values["mcg_channels"]["mcg_channels"]["selected_channels"]
    full_channels = values["full_channels"]["full_channels"]["selected_channels"]
    webhook = values["webhook"]["webhook"]["value"]
    checkboxes = values["checkboxes"]["checkboxes"]["selected_options"]
    custom_user_id = values["user_id"]["user_id"]["selected_user"]
    user_token = values["user_token"]["user_token"]["value"]
    xoxc_token = values["xoxc_token"]["xoxc_token"]["value"]
    xoxd_token = values["xoxd_token"]["xoxd_token"]["value"]
    docs_read = "docs" in [c["value"] for c in checkboxes]
    verification_required = "verification" in [c["value"] for c in checkboxes]
    id = view.get("private_metadata")
    if id:
        id = int(id)

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
            errors["user_id"] = (
                "Both XOXC and XOXD tokens are required for a custom user."
            )
        if not custom_user_id and (xoxc_token or xoxd_token):
            errors["user_id"] = "You must select a custom user if providing tokens."
        if xoxc_token and xoxd_token and custom_user_id and not user_token:
            errors["user_token"] = (
                "User token is required if XOXC token, XOXD token, and custom user ID are provided."
            )

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
    )
    existing_program = False
    program_id = None

    if id:
        # We're updating an existing program. Use the provided id as the program id.
        existing_program = True
        await Program.update(
            {
                Program.name: unset_program.name,
                Program.mcg_channels: unset_program.mcg_channels,
                Program.full_channels: unset_program.full_channels,
                Program.verification_required: unset_program.verification_required,
                Program.webhook: unset_program.webhook,
                Program.user_id: unset_program.user_id,
                Program.xoxc_token: unset_program.xoxc_token,
                Program.xoxd_token: unset_program.xoxd_token,
            }
        ).where(Program.id == id)
        program_id = id
    else:
        # Insert a new program. The insert may return a list with the new id, but it
        # might also return an empty list on failure — handle that safely.
        existing_program = False
        res = await Program.insert(unset_program)
        if res and isinstance(res, (list, tuple)) and len(res) > 0 and "id" in res[0]:
            program_id = res[0]["id"]

    if not program_id:
        await ack(
            response_action="errors",
            errors={
                "program_name": f"Failed to {'update' if existing_program else 'create'} program. Please try again."
            },
        )
        return

    # Normalize to `id` for the rest of the function
    id = program_id
    program = await Program.objects().where(Program.id == id).first()

    if not isinstance(program, Program):
        await ack(
            response_action="errors",
            errors={
                "program_name": f"Failed to {'update' if existing_program else 'create'} program. Please try again."
            },
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

    existing_links = (
        await PersonProgramLink.select(PersonProgramLink.user_id)
        .where(
            PersonProgramLink.program_id == program.id,
            PersonProgramLink.user_id.is_in([m.id for m in managers]),
        )
        .output(as_list=True)
    )

    missing_manager_ids = [m.id for m in managers if m.id not in existing_links]

    if missing_manager_ids:
        links = [
            PersonProgramLink(user_id=manager_id, program_id=program.id)
            for manager_id in missing_manager_ids
        ]
        await PersonProgramLink.insert(*links)

    await send_heartbeat(
        f":neodog_nom_stick: New program {'updated' if id else 'created'}: {program_name} (ID: {program.id})",
        client=client,
        production=True,
    )

    if not existing_program:
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

    else:
        await open_app_home("programs", client, user_id)
