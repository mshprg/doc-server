from app import db


class FileData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(), nullable=False)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)
