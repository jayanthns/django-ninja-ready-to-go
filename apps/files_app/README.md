# 📂 Files Reference App

This app serves as a reference implementation for handling file uploads, downloads, streaming, and parsing in Django Ninja.

## 🚀 Features

1. **Linear Data Upload**: Upload CSV/JSON files, validate size, and parse content.
2. **Generic File Upload**: Upload any file type with size validation.
3. **File Download**: Download generated files.
4. **File Streaming**: Stream large files (simulated).
5. **File Preview**: Preview file content.

## 🛠️ API Endpoints

### 1. Upload Linear Data

**POST** `/api/v1/files/upload/linear`

- **Input**: `file` (Multipart Form Data) - CSV or JSON.
- **Validation**: Max size **25KB**.
- **Output**: Standard API Response.

  ```json
  {
    "data": {
      "message": "File uploaded and parsed successfully.",
      "filename": "valid.csv",
      "total_rows": 10,
      "preview_rows": [...]
    },
    "trace_id": "...",
    "error": {}
  }
  ```

### 2. Upload Generic File

**POST** `/api/v1/files/upload/generic`

- **Input**: `file` (Multipart Form Data) - Any type.
- **Validation**: Max size **25KB**.
- **Output**: Standard API Response.

  ```json
  {
    "data": {
      "message": "File uploaded successfully.",
      "filename": "test.txt",
      "size": 1024,
      "human_readable_size": "1.0 KB"
    },
    "trace_id": "...",
    "error": {}
  }
  ```

### 3. Download File

**GET** `/api/v1/files/download/{filename}`

- **Output**: Downloads a dummy file (25KB).

### 4. Stream File

**GET** `/api/v1/files/stream/{filename}`

- **Output**: Streams a dummy file (25KB) in chunks.

### 5. Preview File

**GET** `/api/v1/files/preview/{filename}`

- **Output**: Returns raw text content of the dummy file.

## 💡 Implementation Details

### Service Layer (`services.py`)

- **`validate_file_size`**: Enforces the 25KB limit.
- **`parse_linear_file`**: Detects CSV vs JSON and parses accordingly.
- **`get_file_stream`**: Uses a Python generator to yield chunks for streaming.

### Views (`views.py`)

- Uses `ninja.File` and `ninja.UploadedFile` for handling uploads.
- Uses `django.http.StreamingHttpResponse` for streaming.

## ⚠️ Error Handling

All endpoints follow a standard error response structure. For example, if a file exceeds the size limit:

```json
{
  "data": null,
  "trace_id": "...",
  "error": {
    "message": "File size exceeds the limit of 25KB. Actual size: 26.0 KB"
  }
}
```

## 📂 Sample Files

For testing purposes, we have provided sample files in the `samples/` directory:

1.  **`samples/valid.csv`**: A valid CSV file with < 25KB size.
2.  **`samples/valid.json`**: A valid JSON file with < 25KB size.
3.  **`samples/generic.txt`**: A small text file for generic uploads.
4.  **`samples/large_file.txt`**: A file > 25KB to test error handling (size limit).

### How to Test with cURL

```bash
# Upload CSV
curl -X POST "http://localhost:8000/api/v1/files/upload/linear" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@apps/files_app/samples/valid.csv"

# Upload Large File (Should Fail)
curl -X POST "http://localhost:8000/api/v1/files/upload/generic" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@apps/files_app/samples/large_file.txt"
```
