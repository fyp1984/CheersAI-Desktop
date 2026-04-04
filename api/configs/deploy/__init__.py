from pydantic import Field
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
