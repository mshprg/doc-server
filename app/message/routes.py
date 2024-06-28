import time
from flask import Blueprint, request
from app.models.chat import Chat
from app.models.user import User
from app.models.message import Message
from app.models import file_data
from sqlalchemy import asc
from app.gigachat import send_with_doc, get_message_history
from app import db
from app.gigachat import refresh, expires_at, lock, giga_token

message_print = Blueprint('message', __name__)


@message_print.route('/ask-gpt', methods=['POST'])
async def ask_gpt():

    if round(time.time() * 1000) >= expires_at:
        async with lock:
            refresh()

    data = request.get_json()

    text = data['text']
    hid = data['hid']

    chat = db.session.query(Chat).filter(Chat.hid == hid).first()

    user = db.session.query(User).filter(User.id == chat.user_id).first()

    messages = db.session.query(Message).filter(Message.chat_id == chat.id).order_by(
        asc(Message.created_at)).all()

    new_message_question = Message(text=text, chat=chat, role='user')

    history = []

    for message_obj in messages:
        history.append(
            {'role': str(message_obj.role), 'content': str(message_obj.text)}
        )

    if chat.type == 'default':
        history.append({'role': 'user', 'content': text})
        answer_ai, _, token_used = await get_message_history(giga_token, history)
        user.message_tokens += token_used
    else:
        file = db.session.query(file_data.FileData).filter(file_data.FileData.chat_id == chat.id).first()
        file_text = file.data

        answer_ai, _, em_tokens, ms_tokens = \
            await send_with_doc(file_text, text, str(history), True if chat.type == 'analysis' else False)
        user.message_tokens += ms_tokens
        user.embedding_tokens += em_tokens

    new_message_answer = Message(text=answer_ai, chat=chat, role='assistant')

    db.session.add(new_message_question)
    db.session.add(new_message_answer)
    db.session.commit()

    return {'question': new_message_question.to_dict(), 'answer': new_message_answer.to_dict()}


@message_print.route('/all/<int:chat_id>', methods=['GET'])
async def get_all_messages_by_chat_id(chat_id: int):

    messages = db.session.query(Message).filter(Message.chat_id == chat_id).order_by(
        asc(Message.created_at)).all()

    response = []

    for m in messages:
        response.append(m.to_dict())

    return response
