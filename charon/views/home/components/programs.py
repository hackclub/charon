import json
import logging

from charon.config import config
from charon.db.tables import Person
from charon.db.tables import Program
from charon.db.tables import Signup
from charon.env import env

logger = logging.getLogger(__name__)


async def get_programs(user: Person | None):
    programs = await Program.objects().where(Program.approved == True)  # noqa: E712
    user_programs = []
    other_programs = []

    for program in programs:
        blocks = []
        signups = await Signup.count().where(Signup.program_id == program.id)

        managers_table = await program.get_m2m(Program.managers) or []
        managers = [
            manager for manager in managers_table if isinstance(manager, Person)
        ]
        is_manager = user and user.slack_id in [m.slack_id for m in managers]

        logger.info(f"Program {program.name} has {signups} signups.")

        title_str = (
            f"{':double_vertical_bar: ' if not program.enabled else ''}*{program.name}*"
        )
        managers_str = (
            ", ".join([f"<@{manager.slack_id}>" for manager in managers])
            if program.managers
            else "No managers"
        )
        channels_str = (
            ", ".join([f"<#{cid}>" for cid in json.loads(program.mcg_channels)])
            if program.mcg_channels
            else "No channels"
        )

        text = f"""
{title_str}        
- *Status*: {":green_heart: Enabled" if program.enabled else ":red-x: Disabled"}
- *Managers*: {managers_str}
- *Channels*: {channels_str}
- *Identity Verification*: {":closed_lock_with_key: Required" if program.verification_required else ":unlock: Not Required"}
        """

        inviter_id = program.user_id or config.slack.user_id
        inviter_info = await env.slack_client.users_info(user=inviter_id)

        profile_pic = (
            inviter_info.get("user", {}).get("profile", {}).get("image_original")
            if inviter_info
            else None
        )

        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": text,
                },
                "accessory": {
                    "type": "image",
                    "image_url": profile_pic
                    or "https://a.slack-edge.com/80588/marketing/img/meta/slack_hash_256.png",
                    "alt_text": "Inviter Profile Picture",
                },
            }
        )

        buttons = [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "More Details", "emoji": True},
                "value": str(program.id),
                "action_id": "view_program_details",
                "style": "primary",
            }
        ]

        if user and (is_manager or user.admin):
            buttons.append(
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Edit", "emoji": True},
                    "value": str(program.id),
                    "action_id": "manage_program",
                }
            )

        blocks.append({"type": "actions", "elements": buttons})
        blocks.append({"type": "divider"})

        if is_manager:
            user_programs.extend(blocks)
        else:
            other_programs.extend(blocks)
    return user_programs, other_programs
