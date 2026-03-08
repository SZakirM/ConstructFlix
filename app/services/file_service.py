import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app, url_for
from datetime import datetime
import hashlib

class FileService:
    
    @staticmethod
    def allowed_file(filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']
    
    @staticmethod
    def get_file_extension(filename):
        """Get file extension"""
        return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    @staticmethod
    def generate_unique_filename(original_filename):
        """Generate unique filename"""
        ext = FileService.get_file_extension(original_filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        return f"{timestamp}_{unique_id}.{ext}"
    
    @staticmethod
    def save_upload(file, subfolder=''):
        """Save uploaded file"""
        if not file or not FileService.allowed_file(file.filename):
            return None
        
        # Generate secure filename
        filename = FileService.generate_unique_filename(file.filename)
        
        # Create subfolder path
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
        os.makedirs(upload_path, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)
        
        # Calculate file hash for integrity
        file_hash = FileService.calculate_file_hash(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        return {
            'filename': filename,
            'original_filename': secure_filename(file.filename),
            'path': file_path,
            'url': url_for('static', filename=f'uploads/{subfolder}/{filename}'),
            'size': file_size,
            'hash': file_hash,
            'extension': FileService.get_file_extension(filename)
        }
    
    @staticmethod
    def calculate_file_hash(filepath):
        """Calculate SHA-256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    @staticmethod
    def delete_file(filepath):
        """Delete file from filesystem"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
        except Exception as e:
            current_app.logger.error(f"Error deleting file {filepath}: {str(e)}")
        return False
    
    @staticmethod
    def get_file_info(filepath):
        """Get file information"""
        try:
            stat = os.stat(filepath)
            return {
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'hash': FileService.calculate_file_hash(filepath)
            }
        except Exception as e:
            current_app.logger.error(f"Error getting file info: {str(e)}")
            return None