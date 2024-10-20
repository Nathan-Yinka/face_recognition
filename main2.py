import os
import cv2
from deepface import DeepFace
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Paths to the two images
image1_path = 'download.jpeg'
image2_path = 'download.jpeg'

# List of supported models
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

def load_model_from_env():
    """Load the model name from the environment variable."""
    model_name = os.getenv("DEEPFACE_MODEL", "OpenFace")
    if model_name not in MODELS:
        raise ValueError(f"Invalid model specified: {model_name}. Must be one of {MODELS}.")
    return model_name

def is_image_accessible(image_path):
    """Check if the image file exists and is accessible."""
    if not os.path.isfile(image_path):
        return False, f"File not found: {image_path}"
    try:
        # Try to open the image with OpenCV
        image = cv2.imread(image_path)
        if image is None:
            return False, f"Unable to read image file: {image_path}"
        return True, None
    except Exception as e:
        return False, f"Error accessing image: {str(e)}"

def check_face_detection(image_path, model_name, backends=['opencv', 'mtcnn', 'ssd', 'dlib']):
    """Check if a face is detected in the image using multiple detection backends."""
    for backend in backends:
        try:
            # Try to verify the face with itself to check if a face is present
            DeepFace.verify(img1_path=image_path, img2_path=image_path, enforce_detection=False, detector_backend=backend, model_name=model_name)
            return True, None  # Face detected successfully
        except ValueError as e:
            # If no face is detected, catch the ValueError
            if "Face could not be detected" in str(e):
                continue  # Try the next backend
            else:
                return False, f"Detection error with {backend}: {str(e)}"
        except Exception as e:
            # Log any other unexpected errors
            return False, f"Unexpected error with {backend}: {str(e)}"
    
    # If all backends fail to detect a face
    return False, "No face detected using available backends"

def main():
    try:
        # Step 1: Load model from environment
        model_name = load_model_from_env()

        # Step 2: Check if both image files are accessible
        accessible1, error1 = is_image_accessible(image1_path)
        accessible2, error2 = is_image_accessible(image2_path)
        
        if not accessible1:
            raise Exception(f"First image issue: {error1}")
        if not accessible2:
            raise Exception(f"Second image issue: {error2}")
        
        # Step 3: Check if faces are detected in both images
        face1_detected, error1 = check_face_detection(image1_path, model_name)
        face2_detected, error2 = check_face_detection(image2_path, model_name)
        
        if not face1_detected:
            raise Exception(f"No valid face detected in the first image: {error1}")
        if not face2_detected:
            raise Exception(f"No valid face detected in the second image: {error2}")
        
        # Step 4: Proceed to compare the faces using DeepFace with the specified model
        result = DeepFace.verify(img1_path=image1_path, img2_path=image2_path, model_name=model_name, enforce_detection=True)
        print("DeepFace: Are the faces identical?", result["verified"])
        print("DeepFace: Similarity score:", result["distance"])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
