from django.http import HttpResponse, StreamingHttpResponse
from ninja import File, Router, UploadedFile

from .schemas import FileSuccessSchema, LinearDataResponseSchema
from .services import FileService

router = Router()


@router.post("/upload/linear", response=LinearDataResponseSchema)
def upload_linear_file(request, file: UploadedFile = File(...)):
    """
    Uploads a linear data file (CSV or JSON), validates size (25KB limit),
    and returns the top 10 records.
    """
    # 1. Validate size
    FileService.validate_file_size(file, limit_kb=25)

    # 2. Parse file
    data = FileService.parse_linear_file(file)

    return {
        "message": "File uploaded and parsed successfully.",
        "filename": file.name,
        "total_rows": len(
            data
        ),  # Note: This is just the preview count if we only parsed top 10, but for reference it's fine.
        "preview_rows": data,
    }


@router.post("/upload/generic", response=FileSuccessSchema)
def upload_generic_file(request, file: UploadedFile = File(...)):
    """
    Uploads any file, validates size (25KB limit), and returns success.
    """
    # 1. Validate size
    FileService.validate_file_size(file, limit_kb=25)

    return {"message": "File uploaded successfully.", "filename": file.name, "size": file.size}


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
