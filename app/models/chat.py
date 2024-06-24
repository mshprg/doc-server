from datetime import datetime
from app import db


class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hid = db.Column(db.String(), unique=True, nullable=False)
    name = db.Column(db.String(), nullable=False)
    messages = db.relationship('Message', backref='chat', lazy=True)
    files = db.relationship('FileData', backref='chat', lazy=True)
    type = db.Column(db.String(), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id,
            'hid': self.hid,
            'type': self.type
        }
