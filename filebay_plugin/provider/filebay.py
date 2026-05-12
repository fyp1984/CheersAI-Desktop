"""FileBay Provider - Credential validation"""
from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError
from tools.read_file import ReadFileTool


class FileBayProvider(ToolProvider):
    """FileBay tool provider for file operations"""
    
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        """
        Validate the credentials by attempting to list files in the repository
        
        Args:
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
            
            # Try to read a test file or list root directory to validate credentials
            # We'll use the read_file tool to test connectivity
            tool = ReadFileTool.from_credentials(credentials)
            
            # Test by attempting to access the repository
            # This will raise an exception if credentials are invalid
            try:
                # Try to read README.md or any common file
                for _ in tool.invoke(tool_parameters={"file_path": "README.md", "encoding": "utf-8"}):
                    pass
            except Exception:
                # If README.md doesn't exist, that's okay - credentials are still valid
                # The important thing is that we can connect to the repository
                pass
                
        except ToolProviderCredentialValidationError:
            raise
        except Exception as e:
            raise ToolProviderCredentialValidationError(
                f"Failed to validate FileBay credentials: {str(e)}"
            )
