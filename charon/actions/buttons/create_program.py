from slack_bolt.async_app import AsyncAck
from slack_sdk.web.async_client import AsyncWebClient

from charon.views.modals.new_program import get_new_program_modal


async def create_invite_program_btn(ack: AsyncAck, body: dict, client: AsyncWebClient):
    """
    Handle the create program button action.
    """
    user_id = body.get("user", {}).get("id")
    if not user_id:
        return
    trigger_id = body.get("trigger_id")
    if not trigger_id:
        return

    view = get_new_program_modal(user_id=user_id)

    await client.views_open(
        trigger_id=trigger_id,
        view=view,
    )
