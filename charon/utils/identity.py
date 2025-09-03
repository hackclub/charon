import logging
from enum import Enum

from charon.config import config
from charon.env import env

logger = logging.getLogger(__name__)


class VerificationStatus(Enum):
    NOT_FOUND = "not_found"
    NEEDS_SUBMISSION = "needs_submission"
    PENDING = "pending"
    REJECTED = "rejected"
    VERIFIED_ELIGIBLE = "verified_eligible"
    VERIFIED_BUT_OVER_18 = "verified_but_over_18"

    def __str__(self):
        return self.value

    @classmethod
    def from_string(cls, value: str):
        for status in cls:
            if status.value == value:
                return status
        raise ValueError(f"Unknown VerificationStatus: {value}")


async def check_identity(email: str) -> VerificationStatus:
    api_endpoint = f"{config.identity_base_url}/api/external/check?email={email}"

    async with env.http.get(api_endpoint) as response:
        if response.status != 200:
            raise Exception(f"Failed to check identity: {response.status}")

        data = await response.json()

        status = data.get("result")
        if not status:
            return VerificationStatus.NOT_FOUND

        logger.info(f"Identity check for {email}: {status}")
        return VerificationStatus.from_string(status)
