from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class DeploymentConfig(BaseSettings):
    """
    Configuration settings for application deployment
    """

    APPLICATION_NAME: str = Field(
        description="Name of the application, used for identification and logging purposes",
        default="langgenius/dify",
    )

    DEBUG: bool = Field(
        description="Enable debug mode for additional logging and development features",
        default=False,
    )

    @field_validator("DEBUG", mode="before")
    @classmethod
    def _normalize_debug_value(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "production", "prod"}:
                return False
            if normalized in {"debug", "development", "dev"}:
                return True
        return value

    # Request logging configuration
    ENABLE_REQUEST_LOGGING: bool = Field(
        description="Enable request and response body logging",
        default=False,
    )

    EDITION: str = Field(
        description="Deployment edition of the application (e.g., 'SELF_HOSTED', 'CLOUD')",
        default="SELF_HOSTED",
    )

    DEPLOY_ENV: str = Field(
        description="Deployment environment (e.g., 'PRODUCTION', 'DEVELOPMENT'), default to PRODUCTION",
        default="PRODUCTION",
    )

    # SSO Configuration
    SSO_API_URL: str = Field(
        description="SSO API base URL for authentication",
        default="",
    )

    DESKTOP_SSO_CLIENT_ID: str = Field(
        description="OAuth2 client ID for Desktop SSO",
        default="",
    )

    DESKTOP_SSO_CLIENT_SECRET: str = Field(
        description="OAuth2 client secret for Desktop SSO",
        default="",
    )

    SSO_PROVISION_OWNER: str = Field(
        description="SSO owner used when provisioning beta users",
        default="CheersAI",
    )

    SSO_PROVISION_CLIENT_ID: str = Field(
        description="Client ID used for SSO beta user provisioning",
        default="",
    )

    SSO_PROVISION_CLIENT_SECRET: str = Field(
        description="Client secret used for SSO beta user provisioning",
        default="",
    )

    SSO_PROVISION_DEFAULT_ROLE: str = Field(
        description="Default SSO role assigned to approved beta users",
        default="desktop_team_member",
    )

    SSO_PROVISION_SIGNUP_APPLICATION: str = Field(
        description="Signup application name written to SSO user records",
        default="CheersAI-Desktop",
    )

    GITEA_URL: str = Field(
        description="Gitea/FileBay base URL",
        default="",
    )

    FILEBAY_BASE_URL: str = Field(
        description="FileBay base URL for beta user provisioning",
        default="",
    )

    FILEBAY_ADMIN_USERNAME: str = Field(
        description="FileBay admin username used for beta provisioning",
        default="",
    )

    FILEBAY_ADMIN_PASSWORD: str = Field(
        description="FileBay admin password used for beta provisioning",
        default="",
    )

    FILEBAY_DEFAULT_REPO: str = Field(
        description="Default private repository name created for beta users",
        default="desktop-sync-files",
    )

    FILEBAY_DEFAULT_BRANCH: str = Field(
        description="Default branch used when initializing beta user repositories",
        default="main",
    )

    FILEBAY_DEFAULT_MASKED_DIR: str = Field(
        description="Default masked directory path initialized in FileBay repositories",
        default="masked",
    )

    BETA_PROVISION_HTTP_TIMEOUT: int = Field(
        description="HTTP timeout in seconds for beta provisioning calls",
        default=10,
    )

    BETA_PROVISION_LOCK_TIMEOUT: int = Field(
        description="Distributed lock timeout in seconds for beta provisioning per application",
        default=600,
    )

    BETA_PROVISION_MAX_MANUAL_RETRY: int = Field(
        description="Maximum number of manual retries allowed after the initial provisioning attempt",
        default=5,
    )

    BETA_ENABLE_NEXUS_RESOURCE_INIT: bool = Field(
        description="Whether to execute step6 Nexus resource initialization during beta provisioning",
        default=False,
    )

    BETA_PROVISION_SSL_VERIFY: bool = Field(
        description="Whether SSL certificates should be verified during beta provisioning",
        default=True,
    )

    BETA_NOTIFICATION_DESKTOP_URL: str = Field(
        description="Desktop login entry used in beta approval notification emails",
        default="",
    )

    BETA_NOTIFICATION_SSO_LOGIN_URL: str = Field(
        description="SSO login entry used in beta approval notification emails",
        default="",
    )
