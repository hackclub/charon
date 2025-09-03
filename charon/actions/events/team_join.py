import logging

from slack_sdk.web.async_client import AsyncWebClient

from charon.db.tables import Program
from charon.db.tables import Signup
from charon.db.tables import SignupStage
from charon.env import env

logger = logging.getLogger(__name__)


async def handle_team_join(client: AsyncWebClient, event: dict):
    """
    Handle the team_join event to welcome new users.
    """

    user_id = event.get("user", {}).get("id")
    if not user_id:
        return

    user_info = await client.users_info(user=user_id)
    user = user_info.get("user", {})
    if not user or not user_info.get("ok", False):
        logger.error(
            f"Failed to fetch user info for {user_id}: {user.get('error', 'Unknown error')}"
        )
        return

    email = user.get("profile", {}).get("email")
    if not email:
        logger.warning("No email found for the new user.")
        return

    # Check if the user is already in the database
    existing_user = await Signup.objects().where(Signup.email == email).first()

    # If user wasn't invited through Charon, create a record for direct join tracking
    if not existing_user:
        logger.info(
            f"User {email} joined directly (not through Charon). Creating tracking record."
        )
        existing_user = Signup(
            email=email,
            slack_id=user_id,
            status=SignupStage.JOINED
            if user.get("is_restricted")
            else SignupStage.PROMOTED,
            program_id=None,
        )
        await existing_user.save()

        return

    # For users who were invited through Charon, continue with the existing flow
    if existing_user.program_id is None:
        logger.error(
            f"This should not happen - user {email} has no program_id but was found in database"
        )
        return

    program = (
        await Program.objects().where(Program.id == existing_user.program_id).first()
    )

    if not program:
        logger.error(f"Program not found for user {email}.")
        return

    # Send request to program's API

    event["user"]["profile"]["email"] = email

    async with env.http.post(program.webhook, json=event) as response:
        if response.status < 200 or response.status >= 300:
            logger.error(
                f"Failed to send event to {program.name} webhook: {response.status}"
            )
            return

    # Send a welcome message to the new user
    try:
        await client.chat_postMessage(
            channel=user_id,
            text=f"Welcome! If you have any questions, feel free to ask. I see you joined from {program.name}",
        )
    except Exception as e:
        logger.error(f"Failed to send welcome message: {e}")

    await Signup.update(
        {
            "status": SignupStage.JOINED,
            "slack_id": user_id,
        }
    ).where(Signup.id == existing_user.id)
