import json
import logging
from urllib.parse import quote

from fastapi.responses import JSONResponse
from pydantic import BaseModel

from charon.config import config
from charon.db.tables import Program
from charon.db.tables import Settings
from charon.db.tables import Signup
from charon.db.tables import SignupStage
from charon.env import env
from charon.utils.identity import check_identity
from charon.utils.identity import VerificationStatus
from charon.utils.logging import send_heartbeat


class UserPromoteRequest(BaseModel):
    id: str
    channels: list[str] | None = None


logger = logging.getLogger(__name__)


async def promote_user(data: UserPromoteRequest, program: Program) -> JSONResponse:
    """
    Handle user promotion requests.
    """

    verification_required = program.verification_required
    if not verification_required:
        global_settings = await Settings.objects().first()
        verification_required = (
            not global_settings or global_settings.global_verification
        )
        if not global_settings:
            logger.error("This should never happen, but global settings not found.")

    user_info = await env.slack_client.users_info(user=data.id)
    if not user_info.get("ok", False):
        logger.error(
            f"Failed to fetch user info for {data.id}: {user_info.get('error', 'Unknown error')}"
        )
        return JSONResponse(
            status_code=404,
            content={
                "ok": False,
                "message": "user_not_found",
            },
        )
    user = user_info.get("user", {})
    email = user.get("profile", {}).get("email")
    if not email:
        logger.error(f"User {data.id} does not have an email address")
        return JSONResponse(
            status_code=422,
            content={
                "ok": False,
                "message": "email_not_found",
            },
        )

    verification_status = await check_identity(email)
    if verification_status == VerificationStatus.VERIFIED_BUT_OVER_18:
        logger.info(f"User {data.id} is over 18, not promoting")

        return JSONResponse(
            status_code=422,
            content={
                "ok": False,
                "message": "adult",
            },
        )
    if (
        verification_required
        and verification_status != VerificationStatus.VERIFIED_ELIGIBLE
    ):
        logger.info(
            f"User {data.id} is not eligible for promotion: {verification_status}"
        )

        return JSONResponse(
            status_code=422,
            content={
                "ok": False,
                "message": "verification_failed",
            },
        )

    xoxd = (program.xoxd_token or config.slack.xoxd_token).strip()
    xoxc = (program.xoxc_token or config.slack.xoxc_token).strip()
    xoxd_token = quote(xoxd)
    channels: list[str] = (
        data.channels if data.channels else json.loads(program.full_channels)
    )
    channels_str = ",".join(channels)

    logger.debug(f"Promoting user {data.id} with channels: {channels_str}")

    headers = {
        "Cookie": f"d={xoxd_token}",
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {xoxc}",
    }

    body = {"user": data.id}

    async with env.http.post(
        f"https://slack.com/api/users.admin.setRegular?slack_route=${config.slack.team_id}&user={data.id}",
        headers=headers,
        data=json.dumps(body),
    ) as response:
        response_json = await response.json()
        logging.debug(f"Slack response: {response_json}")
        await send_heartbeat(
            f":neodog_nom_stick: User {data.id} promoted by program {program.name}",
            [f"```{body}```", f"```{response_json}```"],
            production=True,
        )

        ok = True
        if not response_json["ok"]:
            logger.error(
                f"Failed to promote user {data.id}: {response_json.get('error', 'Unknown error')}"
            )
            await send_heartbeat(
                f":neodog_nom_stick: Failed to promote user {data.id} to channels {channels_str} for program {program.name}",
                [f"```{response_json}```"],
                production=True,
            )
            ok = False

        signup = await Signup.objects().where(Signup.slack_id == data.id).first()
        if not signup:
            logger.error(f"Signup not found for user {data.id}")
            return JSONResponse(
                status_code=404,
                content={
                    "ok": False,
                    "message": "signup_not_found",
                },
            )

        signups = await Signup.update(
            {Signup.status: SignupStage.PROMOTED, Signup.slack_id: data.id}
            if ok
            else {Signup.status: SignupStage.ERRORED, Signup.slack_id: data.id}
        ).where(Signup.id == signup.id)

        signup = signups[0] if signups else signup

        # Dispatch the upgrade to Professor Bloom
        if config.bloom_token:
            env.http.post(
                f"https://professorbloom.hackclub.com/webhook/charon/{config.bloom_token}",
                data=json.dumps({
                    "user_id": data.id,
                    "program_id": program.id,
                    "program_name": program.name,
                    "action": "promotion"
                }),
                headers={"Content-Type": "application/json"}
            )

        return JSONResponse(
            status_code=200 if ok else 422,
            content={
                "ok": ok,
                "message": "promotion_success" if ok else "promotion_fail",
                "signup": {
                    "id": signup.id,
                    "email": signup.email,
                    "status": signup.status,
                    "program_id": signup.program_id,
                },
            },
        )
