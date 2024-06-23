from app import db


class User(db.Models):
    id = db.Column(db.Integer, primary_key=True)
    hid = db.Column(db.String(), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)
    message_tokens = db.Column(db.Integer, nullable=False)
    embedding_tokens = db.Column(db.Integer, nullable=False)
    images = db.Column(db.Integer, nullable=False)
    chats = db.relationship('Chat', backref='user', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'password': self.password,
            'message_tokens': self.message_tokens,
            'embedding_tokens': self.embedding_tokens,
            'images': self.images
        }
