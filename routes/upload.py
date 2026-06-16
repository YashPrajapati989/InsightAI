import os
from flask import Blueprint, render_template, request, current_app, flash, redirect, url_for, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from services.file_service import save_upload_securely, cleanup_file
from services.dataset_service import load_dataset, DatasetError
from utils.analyzer import DataProfiler
from utils.cleaner import DataCleaner, DataCleaningAgent
from utils.dashboard_recommender import DashboardRecommender
from utils.storytelling import BusinessStoryGenerator
from utils.chat_engine import ChatEngine

upload_bp = Blueprint('upload', __name__)

@upload_bp.route("/upload", methods=["POST"])
def upload():
    """Handle dataset upload, validate it, and render the generated dashboard report with cleaning recommendations."""
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
            
            # Instantiate cleaner to analyze and generate recommendations
            cleaner = DataCleaner(df, report["quality_score"])
            recommendations = cleaner.analyze()
            
            # Extract file_id (the unique UUID-based filename)
            file_id = os.path.basename(filepath)
            
            # Log success
            current_app.logger.info(f"Successfully profiled dataset: {original_name}")
            
            # Render result page with recommendations and file_id
            return render_template(
                "result.html", 
                report=report, 
                file_id=file_id, 
                recommendations=recommendations
            )
            
        except DatasetError as e:
            current_app.logger.warning(f"Dataset error for {original_name}: {str(e)}")
            flash(str(e), "error")
            # Cleanup immediately if loading fails
            cleanup_file(filepath)
            return redirect(url_for('main.home'))
            
    except ValueError as e:
        current_app.logger.warning(f"Validation error during upload: {str(e)}")
        flash(str(e), "error")
        return redirect(url_for('main.home'))
    except Exception as e:
        current_app.logger.error(f"Unexpected error during upload handling: {e}")
        flash("An unexpected error occurred while processing your upload.", "error")
        return redirect(url_for('main.home'))

@upload_bp.route("/clean", methods=["POST"])
def clean():
    """Perform automatic cleaning on the previously uploaded dataset."""
    file_id = request.form.get("file_id")
    original_score = request.form.get("original_score", type=int)
    
    if not file_id:
        flash("Invalid request. Missing file identifier.", "error")
        return redirect(url_for('main.home'))
        
    # Standard security check for path traversal on file_id
    file_id = secure_filename(file_id)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file_id)
    
    if not os.path.exists(filepath):
        flash("The uploaded file has expired or was already processed. Please upload again.", "error")
        return redirect(url_for('main.home'))
        
    try:
        # Load original dataset
        df = load_dataset(filepath)
        
        # Initialize cleaner and run cleaning pipeline
        cleaner = DataCleaner(df, original_score)
        clean_results = cleaner.clean()
        
        # Save cleaned file to cleaned_files/
        cleaned_filename = f"cleaned_{file_id}"
        cleaner.save_cleaned_file(current_app.config['CLEANED_FOLDER'], cleaned_filename)
        
        # Delete original uploaded raw file to protect storage
        cleanup_file(filepath)
        
        current_app.logger.info(f"Successfully cleaned file {file_id}. Saved as {cleaned_filename}")
        
        return render_template(
            "cleaned_result.html",
            results=clean_results,
            cleaned_filename=cleaned_filename
        )
        
    except Exception as e:
        current_app.logger.error(f"Error during data cleaning for file {file_id}: {e}")
        flash("An error occurred while cleaning the dataset.", "error")
        # Ensure cleanup of original upload on error
        cleanup_file(filepath)
        return redirect(url_for('main.home'))

@upload_bp.route("/download/<filename>", methods=["GET"])
def download(filename):
    """Allow downloading of the cleaned file."""
    filename = secure_filename(filename)
    cleaned_dir = current_app.config['CLEANED_FOLDER']
    filepath = os.path.join(cleaned_dir, filename)
    
    if not os.path.exists(filepath):
        flash("The requested file does not exist or has expired.", "error")
        return redirect(url_for('main.home'))
        
    return send_from_directory(cleaned_dir, filename, as_attachment=True)


@upload_bp.route("/download-audit/<filename>", methods=["GET"])
def download_audit(filename):
    """Allow downloading of the audit log text file."""
    filename = secure_filename(filename)
    cleaned_dir = current_app.config['CLEANED_FOLDER']
    filepath = os.path.join(cleaned_dir, filename)
    
    if not os.path.exists(filepath):
        flash("The audit log file does not exist or has expired.", "error")
        return redirect(url_for('main.home'))
        
    return send_from_directory(cleaned_dir, filename, as_attachment=True)

