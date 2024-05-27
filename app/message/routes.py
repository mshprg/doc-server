import time

from flask import Blueprint, request, flash, redirect
from app.models import chat as chat_model
from app.models import message as message_model
from app.models import file_data
from sqlalchemy import asc
from app.gigachat import send_with_doc, get_message_history
from app import db
from app.gigachat import refresh, expires_at, lock, giga_token

message = Blueprint('message', __name__)


@message.route('/ask-gpt', methods=['POST'])
async def ask_gpt():

    if round(time.time() * 1000) >= expires_at:
        async with lock:
            refresh()

    data = request.get_json()

    text = data['text']
    hid = data['hid']

    chat = db.session.query(chat_model.Chat).filter(chat_model.Chat.hid == hid).first()

    messages = db.session.query(message_model.Message).filter(message_model.Message.chat_id == chat.id).order_by(
        asc(message_model.Message.created_at)).all()

    new_message_question = message_model.Message(text=text, chat=chat, role='user')

    history = []

    for message_obj in messages:
        history.append(
            {'role': str(message_obj.role), 'content': str(message_obj.text)}
        )

    if chat.type == 'default':
        history.append({'role': 'user', 'content': text})
        answer_ai, _ = await get_message_history(giga_token, history)
    else:
        file = db.session.query(file_data.FileData).filter(file_data.FileData.chat_id == chat.id).first()
        file_text = file.data

        answer_ai, _ = await send_with_doc(file_text, text, str(history), True if chat.type == 'analysis' else False)

    new_message_answer = message_model.Message(text=answer_ai, chat=chat, role='assistant')

    db.session.add(new_message_question)
    db.session.add(new_message_answer)
    db.session.commit()

    return {'question': new_message_question.to_dict(), 'answer': new_message_answer.to_dict()}


@message.route('/all/<int:chat_id>', methods=['GET'])
async def get_all_messages_by_chat_id(chat_id: int):

    messages = db.session.query(message_model.Message).filter(message_model.Message.chat_id == chat_id).order_by(
        asc(message_model.Message.created_at)).all()

    response = []

    for m in messages:
        response.append(m.to_dict())

    return response
