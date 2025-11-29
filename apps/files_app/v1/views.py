from typing import Any, Dict, List

from django.http import HttpResponse, StreamingHttpResponse
from ninja import File, Router, UploadedFile

from common.base_schemas import create_api_response_schema

from .schemas import FileSuccessSchema, LinearDataResponseSchema
from .services import FileService

router = Router()


from ninja.errors import HttpError


@router.post(
    "/upload/linear",
    response={200: create_api_response_schema(LinearDataResponseSchema), 400: Dict[str, Any]},
)
def upload_linear_file(request, file: UploadedFile = File(...)):
    """
    Uploads a linear data file (CSV or JSON), validates size (25KB limit),
    and returns the top 10 records.
    """
    try:
        # 1. Validate size
        FileService.validate_file_size(file, limit_kb=25)

        # 2. Parse file
        data = FileService.parse_linear_file(file)

        response_data = {
            "message": "File uploaded and parsed successfully.",
            "filename": file.name,
            "total_rows": len(data),
            "preview_rows": data,
            "human_readable_size": FileService.get_human_readable_size(file.size),
        }

        return {"data": response_data, "trace_id": str(request.trace_id), "error": {}}
    except HttpError as e:
        return 400, {"data": None, "trace_id": str(request.trace_id), "error": {"message": str(e)}}


@router.post(
    "/upload/generic", response={200: create_api_response_schema(FileSuccessSchema), 400: Dict[str, Any]}
)
def upload_generic_file(request, file: UploadedFile = File(...)):
    """
    Uploads any file, validates size (25KB limit), and returns success.
    """
    try:
        # 1. Validate size
        FileService.validate_file_size(file, limit_kb=25)

        response_data = {"message": "File uploaded successfully.", "filename": file.name, "size": file.size}

        return {"data": response_data, "trace_id": str(request.trace_id), "error": {}}
    except HttpError as e:
        return 400, {"data": None, "trace_id": str(request.trace_id), "error": {"message": str(e)}}


@router.get("/download/{filename}")
def download_file(request, filename: str):
    """
    Downloads a dummy file of 25KB.
    """
    content = FileService.get_file_content(filename, size_kb=25)
    response = HttpResponse(content, content_type="text/plain")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@router.get("/stream/{filename}")
def stream_file(request, filename: str):
    """
    Streams a dummy file of 25KB.
    """
    stream_generator = FileService.get_file_stream(filename, size_kb=25)
    response = StreamingHttpResponse(stream_generator, content_type="text/plain")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@router.get("/preview/{filename}")
def preview_file(request, filename: str):
    """
    Previews the content of a dummy file (25KB).
    """
    content = FileService.get_file_content(filename, size_kb=25)
    return HttpResponse(content, content_type="text/plain")
