import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

def allowed_file(filename):
    """Check if a file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_upload_securely(file):
    """
    Securely save an uploaded file.
    Validates extension, creates a safe UUID-based filename.
    """
    if file.filename == '':
        raise ValueError("No file selected")
        
    if not allowed_file(file.filename):
        raise ValueError("Unsupported file format. Please upload CSV or Excel.")

    # Secure the original filename just in case we want to use parts of it,
    # but we will rely on UUID for the actual stored filename to prevent path traversal
    # and character issues.
    original_secure_name = secure_filename(file.filename)
    ext = original_secure_name.rsplit('.', 1)[1].lower() if '.' in original_secure_name else ''
    
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    
    # Ensure upload folder exists
    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(filepath)
    
    return filepath, original_secure_name

def cleanup_file(filepath):
    """Safely delete a file after processing to prevent storage exhaustion."""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            current_app.logger.info(f"Cleaned up file: {filepath}")
    except Exception as e:
        current_app.logger.error(f"Failed to cleanup file {filepath}: {e}")
