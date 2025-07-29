import os
from flask import Flask, request, redirect, url_for, render_template, send_from_directory
# REMOVED: from werkzeug.utils import secure_filename - we're bypassing it
import uuid # For generating unique IDs if needed, but not used directly for filename in this risky version

# Initialize the Flask application
app = Flask(__name__)

# --- Configuration for Uploads ---
UPLOAD_FOLDER = 'uploads'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 999999999999 # Allows uploads up to ~999 GB

# Ensure the upload directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- Helper Function for Allowed File Types (Still just returns True) ---
def allowed_file(filename):
    return True # Allow any filename

# --- Main Route: Display the HTML Page (index.html) ---
@app.route('/')
def index():
    files = []
    # Using os.scandir for potentially better performance with many files
    with os.scandir(app.config['UPLOAD_FOLDER']) as entries:
        for entry in entries:
            if entry.is_file():
                files.append(entry.name)
    return render_template('index.html', files=files)

# --- Upload Route: Handles file uploads ---
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'fileToUpload' not in request.files:
        return redirect(request.url)
    file = request.files['fileToUpload']
    if file.filename == '':
        return redirect(request.url)

    if file and allowed_file(file.filename):
        # !!! DANGER DANGER DANGER !!!
        # Bypassing secure_filename means we are directly using the filename provided by the user.
        # This can lead to security vulnerabilities (e.g., path traversal).
        # ONLY USE THIS FOR LOCAL TESTING WITH TRUSTED INPUT.
        filename = file.filename # Using the original, potentially unsafe filename directly
        
        # Ensure the filename is compatible with the file system encoding
        # This helps with non-ASCII characters, but doesn't prevent path traversal
        try:
            filename.encode('utf-8')
        except UnicodeEncodeError:
            return 'Filename contains characters that cannot be processed!'

        full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Basic check to prevent overwriting existing files if filename is identical (optional, but good practice)
        # You might want to append a number or UUID if collisions are likely
        # if os.path.exists(full_path):
        #     # Simple example of handling collision - not robust
        #     base, ext = os.path.splitext(filename)
        #     filename = f"{base}_{uuid.uuid4().hex[:8]}{ext}"
        #     full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        file.save(full_path)
        return redirect(url_for('view_file', filename=filename))
    else:
        return 'Something went wrong with the file upload!'

# --- View File Route: Displays a dedicated page for a single file ---
@app.route('/view/<filename>')
def view_file(filename):
    return render_template('view_file.html', filename=filename)

# --- Download Route: Serves files for download ---
@app.route('/downloads/<filename>')
def download_file(filename):
    # send_from_directory should handle various filenames, but if the original save failed
    # due to file system incompatibility, this will fail too.
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- Run the Flask app ---
if __name__ == '__main__':
    app.run(debug=True)