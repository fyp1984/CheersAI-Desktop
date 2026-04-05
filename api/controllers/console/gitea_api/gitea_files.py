"""Gitea file retrieval API endpoints."""
from io import BytesIO

from flask import send_file
from flask_restx import Resource, fields

from controllers.console import console_ns
from controllers.console.wraps import setup_required
from libs.login import login_required
from services.gitea_storage_service import GiteaStorageService

# Define API models
gitea_file_list_model = console_ns.model('GiteaFileList', {
    'files': fields.List(fields.Raw, description='List of files'),
})

gitea_file_metadata_model = console_ns.model('GiteaFileMetadata', {
    'name': fields.String(description='File name'),
    'path': fields.String(description='File path'),
    'size': fields.Integer(description='File size in bytes'),
    'sha': fields.String(description='File SHA hash'),
    'url': fields.String(description='Download URL'),
    'type': fields.String(description='File type'),
})


@console_ns.route('/gitea/files/<path:file_path>')
class GiteaFileApi(Resource):
    """Gitea file retrieval API."""

    @setup_required
    @login_required
    def get(self, file_path):
        """
        Download file from Gitea repository.
        
        Args:
            file_path: Path to the file in Gitea repository
            
        Returns:
            File content
        """
        try:
            gitea_service = GiteaStorageService()
            file_content = gitea_service.get_file(file_path)
            
            # Get file metadata for proper filename
            try:
                metadata = gitea_service.get_file_metadata(file_path)
                filename = metadata.get('name', file_path.split('/')[-1])
            except Exception:
                filename = file_path.split('/')[-1]
            
            # Return file as download
            return send_file(
                BytesIO(file_content),
                as_attachment=True,
                download_name=filename,
                mimetype='application/octet-stream'
            )
        except FileNotFoundError:
            return {'error': 'File not found in Gitea repository'}, 404
        except Exception as e:
            return {'error': f'Failed to retrieve file: {str(e)}'}, 500


@console_ns.route('/gitea/files/<path:file_path>/metadata')
class GiteaFileMetadataApi(Resource):
    """Gitea file metadata API."""

    @setup_required
    @login_required
    @console_ns.marshal_with(gitea_file_metadata_model)
    def get(self, file_path):
        """
        Get file metadata from Gitea repository.
        
        Args:
            file_path: Path to the file in Gitea repository
            
        Returns:
            File metadata
        """
        try:
            gitea_service = GiteaStorageService()
            metadata = gitea_service.get_file_metadata(file_path)
            return metadata
        except FileNotFoundError:
            return {'error': 'File not found in Gitea repository'}, 404
        except Exception as e:
            return {'error': f'Failed to retrieve metadata: {str(e)}'}, 500


@console_ns.route('/gitea/files')
class GiteaFileListApi(Resource):
    """Gitea file list API."""

    @setup_required
    @login_required
    @console_ns.marshal_with(gitea_file_list_model)
    def get(self):
        """
        List files in Gitea repository.
        
        Query parameters:
            path: Directory path (optional, default: root)
            
        Returns:
            List of files
        """
        from flask import request
        
        directory_path = request.args.get('path', '')
        
        try:
            gitea_service = GiteaStorageService()
            files = gitea_service.list_files(directory_path)
            return {'files': files}
        except FileNotFoundError:
            return {'error': 'Directory not found in Gitea repository'}, 404
        except Exception as e:
            return {'error': f'Failed to list files: {str(e)}'}, 500


@console_ns.route('/gitea/files/<path:file_path>/url')
class GiteaFileUrlApi(Resource):
    """Gitea file URL API."""

    @setup_required
    @login_required
    def get(self, file_path):
        """
        Get direct download URL for a file in Gitea repository.
        
        Args:
            file_path: Path to the file in Gitea repository
            
        Returns:
            Download URL
        """
        try:
            gitea_service = GiteaStorageService()
            
            # Check if file exists
            if not gitea_service.file_exists(file_path):
                return {'error': 'File not found in Gitea repository'}, 404
            
            url = gitea_service.get_file_url(file_path)
            return {
                'url': url,
                'path': file_path
            }
        except Exception as e:
            return {'error': f'Failed to get file URL: {str(e)}'}, 500
