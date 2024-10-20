# gunicorn_config.py

from deepface import DeepFace
import os

MODELS = [
    "VGG-Face", 
    "Facenet", 
    "Facenet512", 
    "OpenFace", 
    "DeepFace", 
    "DeepID", 
    "ArcFace", 
    "Dlib", 
    "SFace", 
    "GhostFaceNet"
]

# Global variable to hold the model
deepface_model = None

def post_fork(server, worker):
    """Load the DeepFace model after the worker process is forked."""
    global deepface_model
    model_name = os.getenv("DEEPFACE_MODEL", "VGG-Face")
    if model_name not in MODELS:
        raise ValueError(f"Invalid model specified: {model_name}. Must be one of {MODELS}.")
    
    # Load the model
    deepface_model = DeepFace.build_model(model_name)
    server.log.info(f"{model_name} model loaded in worker {worker.pid}")
