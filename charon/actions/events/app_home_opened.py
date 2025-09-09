import logging
import traceback

from slack_sdk.web.async_client import AsyncWebClient

from charon.config import config
from charon.db.tables import Person
from charon.utils.logging import send_heartbeat
from charon.views.home.error import get_error_view
from charon.views.home.loading import get_loading_view
from charon.views.home.pages.dashboard import get_dashboard_view
from charon.views.home.pages.program import get_program_view
from charon.views.home.pages.programs import get_programs_view


logger = logging.getLogger(__name__)


async def on_app_home_opened(event: dict, client: AsyncWebClient):
    user_id = event.get("user")
    if not user_id:
        logger.error("No user ID found in the app_home_opened event.")
        return
    await open_app_home("default", client, user_id)


async def open_app_home(
    home_type: str, client: AsyncWebClient, user_id: str, id: str | None = None
):
    try:
        await client.views_publish(view=get_loading_view(), user_id=user_id)
        user = await Person.objects().where(Person.slack_id == user_id).first()
        match home_type:
            case "default" | "dashboard":
                view = await get_dashboard_view(user, user_id)
            case "programs":
                view = await get_programs_view(user, user_id)
            case "program":
                if not id:
                    view = get_error_view("No program ID provided.")
                else:
                    view = await get_program_view(user, id=id)
            case "admin":
                view = get_error_view(
                    "This is a placeholder for the admin page, which is not yet implemented."
                )
            case _:
                await send_heartbeat(
                    f"Attempted to load unknown app home type {home_type} for <@{user_id}>"
                )
                view = get_error_view(
                    f"This shouldn't happen, please tell <@{config.slack.maintainer_id}> that app home case `_` was hit with home type `{home_type}`"
                )
        await client.views_publish(view=view, user_id=user_id)
    except Exception as e:
        logger.error(f"Error opening app home for {user_id}: {e}")
        tb = traceback.format_exception(e)
        tb_str = "".join(tb)

        view = get_error_view(
            f"An error occurred while opening your app home:  {e}", traceback=tb_str
        )
        err_type = type(e).__name__
        logger.error(f"Error type: {err_type}, Traceback: {tb_str}")
        await send_heartbeat(
            f"Error opening app home for <@{user_id}>: {err_type}\n{tb_str}",
            production=True,
        )
        return
