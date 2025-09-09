from slack_bolt.async_app import AsyncAck
from slack_sdk.web.async_client import AsyncWebClient

from charon.actions.events.app_home_opened import open_app_home
from charon.db.tables import Person
from charon.db.tables import Program
from charon.utils.logging import send_heartbeat


async def toggle_invites_btn(ack: AsyncAck, body: dict, client: AsyncWebClient):
    program_id = body["actions"][0]["value"]
    user_id = body["user"]["id"]

    program = await Program.objects().where(Program.id == int(program_id)).first()
    if not program:
        await send_heartbeat(
            f"Program with ID {program_id} not found for toggle_invites_btn by <@{user_id}>",
            production=True,
        )
        return
    user = await Person.objects().where(Person.slack_id == user_id).first()
    if not user:
        await send_heartbeat(
            f"User with Slack ID {user_id} not found for toggle_invites_btn",
            production=True,
        )
        return

    if not user.admin:
        managers_table = await program.get_m2m(Program.managers) or []
        managers = [
            manager for manager in managers_table if isinstance(manager, Person)
        ]
        is_manager = user and user.slack_id in [m.slack_id for m in managers]
        if not is_manager:
            await send_heartbeat(
                f"Unauthorized toggle_invites_btn attempt by <@{user_id}> on program ID {program_id}",
                production=True,
            )
            return

    program.enabled = not program.enabled
    await program.save()
    await send_heartbeat(
        f"Invites for program ID {program_id} {'enabled' if program.enabled else 'disabled'} by <@{user_id}>",
        production=True,
    )
    await open_app_home("program", client, user_id, id=program_id)
