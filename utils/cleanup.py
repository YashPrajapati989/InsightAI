import os
import time
import threading
import logging

def cleanup_old_files(app_config, logger):
    """
    Background job to delete files older than 1 hour in upload and cleaned folders.
    This prevents the server disk from filling up.
    """
    # Run every 30 minutes
    INTERVAL = 30 * 60
    
    # Delete files older than 1 hour
    MAX_AGE = 60 * 60
    
    folders_to_clean = [
        app_config.get("UPLOAD_FOLDER"),
        app_config.get("CLEANED_FOLDER")
    ]
    
    while True:
        try:
            current_time = time.time()
            deleted_count = 0
            
            for folder in folders_to_clean:
                if not folder or not os.path.exists(folder):
                    continue
                    
                for filename in os.listdir(folder):
                    filepath = os.path.join(folder, filename)
                    
                    # Skip directories
                    if os.path.isdir(filepath):
                        continue
                        
                    # Check age
                    file_age = current_time - os.path.getmtime(filepath)
                    if file_age > MAX_AGE:
                        os.remove(filepath)
                        deleted_count += 1
                        
            if deleted_count > 0:
                logger.info(f"Cleanup Job: Deleted {deleted_count} expired files.")
                
        except Exception as e:
            logger.error(f"Cleanup Job Error: {e}")
            
        time.sleep(INTERVAL)

def start_cleanup_thread(app):
    """Starts the background cleanup thread."""
    app_config = {
        "UPLOAD_FOLDER": app.config.get("UPLOAD_FOLDER"),
        "CLEANED_FOLDER": app.config.get("CLEANED_FOLDER")
    }
    
    thread = threading.Thread(
        target=cleanup_old_files, 
        args=(app_config, app.logger),
        daemon=True # Daemon threads exit when the main program exits
    )
    thread.start()
    app.logger.info("Started background file cleanup thread.")
