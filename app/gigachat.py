import asyncio
import json
import re
import uuid
from langchain_community.chat_models import GigaChat
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
)
from chromadb.config import Settings
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.gigachat import GigaChatEmbeddings
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
import ast
from app.prompts import contextualize_q_system_prompt, qa_system_prompt, qa_system_prompt_practic
import requests
import os

contextualize_q_system_prompt = contextualize_q_system_prompt
qa_system_prompt = qa_system_prompt
qa_system_prompt_practic = qa_system_prompt_practic
auth = os.environ.get('GIGACHAT_AUTH')


async def send_with_doc(text, question, chat_history, analysis):
    global contextualize_q_system_prompt, qa_system_prompt, qa_system_prompt_practic
    """
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    documents = [Document(page_content=x) for x in text_splitter.split_text(text)]"""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_text(text)
    llm = GigaChat(
        credentials=auth,
        verify_ssl_certs=False)

    embeddings = GigaChatEmbeddings(
        credentials=auth,
        verify_ssl_certs=False
    )

    db = Chroma.from_texts(
        splits,
        embeddings,
        client_settings=Settings(anonymized_telemetry=False),
    )

    # print(llm.tokens_count(mas))
    tok = 0
    for i in llm.tokens_count(splits):
        tok += int(re.search(r"tokens=\d*", str(i)).group(0)[7:])

    # Извлечение данных и генерация с помощью релевантных фрагментов блога.
    retriever = db.as_retriever()

    contextualize_q_system_prompt = contextualize_q_system_prompt
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )

    if not analysis:
        qa_system_prompt = qa_system_prompt
    else:
        qa_system_prompt = qa_system_prompt_practic
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    all_message = 0
    all_message += tok
    mas = [f'("system", {qa_system_prompt}),MessagesPlaceholder("chat_history"),("human", "{input}")']
    all_message += llm.tokens_count(mas)[0].tokens
    mas = [f'("system", {contextualize_q_system_prompt}),MessagesPlaceholder("chat_history"),("human", "{input}")']
    all_message += llm.tokens_count(mas)[0].tokens
    mas = [str(question)]
    all_message += llm.tokens_count(mas)[0].tokens

    chat_history = ast.literal_eval(chat_history)
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    ai_msg = rag_chain.invoke({"input": question, "chat_history": chat_history})
    chat_history.extend([question, ai_msg["answer"]])
    return ai_msg["answer"], chat_history, tok, all_message


async def get_message_history(auth_token, conversation_history=None):
    # URL API, к которому мы обращаемся
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    # Если история диалога не предоставлена, инициализируем пустым списком
    if conversation_history is None:
        conversation_history = []

    # Подготовка данных запроса в формате JSON
    payload = json.dumps({
        "model": "GigaChat-Pro",
        "messages": conversation_history,
        "temperature": 1,
        "top_p": 0.1,
        "n": 1,
        "stream": False,
        "max_tokens": 512,
        "repetition_penalty": 1,
        "update_interval": 0
    })

    # Заголовки запроса
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {auth_token}'
    }

    # Выполнение POST-запроса и возвращение ответа
    try:
        response = requests.post(url, headers=headers, data=payload, verify=False)
        response_data = response.json()
        token_used = response_data['usage']['total_tokens']

        # Добавляем ответ модели в историю диалога
        conversation_history.append({
            "role": "assistant",
            "content": response_data['choices'][0]['message']['content']
        })

        return response_data['choices'][0]['message']['content'], conversation_history, token_used
    except requests.RequestException as e:
        # Обработка исключения в случае ошибки запроса
        return None, conversation_history, 0


def refresh():
    global giga_token, expires_at
    res = get_token(auth)
    if res != 1:
        giga_token = res.json()['access_token']
        expires_at = res.json()['expires_at']
    return


def get_token(auth_token, scope='GIGACHAT_API_PERS'):
    # Создадим идентификатор UUID (36 знаков)
    rq_uid = str(uuid.uuid4())

    # API URL
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

    # Заголовки
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': rq_uid,
        'Authorization': f'Basic {auth_token}'
    }

    # Тело запроса
    payload = {
        'scope': scope
    }

    try:
        # Делаем POST запрос с отключенной SSL верификацией
        # (можно скачать сертификаты Минцифры, тогда отключать проверку не надо)
        res = requests.post(url, headers=headers, data=payload, verify=False)
        return res
    except requests.RequestException as e:
        print(f"Ошибка: {str(e)}")
        return -1


lock = asyncio.Lock()
response = get_token(auth)
if response != 1:
    giga_token = response.json()['access_token']
    expires_at = response.json()['expires_at']
