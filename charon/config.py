from pydantic import model_validator
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class SlackConfig(BaseSettings):
    bot_token: str
    user_token: str
    signing_secret: str
    app_token: str | None = None
    user_id: str
    xoxc_token: str
    xoxd_token: str
    team_id: str
    heartbeat_channel: str | None = None
    applications_channel: str
    maintainer_id: str


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_nested_delimiter="__", extra="ignore"
    )
    slack: SlackConfig
    database_url: PostgresDsn
    environment: str = "development"
    port: int = 3000
    secret_key: str
    identity_base_url: str = ""

    @model_validator(mode="after")
    def set_identity_base_url(self):
        if not self.identity_base_url:
            self.identity_base_url = (
                "https://identity.hackclub.com"
                if self.environment != "development"
                else "https://idv-staging.a.hackclub.dev"
            )
        return self


config = Config()  # type: ignore
