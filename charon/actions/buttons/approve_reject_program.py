import logging

from slack_bolt.async_app import AsyncAck
from slack_sdk.web.async_client import AsyncWebClient

from charon.db.tables import Person
from charon.db.tables import Program
from charon.env import env
from charon.utils.cryptography import generate_api_key
from charon.utils.logging import send_heartbeat

logger = logging.getLogger(__name__)


async def approve_reject_program_btn(
    ack: AsyncAck, body: dict, client: AsyncWebClient, action: dict
) -> None:
    """
    Approve a program based on the provided button click event.
    """
    action_id = action["action_id"]
    value = action["value"]
    approved = action_id == "approve_program"
    user_id = body["user"]["id"]

    user = await Person.objects().where(Person.slack_id == user_id).first()
    if not (isinstance(user, Person) and user.admin):
        logger.error(
            f"User {user_id} is not an admin and cannot approve/reject programs"
        )
        await send_heartbeat(
            f":warning: <@{user_id}> attempted to approve/reject program `{value}` without admin permissions.",
            production=True,
        )
        await env.slack_client.chat_postEphemeral(
            user=user_id,
            channel=body["channel"]["id"],
            text=":x: You do not have permission to approve or reject programs.",
        )
        return

    if approved:
        program = await Program.objects().where(Program.id == int(value)).first()
        if isinstance(program, Program):
            if not program.approved:
                api_key = generate_api_key()
                await Program.update(
                    {Program.approved: True, Program.api_key: api_key}
                ).where(Program.id == int(value))
                managers = await program.get_m2m(Program.managers)
                logger.debug(f"Program {program.name} approved by {user_id}")
                await send_heartbeat(
                    f"<@{user_id}> approved program {program.name}", production=True
                )
                for manager in managers:
                    if isinstance(manager, Person):
                        await env.slack_client.chat_postMessage(
                            channel=manager.slack_id,
                            text=f":white_check_mark: *{program.name}* has been approved by <@{user_id}>! :tada:\n\n"
                            f"Your API Key is below, keep it safe!\n"
                            f"`{api_key}`",
                        )
            else:
                logger.error(f"Program {program.name} already approved")
                await env.slack_client.chat_postEphemeral(
                    user=user_id,
                    channel=body["channel"]["id"],
                    text=f":x: *{program.name}* has already been approved",
                )
        else:
            logger.error(f"Program with ID {value} does not exist")
            await send_heartbeat(
                f"<@{user_id}> attempted to approve non-existent program with ID {value}",
                production=True,
            )
            await env.slack_client.chat_postEphemeral(
                user=user_id,
                channel=body["channel"]["id"],
                text=f":x: Program with ID `{value}` does not exist.",
            )
    else:
        program = await Program.objects().where(Program.id == int(value)).first()
        if isinstance(program, Program):
            managers = await program.get_m2m(Program.managers)
            for manager in managers:
                if isinstance(manager, Person):
                    await env.slack_client.chat_postMessage(
                        channel=manager.slack_id,
                        text=f":x: *{program.name}* has been rejected by <@{user_id}>",
                    )

            logger.debug(f"Program {program.name} rejected by {user_id}")
            await send_heartbeat(
                f"<@{user_id}> rejected program {program.name}", production=True
            )
            await Program.delete().where(Program.id == int(value))

    message = f"_*{'Approved' if approved else 'Rejected'}* by <@{user_id}>_"

    original_msg = body["message"]
    blocks = original_msg.get("blocks", [])
    for block in blocks:
        if block.get("type") == "actions":
            blocks.remove(block)
    else:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": message}})

    await client.chat_update(
        channel=body["channel"]["id"],
        ts=original_msg["ts"],
        text=original_msg.get("text", ""),
        blocks=blocks,
    )
