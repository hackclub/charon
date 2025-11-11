import json
import logging
from urllib.parse import quote

from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import IPvAnyAddress

from charon.config import config
from charon.db.tables import Program
from charon.db.tables import Signup
from charon.db.tables import SignupStage
from charon.env import env
from charon.utils.logging import send_heartbeat


class UserInviteRequest(BaseModel):
    ip: IPvAnyAddress
    email: EmailStr
    channels: list[str] | None = None


logger = logging.getLogger(__name__)


async def invite_user(data: UserInviteRequest, program: Program) -> tuple[bool, str]:
    """
    Handle user invitation requests.
    """

    xoxd = (program.xoxd_token or config.slack.xoxd_token).strip()
    xoxc = (program.xoxc_token or config.slack.xoxc_token).strip()
    xoxd_token = quote(xoxd)
    channels: list[str] = (
        data.channels if data.channels else json.loads(program.mcg_channels)
    )
    channels_str = ",".join(channels)

    logger.debug(f"Inviting user {data.email} to channels: {channels_str}")

    headers = {
        "Cookie": f"d={xoxd_token}",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {xoxc}",
    }

    body = {
        "invites": [{"email": data.email, "type": "restricted", "mode": "manual"}],
        "restricted": True,
        "channels": channels_str,
    }
    msg = "successfully_invited"

    async with env.http.post(
        "https://slack.com/api/users.admin.inviteBulk",
        headers=headers,
        data=json.dumps(body),
    ) as response:
        response_json = await response.json()
        logging.debug(f"Slack response: {response_json}")
        await send_heartbeat(
            f":neodog_nom_stick: User {data.email} invited to channels {channels_str} for program {program.name}",
            [f"```{response_json}```"],
            production=True,
        )
        invite = response_json.get("invites", [{}])[0]

        ok = invite.get("ok", False)
        if not ok:
            logger.error(
                f"Failed to invite user {data.email}: {response_json.get('error', 'Unknown error')}"
            )
            await send_heartbeat(
                f":neodog_nom_stick: Failed to invite user {data.email} to channels {channels_str} for program {program.name}",
                [f"```{response_json}```"],
                production=True,
            )
            ok = False
            err = invite.get("error", "unknown_error")
            msg = err
            if err == "already_invited" or err == "already_in_team":
                ok = True  # Treat as success for our purposes
                # invite them to the channels if they are already in the team
                user_info = await env.slack_client.users_lookupByEmail(email=data.email)
                if user_info.get("ok", False):
                    user_id = user_info.get("user", {}).get("id")
                    if user_id:
                        token = program.user_token or config.slack.user_token
                        for channel in channels:
                            await env.slack_client.conversations_invite(
                                channel=channel, users=user_id, token=token
                            )
                        msg = "already_in_team"
                        return True, msg
            return False, msg

        signup = Signup(
            email=data.email,
            ip=str(data.ip),
            program_id=program.id,
            status=SignupStage.ERRORED if not ok else SignupStage.INVITED,
        )
        request = await Signup.insert(signup)
        return (True, msg) if request else (False, msg)
