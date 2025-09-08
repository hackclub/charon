from slack_bolt.async_app import AsyncAck
from slack_sdk.web.async_client import AsyncWebClient

from charon.actions.buttons.approve_reject_program import approve_reject_program_btn
from charon.actions.buttons.create_program import create_invite_program_btn
from charon.actions.commands.new_program import new_invite_program_cmd
from charon.actions.events.app_home_opened import on_app_home_opened
from charon.actions.events.app_home_opened import open_app_home
from charon.actions.events.team_join import handle_team_join
from charon.actions.views.new_program import new_invite_program_modal
from charon.env import env

app = env.app


@app.command("/new-invite-program")
async def new_invite_program(ack: AsyncAck, client: AsyncWebClient, body: dict):
    await new_invite_program_cmd(ack, body, client)


@app.action("create_program")
async def create_program_btn(ack: AsyncAck, body: dict, client: AsyncWebClient):
    await ack()
    await create_invite_program_btn(ack, body, client)


@app.view("create_program_modal")
async def create_program_modal(ack: AsyncAck, body: dict, client: AsyncWebClient):
    await ack()
    await new_invite_program_modal(ack, body, client)


@app.action("approve_program")
@app.action("reject_program")
async def approve_reject_program(
    ack: AsyncAck, body: dict, client: AsyncWebClient, action: dict
):
    await ack()
    await approve_reject_program_btn(ack, body, client, action)


@app.event("team_join")
async def team_join_event(client: AsyncWebClient, event: dict):
    """
    Handle the team_join event to welcome new users.
    """
    await handle_team_join(client, event)


@app.event("app_home_opened")
async def app_home_opened(client: AsyncWebClient, event: dict):
    """
    Handle the app_home_opened event to open the app home for the user.
    """
    user_id = event.get("user")
    if not user_id:
        return
    await on_app_home_opened(event, client)


@app.action("dashboard")
@app.action("programs")
@app.action("admin")
async def home_navigation(ack: AsyncAck, body: dict, client: AsyncWebClient):
    """
    Handle the my-programs button click to navigate to the my programs page.
    """
    await ack()
    user_id = body["user"]["id"]
    value = body["actions"][0]["action_id"]
    await open_app_home(value, client, user_id)
