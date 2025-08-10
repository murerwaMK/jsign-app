import os
import subprocess
from flask import Blueprint, render_template, request, jsonify, current_app, send_from_directory, abort, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .models import Document, User, Signature, db

views = Blueprint('views', __name__)

def convert_to_pdf(source_path, output_dir):
    try:
        subprocess.run(['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', output_dir, source_path], check=True, timeout=30)
        base_name = os.path.splitext(os.path.basename(source_path))[0]
        return os.path.join(output_dir, f"{base_name}.pdf")
    except Exception as e:
        print(f"Error converting file: {e}")
        return None

@views.route('/')
@login_required
def index():
    return render_template('index.html')

@views.route('/api/documents/<int:doc_id>')
@login_required
def get_document_details(doc_id):
    doc = Document.query.get_or_404(doc_id)
    if doc.is_deleted: abort(404)

    all_users = User.query.filter_by(role='user').all()
    signed_users = {s.signer for s in doc.signatures}
    signed_user_ids = {u.id for u in signed_users}

    return jsonify({
        'id': doc.id,
        'filename': doc.filename,
        'filepath': doc.filepath,
        'uploader': doc.uploader.username,
        'special_requirements': doc.special_requirements or "No special requirements provided.",
        'signed_by': [{'id': u.id, 'username': u.username} for u in signed_users],
        'not_signed_by': [{'id': u.id, 'username': u.username} for u in all_users if u.id not in signed_user_ids]
    })


@views.route('/api/documents', methods=['GET'])
@login_required
def get_documents():
    all_docs = Document.query.filter_by(is_deleted=False).order_by(Document.upload_timestamp.desc()).all()
    docs_data = []
    for doc in all_docs:
        has_user_signed = Signature.query.filter_by(user_id=current_user.id, document_id=doc.id).first()
        docs_data.append({
            'id': doc.id,
            'filename': doc.filename,
            'uploader': doc.uploader.username,
            'status': "Acknowledged" if has_user_signed else "Pending Acknowledgment"
        })
    return jsonify({'documents': docs_data})


@views.route('/api/documents', methods=['POST'])
@login_required
def upload_document():
    if 'file' not in request.files: return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    special_requirements = request.form.get('special_requirements', '')
    
    if file.filename == '': return jsonify({'error': 'No selected file'}), 400

    original_filename = secure_filename(file.filename)
    upload_folder = current_app.config['UPLOAD_FOLDER']
    temp_path = os.path.join(upload_folder, original_filename)
    file.save(temp_path)

    final_filepath_rel = original_filename
    file_ext = os.path.splitext(original_filename)[1].lower()
    if file_ext in ['.docx', '.xlsx']:
        pdf_path_abs = convert_to_pdf(temp_path, upload_folder)
        if pdf_path_abs:
            final_filepath_rel = os.path.basename(pdf_path_abs)
            os.remove(temp_path)
        else:
            return jsonify({'error': 'File conversion to PDF failed'}), 500
    elif file_ext != '.pdf':
        os.remove(temp_path)
        return jsonify({'error': 'Unsupported file type'}), 400

    new_doc = Document(
        filename=original_filename, 
        filepath=final_filepath_rel, 
        uploader_id=current_user.id,
        special_requirements=special_requirements
    )
    db.session.add(new_doc)
    db.session.commit()
    return jsonify({'message': 'File processed successfully'}), 201

@views.route('/api/documents/<int:doc_id>/sign', methods=['POST'])
@login_required
def acknowledge_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    if Signature.query.filter_by(user_id=current_user.id, document_id=doc_id).first():
        return jsonify({'error': 'You have already acknowledged this document'}), 409
    
    # The 'Signature' now represents an acknowledgment.
    new_acknowledgment = Signature(user_id=current_user.id, document_id=doc.id)
    db.session.add(new_acknowledgment)
    db.session.commit()
    return jsonify({'message': 'Document acknowledged successfully'}), 200

# The other routes (delete, download, etc.) remain the same as the previous version.
# ... (You can copy them from the last version provided) ...
@views.route('/uploads/<path:filename>')
@login_required
def serve_upload(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@views.route('/api/documents/<int:doc_id>', methods=['DELETE'])
@login_required
def delete_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    if current_user.id != doc.uploader_id and current_user.role != 'admin': abort(403)
    doc.is_deleted = True
    db.session.commit()
    return jsonify({'message': 'Document deleted successfully'}), 200

@views.route('/download/signed/<int:doc_id>')
@login_required
def download_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], doc.filepath, as_attachment=True)