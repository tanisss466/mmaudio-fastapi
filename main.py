from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import tempfile
from moviepy.editor import VideoFileClip
from supabase import create_client, Client
from dotenv import load_dotenv
import subprocess

load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

MMAUDIO_PATH = "MMAudio"  # Path to MMAudio directory

@app.get("/")
async def root():
    return {"message": "Video Processing API is running"}

@app.post("/process-video/")
async def process_video(
    file: UploadFile = File(...),
    prompt: str = "add background music that matches the video mood"
):
    try:
        # Create temp directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save uploaded video
            input_path = os.path.join(temp_dir, "input_video.mp4")
            with open(input_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)

            # Process video with MMAudio
            output_dir = os.path.join(temp_dir, "output")
            os.makedirs(output_dir, exist_ok=True)

            # Run MMAudio processing
            command = [
                "python",
                os.path.join(MMAUDIO_PATH, "demo.py"),
                f"--video={input_path}",
                f"--prompt={prompt}",
                f"--output_dir={output_dir}"
            ]

            process = subprocess.run(
                command,
                cwd=MMAUDIO_PATH,
                capture_output=True,
                text=True
            )

            if process.returncode != 0:
                raise HTTPException(
                    status_code=500,
                    detail=f"MMAudio processing failed: {process.stderr}"
                )

            # Find the processed video file
            output_video = None
            for filename in os.listdir(output_dir):
                if filename.endswith(".mp4"):
                    output_video = os.path.join(output_dir, filename)
                    break

            if not output_video:
                raise HTTPException(
                    status_code=500,
                    detail="Could not find processed video"
                )

            # Upload to Supabase Storage
            with open(output_video, "rb") as f:
                file_content = f.read()
                
            bucket_name = "processed-videos"
            file_path = f"videos/{file.filename}"
            
            # Upload to Supabase Storage
            result = supabase.storage \
                .from_(bucket_name) \
                .upload(file_path, file_content)

            # Get public URL
            public_url = supabase.storage \
                .from_(bucket_name) \
                .get_public_url(file_path)

            return {
                "status": "success",
                "message": "Video processed successfully",
                "video_url": public_url
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)