@upload_bp.route("/recommendations/<file_id>", methods=["GET"])
def recommendations(file_id):
    """Analyze the dataset and recommend visualizations and layout for a dashboard."""
    file_id = secure_filename(file_id)
    
    # Check uploads directory (raw dataset)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file_id)
    
    # Check cleaned_files directory (cleaned dataset)
    if not os.path.exists(filepath):
        filepath = os.path.join(current_app.config['CLEANED_FOLDER'], file_id)
        
    if not os.path.exists(filepath):
        flash("The dataset file could not be found or has expired. Please upload again.", "error")
        return redirect(url_for('main.home'))
        
    try:
        # Load dataset
        df = load_dataset(filepath)
        
        # Analyze dataset using DashboardRecommender
        recommender = DashboardRecommender(df)
        rec_data = recommender.recommend()
        
        current_app.logger.info(f"Generated dashboard recommendations for file: {file_id}")
        
        return render_template(
            "recommendations.html",
            recommendations=rec_data,
            file_id=file_id
        )
    except Exception as e:
        current_app.logger.error(f"Error generating dashboard recommendations for {file_id}: {e}")
        flash("An error occurred while analyzing the dataset for recommendations.", "error")
        return redirect(url_for('main.home'))

@upload_bp.route("/storytelling/<file_id>", methods=["GET"])
def storytelling(file_id):
    """Generate and display the Business Storytelling Report."""
    file_id = secure_filename(file_id)
    
    # Check uploads directory (raw dataset)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file_id)
    
    # Check cleaned_files directory (cleaned dataset)
    if not os.path.exists(filepath):
        filepath = os.path.join(current_app.config['CLEANED_FOLDER'], file_id)
        
    if not os.path.exists(filepath):
        flash("The dataset file could not be found or has expired. Please upload again.", "error")
        return redirect(url_for('main.home'))
        
    try:
        # Load dataset
        df = load_dataset(filepath)
        
        # Generate context for storytelling
        report = DataProfiler(df).profile()
        rec_data = DashboardRecommender(df).recommend()
        
        # Retrieve original score from session/args if possible, but for simplicity we rely on current score
        # as it is the current state of the dataset
        original_score = request.args.get("original_score", type=int, default=None)
        
        # Initialize storytelling generator
        generator = BusinessStoryGenerator(df, report, rec_data, original_score=original_score)
        story_report = generator.generate_report()
        
        current_app.logger.info(f"Generated business storytelling report for file: {file_id}")
        
        return render_template(
            "storytelling.html",
            story_report=story_report,
            file_id=file_id
        )
    except Exception as e:
        current_app.logger.error(f"Error generating business storytelling for {file_id}: {e}")
        flash("An error occurred while generating the business story.", "error")
        return redirect(url_for('main.home'))

@upload_bp.route("/chat/<file_id>", methods=["GET"])
def chat_ui(file_id):
    """Render the AI Data Assistant chat interface."""
    file_id = secure_filename(file_id)
    
    # Check uploads directory (raw dataset)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file_id)
    
    # Check cleaned_files directory (cleaned dataset)
    if not os.path.exists(filepath):
        filepath = os.path.join(current_app.config['CLEANED_FOLDER'], file_id)
        
    if not os.path.exists(filepath):
        flash("The dataset file could not be found or has expired. Please upload again.", "error")
        return redirect(url_for('main.home'))
        
    # We only render the UI here. The JS will call the API.
    return render_template("chat.html", file_id=file_id)

