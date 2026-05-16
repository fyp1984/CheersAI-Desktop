class ProviderTokenErrorDescription(str):
    def __new__(cls, value: str, *, http_status: int | None = None, error_code: str | None = None):
        obj = super().__new__(cls, value)
        obj.http_status = http_status
        obj.error_code = error_code
        return obj


class LLMError(ValueError):
    """Base class for all LLM exceptions."""

    description: str | None = None

    def __init__(self, description: str | None = None):
        self.description = description


class LLMBadRequestError(LLMError):
    """Raised when the LLM returns bad request."""

    description = "Bad Request"


class ProviderTokenNotInitError(ValueError):
    """
    Custom exception raised when the provider token is not initialized.
    """

    description = "Provider Token Not Init"

    def __init__(self, *args, **kwargs):
        self.description = args[0] if args else self.description


class TeamModelConfigRequiredError(ProviderTokenNotInitError):
    """
    Raised when a shared model provider exists but the current team has not configured credentials yet.
    """

    description = "Team model credentials are not initialized."

    def __init__(self, description: str | None = None):
        super().__init__(
            ProviderTokenErrorDescription(
                description or self.description,
                http_status=412,
                error_code="team_model_config_required",
            )
        )
        self.http_status = 412
        self.error_code = "team_model_config_required"


class QuotaExceededError(ValueError):
    """
    Custom exception raised when the quota for a provider has been exceeded.
    """

    description = "Quota Exceeded"


class AppInvokeQuotaExceededError(ValueError):
    """
    Custom exception raised when the quota for an app has been exceeded.
    """

    description = "App Invoke Quota Exceeded"


class ModelCurrentlyNotSupportError(ValueError):
    """
    Custom exception raised when the model not support
    """

    description = "Model Currently Not Support"


class InvokeRateLimitError(ValueError):
    """Raised when the Invoke returns rate limit error."""

    description = "Rate Limit Error"
