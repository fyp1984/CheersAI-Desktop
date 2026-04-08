"""
Extractor bypass for dify_extractor plugin issues.

This module provides a fallback mechanism when dify_extractor plugin fails,
automatically using built-in extractors instead.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ExtractorBypass:
    """
    Bypass mechanism for problematic dify_extractor plugin.
    
    When dify_extractor fails with connection errors, this class provides
    alternative extraction methods using built-in Dify extractors.
    """
    
    @staticmethod
    def should_bypass(error_message: str) -> bool:
        """
        Check if an error should trigger bypass.
        
        Args:
            error_message: The error message from dify_extractor
            
        Returns:
            True if bypass should be triggered
        """
        bypass_indicators = [
            "Connection refused",
            "ConnectError",
            "dify_extractor",
            "[Errno 111]",
        ]
        
        return any(indicator in error_message for indicator in bypass_indicators)
    
    @staticmethod
    def extract_with_builtin(file_path: str, file_extension: str) -> Optional[str]:
        """
        Extract text from file using built-in extractors.
        
        Args:
            file_path: Path to the file
            file_extension: File extension (e.g., '.md', '.txt', '.pdf')
            
        Returns:
            Extracted text content or None if extraction fails
        """
        try:
            # For text-based files, use simple file reading
            if file_extension.lower() in ['.txt', '.md', '.markdown', '.csv', '.json', '.xml', '.html']:
                logger.info(f"Using built-in text extractor for {file_extension}")
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            
            # For other files, try to use Unstructured directly
            # This bypasses the plugin and uses the library directly
            try:
                from unstructured.partition.auto import partition
                
                logger.info(f"Using Unstructured library directly for {file_extension}")
                elements = partition(filename=file_path)
                text = "\n\n".join([str(el) for el in elements])
                return text
            except ImportError:
                logger.warning("Unstructured library not available, using basic extraction")
                # Fallback to basic text extraction
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
                    
        except Exception as e:
            logger.error(f"Built-in extraction failed: {str(e)}")
            return None
    
    @staticmethod
    def log_bypass(document_id: str, original_error: str):
        """
        Log bypass action for monitoring.
        
        Args:
            document_id: ID of the document being processed
            original_error: The original error that triggered bypass
        """
        logger.warning(
            f"BYPASS ACTIVATED for document {document_id}. "
            f"Original error: {original_error}. "
            f"Using built-in extractor instead of dify_extractor plugin."
        )
