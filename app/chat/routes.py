from flask import Blueprint, request, flash, redirect
from app import db
from app.models import chat as model_chat
from app.models import file_data as model_file_data
from app.models import message
from app.file_processing import allowed_image, allowed_file_doc, allowed_pdf
from app.vk_cloud import access_token, send_image, get_text, pdf_to_img
from app.gigachat import send_with_doc
from flask import Response
from sqlalchemy import and_, or_
import uuid

chat = Blueprint('chat', __name__)


@chat.route('/create/document', methods=['POST'])
async def create_document():
    if 'file' in request.files:
        file = request.files['file']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and (await allowed_image(file.filename) or await allowed_file_doc(file.filename) or await allowed_pdf(
                file.filename)):
            file_to_txt = ""

            if await allowed_image(file.filename):
                file_to_txt = await send_image(file)
            elif await allowed_file_doc(file.filename):
                file_to_txt = await get_text(file)
            elif await allowed_pdf(file.filename):
                file_to_txt = await pdf_to_img(file, access_token)

            is_practice = int(request.form['isPractice'])

            question = "Проанализируй и запомни этот документ"
            answer_ai, chat_history = \
                await send_with_doc(file_to_txt, question, '[]', True if is_practice == 1 else False)

            new_chat = model_chat.Chat(name=file.filename, client_id=request.form['client_id'], hid=str(uuid.uuid4()),
                                       type='analysis' if is_practice == 1 else 'document')
            db.session.add(new_chat)
            new_file_data = model_file_data.FileData(data=file_to_txt, chat=new_chat)
            db.session.add(new_file_data)

            message_answer = message.Message(text=answer_ai, chat=new_chat, role='assistant')
            db.session.add(message_answer)
            db.session.commit()

            chats = db.session.query(model_chat.Chat).filter(
                and_(
                    model_chat.Chat.client_id == int(request.form['client_id']),
                    or_(
                        model_chat.Chat.type == 'document',
                        model_chat.Chat.type == 'analysis'
                    )
                )
            ).all()

            response = []
            for chat_obj in chats:
                last_message = db.session.query(message.Message).filter(
                    message.Message.chat_id == chat_obj.id).order_by(
                    message.Message.id.desc()).first()
                response.append(
                    {'chat': chat_obj.to_dict(), 'last_message': last_message.to_dict()}
                )

            return response

    return Response({'message': 'Bad request'}, status=400, mimetype='application/json')


@chat.route('/create/default', methods=['POST'])
async def create_chat():
    data = request.get_json()

    client_id = int(data['client_id'])

    new_chat = model_chat.Chat(name="Чат с GigaChat", client_id=client_id, hid=str(uuid.uuid4()),
                               type='default')

    db.session.add(new_chat)
    db.session.commit()

    chats = db.session.query(model_chat.Chat).filter(
        and_(
            model_chat.Chat.client_id == client_id,
            model_chat.Chat.type == 'default'
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

    return {'response': response, 'chat': new_chat.to_dict()}


@chat.route('/documents/<int:client_id>', methods=['GET'])
async def get_documents_chats(client_id: int):
    chats = db.session.query(model_chat.Chat).filter(
        and_(
            model_chat.Chat.client_id == client_id,
            or_(
                model_chat.Chat.type == 'document',
                model_chat.Chat.type == 'analysis'
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


@chat.route('/chats/<int:client_id>', methods=['GET'])
async def get_chats(client_id: int):
    chats = db.session.query(model_chat.Chat).filter(
        and_(
            model_chat.Chat.client_id == client_id,
            model_chat.Chat.type == 'default'
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


@chat.route('/get/<hid>', methods=['GET'])
async def get_chat_by_id(hid: str):
    res = db.session.query(model_chat.Chat).filter(model_chat.Chat.hid == hid).first()

    return res.to_dict()
