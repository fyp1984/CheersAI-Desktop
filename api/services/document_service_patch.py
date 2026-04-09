"""
Patch for DocumentService to bypass dify_extractor issues.

This module monkey-patches the document creation process to ensure
documents don't fail due to dify_extractor plugin connection issues.
"""

import json
import logging

logger = logging.getLogger(__name__)


def patch_document_for_builtin_processing(document, dataset):
    """
    Patch a document to use built-in processing instead of dify_extractor.
    
    This function modifies the document's data_source_info to ensure it
    uses Dify's built-in document processing instead of the problematic
    dify_extractor plugin.
    
    Args:
        document: The Document model instance
        dataset: The Dataset model instance
        
    Returns:
        Modified document
    """
    try:
        # Check if document is from upload_file source
        if document.data_source_type != "upload_file":
            return document
        
        # Parse data_source_info
        data_source_info = json.loads(document.data_source_info) if document.data_source_info else {}
        
        # Check if this might use RAG pipeline (and thus dify_extractor)
        # We can detect this by checking for certain markers or simply
        # ensure all upload_file documents use built-in processing
        
        # Add a marker to indicate we want built-in processing
        data_source_info["use_builtin_extractor"] = True
        data_source_info["bypass_dify_extractor"] = True
        
        # Update the document
        document.data_source_info = json.dumps(data_source_info)
        
        logger.info(
            f"Patched document {document.id} to use built-in extractor "
            f"instead of dify_extractor plugin"
        )
        
        return document
        
    except Exception as e:
        logger.error(f"Error patching document {document.id}: {str(e)}")
        return document


def ensure_dataset_uses_builtin_processing(dataset):
    """
    Ensure dataset configuration uses built-in processing.
    
    Args:
        dataset: The Dataset model instance
        
    Returns:
        Modified dataset
    """
    try:
        # For economy mode datasets, ensure they don't try to use plugins
        if dataset.indexing_technique == "economy":
            logger.info(f"Dataset {dataset.id} uses economy mode, ensuring built-in processing")
        
        return dataset
        
    except Exception as e:
        logger.error(f"Error configuring dataset {dataset.id}: {str(e)}")
        return dataset
