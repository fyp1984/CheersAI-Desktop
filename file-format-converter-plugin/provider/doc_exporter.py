"""Document Exporter Provider"""
from typing import Any
from dify_plugin import ToolProvider


class DocExporterProvider(ToolProvider):
    """Document exporter tool provider - no credentials needed"""
    
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        """
        Validate credentials (none required for this provider)
        
        Args:
            credentials: Empty dict as no credentials are needed
        """
        # No credentials needed for document export
        pass
