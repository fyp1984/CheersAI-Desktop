"""FileBay Tool Provider"""

from typing import Any

from core.tools.builtin_tool.provider import BuiltinToolProviderController
from core.tools.errors import ToolProviderCredentialValidationError


class FileBayProvider(BuiltinToolProviderController):
    """FileBay tool provider for file operations"""

    def _validate_credentials(self, user_id: str, credentials: dict[str, Any]) -> None:
        """
        Validate FileBay credentials
        
        Args:
            user_id: The user ID
            credentials: The credentials dictionary containing:
                - filebay_url: The base URL of FileBay
                - filebay_token: The access token
                - filebay_owner: The repository owner
                - filebay_repo: The repository name
                - filebay_branch: The branch name (optional)
        
        Raises:
            ToolProviderCredentialValidationError: If credentials are invalid
        """
        try:
            # Validate required fields
            required_fields = ['filebay_url', 'filebay_token', 'filebay_owner', 'filebay_repo']
            
            for field in required_fields:
                if not credentials.get(field):
                    raise ToolProviderCredentialValidationError(f"Missing required field: {field}")
            
            # Basic URL validation
            filebay_url = credentials.get('filebay_url', '').strip()
            if not filebay_url.startswith(('http://', 'https://')):
                raise ToolProviderCredentialValidationError("FileBay URL must start with http:// or https://")
            
            # Validate token is not empty
            filebay_token = credentials.get('filebay_token', '').strip()
            if len(filebay_token) < 10:
                raise ToolProviderCredentialValidationError("FileBay token appears to be invalid")
            
            # Set default branch if not provided
            if not credentials.get('filebay_branch'):
                credentials['filebay_branch'] = 'main'
                
        except ToolProviderCredentialValidationError:
            raise
        except Exception as e:
            raise ToolProviderCredentialValidationError(
                f"Failed to validate FileBay credentials: {str(e)}"
            )
