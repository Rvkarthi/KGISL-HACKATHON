# custom
from ats_engine.parser.mparser import parse_resume
from ninja import File, Router
from ninja.errors import HttpError
from ninja.files import UploadedFile

from ats.schemas import ParserSchema

router = Router()


@router.post("/parser", response={200: ParserSchema, 400: dict})
def parser_pdf(request, pdf_file: UploadedFile = File(...)) -> dict:

    try:
        result = parse_resume(pdf_file.read())
        return result
    except Exception as error:
        raise HttpError(status_code=500, message=str(error))
