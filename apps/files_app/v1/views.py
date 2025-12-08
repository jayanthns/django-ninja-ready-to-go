from typing import Any, Dict

from django.http import HttpResponse, StreamingHttpResponse
from ninja import File, Router, UploadedFile
from ninja.errors import HttpError

from common.base_schemas import create_api_response_schema

from .schemas import FileSuccessSchema, LinearDataResponseSchema
from .services import FileService

router = Router()


@router.post(
    "/upload/linear",
    response={200: create_api_response_schema(LinearDataResponseSchema), 400: Dict[str, Any]},
)
def upload_linear_file(request, file: UploadedFile = File(...)):
    """
    Uploads a linear data file (CSV or JSON), validates size (25KB limit),
    and returns the top 10 records.
    """
    request.logger.info("[1] Entering upload_linear_file")
    try:
        # 1. Validate size
        request.logger.info("[2] Validating file size")
        FileService.validate_file_size(file, limit_kb=25)

        # 2. Parse file
        request.logger.info("[3] Parsing file")
        data = FileService.parse_linear_file(file)

        response_data = {
            "message": "File uploaded and parsed successfully.",
            "filename": file.name,
            "total_rows": len(data),
            "preview_rows": data,
            "human_readable_size": FileService.get_human_readable_size(file.size),
        }

        request.logger.info("[4] Exiting upload_linear_file")
        return {"data": response_data, "trace_id": str(request.trace_id), "error": {}}
    except HttpError as e:
        request.logger.info(f"[5] Error in upload_linear_file: {e}")
        return 400, {"data": None, "trace_id": str(request.trace_id), "error": {"message": str(e)}}


@router.post(
    "/upload/generic", response={200: create_api_response_schema(FileSuccessSchema), 400: Dict[str, Any]}
)
def upload_generic_file(request, file: UploadedFile = File(...)):
    """
    Uploads any file, validates size (25KB limit), and returns success.
    """
    request.logger.info("[1] Entering upload_generic_file")
    try:
        # 1. Validate size
        request.logger.info("[2] Validating file size")
        FileService.validate_file_size(file, limit_kb=25)

        response_data = {
            "message": "File uploaded successfully.",
            "filename": file.name,
            "size": file.size,
            "human_readable_size": FileService.get_human_readable_size(file.size),
        }

        request.logger.info("[3] Exiting upload_generic_file")
        return {"data": response_data, "trace_id": str(request.trace_id), "error": {}}
    except HttpError as e:
        request.logger.info(f"[4] Error in upload_generic_file: {e}")
        return 400, {"data": None, "trace_id": str(request.trace_id), "error": {"message": str(e)}}


@router.get("/download/{filename}")
def download_file(request, filename: str):
    """
    Downloads a dummy file of 25KB.
    """
    request.logger.info(f"[1] Entering download_file: {filename}")
    content = FileService.get_file_content(filename, size_kb=25)
    response = HttpResponse(content, content_type="text/plain")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    request.logger.info("[2] Exiting download_file")
    return response


@router.get("/stream/{filename}")
def stream_file(request, filename: str):
    """
    Streams a dummy file of 25KB.
    """
    request.logger.info(f"[1] Entering stream_file: {filename}")
    stream_generator = FileService.get_file_stream(filename, size_kb=25)
    response = StreamingHttpResponse(stream_generator, content_type="text/plain")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    request.logger.info("[2] Exiting stream_file")
    return response


@router.get("/preview/{filename}")
def preview_file(request, filename: str):
    """
    Previews the content of a dummy file (25KB).
    """
    request.logger.info(f"[1] Entering preview_file: {filename}")
    content = FileService.get_file_content(filename, size_kb=25)
    request.logger.info("[2] Exiting preview_file")
    return HttpResponse(content, content_type="text/plain")
