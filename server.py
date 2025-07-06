from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import requests
import os

app = FastAPI()

# Make sure the images directory exists
images_dir = Path("images")
images_dir.mkdir(parents=True, exist_ok=True)

# Serve the 'images/' directory statically at '/images'
app.mount("/images", StaticFiles(directory=str(images_dir)), name="images")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/images")
def list_images(request: Request):
    base_url = str(request.base_url).rstrip("/")
    files = [f.name for f in images_dir.iterdir() if f.is_file()]
    urls = [f"{base_url}/images/{filename}" for filename in files]
    return urls

@app.post("/upload-urls/")
async def upload_urls(file: UploadFile = File(...)):
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are allowed")

    contents = await file.read()
    urls = contents.decode("utf-8").splitlines()

    for url in urls:
        url = url.strip()
        if not url:
            continue
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            filename = url.split("/")[-1]
            filepath = images_dir / filename
            with open(filepath, "wb") as f:
                f.write(response.content)
        except Exception as e:
            print(f"Failed to download {url}: {e}")

    return {"status": "done", "downloaded": len(urls)}

@app.post("/remove-images")
def remove_all_images():
    removed_files = []
    for file in images_dir.iterdir():
        if file.is_file():
            removed_files.append(file.name)
            file.unlink()
    return {"status": "deleted", "files_removed": removed_files}