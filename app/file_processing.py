from app.consts import ALLOWED_PDF, ALLOWED_EXTENSIONS_DOC, ALLOWED_EXTENSIONS_IMAGE


async def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_IMAGE


async def allowed_file_doc(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_DOC


async def allowed_pdf(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_PDF

