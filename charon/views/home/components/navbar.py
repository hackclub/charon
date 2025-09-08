from charon.db.tables import Person


def get_buttons(person: Person | None, current: str = "dashboard"):
    buttons = []

    buttons.append(
        {
            "type": "button",
            "text": {"type": "plain_text", "text": "Dashboard", "emoji": True},
            "action_id": "dashboard",
            **({"style": "primary"} if current != "dashboard" else {}),
        }
    )

    buttons.append(
        {
            "type": "button",
            "text": {"type": "plain_text", "text": "Programs", "emoji": True},
            "action_id": "programs",
            **({"style": "primary"} if current != "programs" else {}),
        }
    )

    if person and person.admin:
        buttons.append(
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Admin", "emoji": True},
                "action_id": "admin",
                **({"style": "primary"} if current != "admin" else {}),
            }
        )

    blocks = {"type": "actions", "elements": buttons}
    return blocks
