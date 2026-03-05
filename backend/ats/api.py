# custom
from ats_engine.parser.mparser import parse_resume
from ats_engine.parser.sparser import ResumeParser
from ninja import File, Router
from ninja.errors import HttpError
from ninja.files import UploadedFile
from ninja_jwt.authentication import JWTAuth

from ats.schemas import ParserSchema

router = Router()


@router.post("/parser", response={200: dict, 400: dict})
def parser_pdf(request, pdf_file: UploadedFile = File(...)) -> dict:

    try:
        half_parser = parse_resume(pdf_file.read())
        print(f"[LOG] [`api ats file`] : {half_parser}")
        result = ResumeParser(half_parser).parse()
        return result
    except Exception as error:
        raise HttpError(status_code=500, message=str(error))
