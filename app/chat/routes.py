from flask import Blueprint, request, flash, redirect
from app import db
from app.models.chat import Chat
from app.models.file_data import FileData
from app.models import message
from app.models.user import User
from app.file_processing import allowed_image, allowed_file_doc, allowed_pdf
from app.vk_cloud import send_image, get_text, pdf_to_img
from app.gigachat import send_with_doc
from flask import Response
from sqlalchemy import and_, or_
import uuid

chat_print = Blueprint('chat', __name__)


@chat_print.route('/create/document', methods=['POST'])
async def create_document():
    if 'file' in request.files:
        file = request.files['file']
        user_hid = request.form['user_hid']

        user = db.session.query(User).filter(User.hid == user_hid).first()

        vk_tokens = 0

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and (await allowed_image(file.filename) or await allowed_file_doc(file.filename) or await allowed_pdf(
                file.filename)):
            file_to_txt = ""

            if await allowed_image(file.filename):
                file_to_txt = await send_image(file)
                vk_tokens = 1
            elif await allowed_file_doc(file.filename):
                file_to_txt, tk = await get_text(file)
                vk_tokens = tk
            elif await allowed_pdf(file.filename):
                file_to_txt, tk = await pdf_to_img(file)
                vk_tokens = tk

            is_practice = int(request.form['isPractice'])

            question = "Проанализируй и запомни этот текст"
            answer_ai, chat_history, em_tokens, ms_tokens = \
                await send_with_doc(file_to_txt, question, '[]', True if is_practice == 1 else False)

            new_chat = Chat(name=file.filename, user=user, hid=str(uuid.uuid4()),
                                       type='analysis' if is_practice == 1 else 'document')
            db.session.add(new_chat)
            new_file_data = FileData(data=file_to_txt, chat=new_chat)
            db.session.add(new_file_data)

            message_answer = message.Message(text=answer_ai, chat=new_chat, role='assistant')
            db.session.add(message_answer)

            mt = user.message_tokens + ms_tokens
            et = user.embedding_tokens + em_tokens

            user.message_tokens = mt
            user.embedding_tokens = et
            user.images = vk_tokens

            db.session.commit()

            chats = db.session.query(Chat).filter(
                and_(
                    Chat.user_id == user.id,
                    or_(
                        Chat.type == 'document',
                        Chat.type == 'analysis'
                    )
                )
            ).all()

            response = []
            for chat_obj in chats:
                try:
                    last_message = db.session.query(message.Message).filter(
                        message.Message.chat_id == chat_obj.id).order_by(
                        message.Message.id.desc()).first()
                    d = last_message.to_dict()
                except Exception as e:
                    d = {}
                response.append(
                    {'chat': chat_obj.to_dict(), 'last_message': d}
                )

            return {'all_chats': response, 'new_chat': new_chat.to_dict()}

    return Response({'message': 'Bad request'}, status=400, mimetype='application/json')


@chat_print.route('/create/document-test', methods=['POST'])
async def create_document_test():
    if 'file' in request.files:
        file = request.files['file']

        vk_tokens = 0

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and (await allowed_image(file.filename) or await allowed_file_doc(file.filename) or await allowed_pdf(
                file.filename)):
            file_to_txt = ""

            if await allowed_image(file.filename):
                file_to_txt = await send_image(file)
                vk_tokens = 1
            elif await allowed_file_doc(file.filename):
                file_to_txt, tk = await get_text(file)
                vk_tokens = tk
            elif await allowed_pdf(file.filename):
                file_to_txt, tk = await pdf_to_img(file)
                vk_tokens = tk

            question = "Проанализируй и запомни этот текст"
            answer_ai, chat_history, em_tokens, ms_tokens = \
                await send_with_doc(file_to_txt, question, '[]', False)
            

            return {'text': answer_ai, 'history': chat_history}

    return Response({'message': 'Bad request'}, status=400, mimetype='application/json')


@chat_print.route('/create/default', methods=['POST'])
async def create_chat():
    data = request.get_json()

    user_hid = data['user_hid']
    chat_name = data['name']
    user = db.session.query(User).filter(User.hid == user_hid).first()

    new_chat = Chat(name=chat_name, user=user, hid=str(uuid.uuid4()),
                               type='default')

    db.session.add(new_chat)
    db.session.commit()

    chats = db.session.query(Chat).filter(
        and_(
            Chat.user_id == user.id,
            Chat.type == 'default'
        )
    ).all()

    response = []
    for chat_obj in chats:
        try:
            last_message = db.session.query(message.Message).filter(
                message.Message.chat_id == chat_obj.id).order_by(
                message.Message.id.desc()).first()
            d = last_message.to_dict()
        except Exception as e:
            d = {}
        response.append(
            {'chat': chat_obj.to_dict(), 'last_message': d}
        )

    return {'all_chats': response, 'new_chat': new_chat.to_dict()}


@chat_print.route('/documents/<int:user_id>', methods=['GET'])
async def get_documents_chats(user_id: int):
    chats = db.session.query(Chat).filter(
        and_(
            Chat.user_id == user_id,
            or_(
                Chat.type == 'document',
                Chat.type == 'analysis'
            )
        )
    ).all()

    response = []
    for chat_obj in chats:
        last_message = db.session.query(message.Message) \
            .filter(message.Message.chat_id == chat_obj.id).order_by(
            message.Message.id.desc()).first()
        response.append(
            {'chat': chat_obj.to_dict(), 'last_message': last_message.to_dict()}
        )

    return response


@chat_print.route('/defaults/<int:user_id>', methods=['GET'])
async def get_chats(user_id: int):
    chats = db.session.query(Chat).filter(
        and_(
            Chat.user_id == user_id,
            Chat.type == 'default'
        )
    ).all()

    response = []
    for chat_obj in chats:
        try:
            last_message = db.session.query(message.Message).filter(
                message.Message.chat_id == chat_obj.id).order_by(
                message.Message.id.desc()).first()
            d = last_message.to_dict()
        except Exception as e:
            d = {}
        response.append(
            {'chat': chat_obj.to_dict(), 'last_message': d}
        )

    return response


@chat_print.route('/get/<hid>', methods=['GET'])
async def get_chat_by_id(hid: str):
    res = db.session.query(Chat).filter(Chat.hid == hid).first()

    return res.to_dict()
