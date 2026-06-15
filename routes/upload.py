from flask import Blueprint, render_template, request, current_app, flash, redirect, url_for
from services.file_service import save_upload_securely, cleanup_file
from services.dataset_service import load_dataset, DatasetError
from utils.analyzer import DataProfiler

upload_bp = Blueprint('upload', __name__)

@upload_bp.route("/upload", methods=["POST"])
def upload():
    """Handle dataset upload, validate it, and render the generated dashboard report."""
    if "file" not in request.files:
        flash("No file part in the request.", "error")
        return redirect(url_for('main.home'))

    file = request.files["file"]
    
    try:
        # Securely save the file
        filepath, original_name = save_upload_securely(file)
        current_app.logger.info(f"Successfully uploaded: {original_name}")
        
        try:
            # Safely load the dataset
            df = load_dataset(filepath)
            
            # Profile dataset using the DataProfiler utility
            report = DataProfiler(df).profile()
            
            # Log success
            current_app.logger.info(f"Successfully profiled dataset: {original_name}")
            
            # Render result page
            return render_template("result.html", report=report)
            
        except DatasetError as e:
            current_app.logger.warning(f"Dataset error for {original_name}: {str(e)}")
            flash(str(e), "error")
            return redirect(url_for('main.home'))
            
        finally:
            # Always clean up the uploaded file to prevent storage exhaustion
            cleanup_file(filepath)
            
    except ValueError as e:
        current_app.logger.warning(f"Validation error during upload: {str(e)}")
        flash(str(e), "error")
        return redirect(url_for('main.home'))
    except Exception as e:
        current_app.logger.error(f"Unexpected error during upload handling: {e}")
        flash("An unexpected error occurred while processing your upload.", "error")
        return redirect(url_for('main.home'))
