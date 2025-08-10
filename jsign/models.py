from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150))
    role = db.Column(db.String(50), nullable=False, default='user')
    # REMOVED: signature_image field is no longer needed.
    
    documents_uploaded = db.relationship('Document', backref='uploader', lazy=True)
    signatures = db.relationship('Signature', backref='signer', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    upload_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)
    # NEW: Field for special requirements text.
    special_requirements = db.Column(db.Text, nullable=True)

    signatures = db.relationship('Signature', backref='document', lazy='dynamic', cascade="all, delete-orphan")

class Signature(db.Model):
    # This model now represents an "Acknowledgment" event.
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    # REMOVED: signature_data field is no longer needed.