@upload_bp.route("/api/chat", methods=["POST"])
def api_chat():
    """Handle chat requests via JSON AJAX."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload provided"}), 400
        
    file_id = data.get("file_id")
    question = data.get("question")
    history = data.get("history", [])
    
    if not file_id or not question:
        return jsonify({"error": "Missing file_id or question"}), 400
        
    file_id = secure_filename(file_id)
    
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file_id)
    if not os.path.exists(filepath):
        filepath = os.path.join(current_app.config['CLEANED_FOLDER'], file_id)
        
    if not os.path.exists(filepath):
        return jsonify({"error": "Dataset expired or not found"}), 404
        
    try:
        df = load_dataset(filepath)
        engine = ChatEngine(df)
        
        # Determine if we should enforce security limits
        if len(question) > 500:
            return jsonify({"error": "Question too long"}), 400
            
        result = engine.generate_answer(question, context=history)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Chat API error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@upload_bp.route("/clean-agent/<file_id>", methods=["GET"])
def clean_agent(file_id):
    """Run the Interactive AI Data Cleaning Agent analysis and render the config dashboard."""
    file_id = secure_filename(file_id)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file_id)
    
    if not os.path.exists(filepath):
        filepath = os.path.join(current_app.config['CLEANED_FOLDER'], file_id)
        
    if not os.path.exists(filepath):
        flash("The uploaded dataset has expired or was not found. Please upload again.", "error")
        return redirect(url_for('main.home'))
        
    try:
        df = load_dataset(filepath)
        profiler = DataProfiler(df)
        report = profiler.profile()
        
        # Instantiate and run detailed cleaning analysis
        agent = DataCleaningAgent(df, report["quality_score"])
        analysis_report = agent.analyze()
        
        return render_template(
            "clean_agent.html",
            file_id=file_id,
            analysis=analysis_report,
            report=report
        )
    except Exception as e:
        current_app.logger.error(f"Error initializing DataCleaningAgent for {file_id}: {e}")
        flash("An error occurred while analyzing the dataset.", "error")
        return redirect(url_for('main.home'))


@upload_bp.route("/clean-agent/apply", methods=["POST"])
def clean_agent_apply():
    """Apply the custom cleaning actions approved by the user."""
    file_id = request.form.get("file_id")
    if not file_id:
        flash("Invalid request. Missing file identifier.", "error")
        return redirect(url_for('main.home'))
        
    file_id = secure_filename(file_id)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file_id)
    if not os.path.exists(filepath):
        filepath = os.path.join(current_app.config['CLEANED_FOLDER'], file_id)
        
    if not os.path.exists(filepath):
        flash("The dataset file could not be found or has expired.", "error")
        return redirect(url_for('main.home'))
        
    try:
        # Load the original data
        df = load_dataset(filepath)
        
        # Profile original dataset to get its base score
        profiler_orig = DataProfiler(df)
        report_orig = profiler_orig.profile()
        original_score = report_orig["quality_score"]
        
        # Gather form inputs for approved cleaning
        remove_duplicates = request.form.get("remove_duplicates") == "on"
        remove_empty_rows = request.form.get("remove_empty_rows") == "on"
        
        missing_actions = {}
        outlier_actions = {}
        for key in request.form.keys():
            if key.startswith("missing_action_"):
                col_name = key[len("missing_action_"):]
                # Only apply if user checked the approve checkbox for this column
                approved = request.form.get(f"approve_missing_{col_name}") == "on"
                if approved:
                    missing_actions[col_name] = request.form.get(key)
                else:
                    missing_actions[col_name] = "skip"   # signals audit-log-only
            elif key.startswith("outlier_action_"):
                col_name = key[len("outlier_action_"):]
                approved = request.form.get(f"approve_outlier_{col_name}") == "on"
                if approved:
                    outlier_actions[col_name] = request.form.get(key)
                else:
                    outlier_actions[col_name] = "skip"


        config = {
            "remove_duplicates": remove_duplicates,
            "remove_empty_rows": remove_empty_rows,
            "missing_actions": missing_actions,
            "outlier_actions": outlier_actions
        }
        
        # Execute the approved cleanings
        agent = DataCleaningAgent(df, original_score)
        df_cleaned, audit_log = agent.apply_custom_cleaning(config)
        
        # Save cleaned file to cleaned_files/
        cleaned_filename = f"cleaned_{file_id}"
        cleaned_dir = current_app.config['CLEANED_FOLDER']
        os.makedirs(cleaned_dir, exist_ok=True)
        
        # Write cleaned file
        cleaned_path = os.path.join(cleaned_dir, cleaned_filename)
        if cleaned_path.lower().endswith('.xlsx'):
            df_cleaned.to_excel(cleaned_path, index=False, engine='openpyxl')
        else:
            df_cleaned.to_csv(cleaned_path, index=False)
            
        # Write the Audit Log text file next to the cleaned dataset
        audit_log_filename = f"audit_log_{file_id}.txt"
        audit_log_path = os.path.join(cleaned_dir, audit_log_filename)
        with open(audit_log_path, 'w', encoding='utf-8') as f:
            f.write("=== InsightAI Data Cleaning Audit Log ===\n")
            f.write(f"File ID: {file_id}\n")
            f.write(f"Initial Quality Score: {original_score}/100\n")
            f.write(f"Applied Changes:\n\n")
            for entry in audit_log:
                f.write(f"- {entry}\n")
        
        # Profile the cleaned dataset to get post-clean metrics
        profiler_clean = DataProfiler(df_cleaned)
        report_clean = profiler_clean.profile()
        
        # Cleanup original upload raw file
        cleanup_file(filepath)
        
        current_app.logger.info(f"Agent applied custom cleaning for {file_id}. Audit trail saved.")
        
        return render_template(
            "clean_agent_result.html",
            original_score=original_score,
            cleaned_score=report_clean["quality_score"],
            audit_log=audit_log,
            cleaned_filename=cleaned_filename,
            audit_log_filename=audit_log_filename,
            rows_before=len(df),
            rows_after=len(df_cleaned)
        )
        
    except Exception as e:
        current_app.logger.error(f"Error applying custom cleanings for {file_id}: {e}")
        flash("An error occurred while cleaning the dataset.", "error")
        return redirect(url_for('main.home'))
