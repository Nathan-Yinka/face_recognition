import os
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
import cv2
import requests
import tempfile
import numpy as np
import time
from multiprocessing import Process, Queue
from deepface import DeepFace
from retinaface import RetinaFace
from dotenv import load_dotenv
from mtcnn import MTCNN

# Load environment variables
load_dotenv()

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

# Load the DeepFace model once
model_name = os.getenv("DEEPFACE_MODEL", "Facenet512")
if model_name not in MODELS:
    raise ValueError(f"Invalid model specified: {model_name}. Must be one of {MODELS}.")
deepface_model = DeepFace.build_model(model_name)

def download_image_to_temp_file(image_url):
    """Download the image from a URL and save it to a temporary file."""
    try:
        supported_formats = ['.jpg', '.jpeg', '.png']
        file_extension = os.path.splitext(image_url)[-1].lower()
        if file_extension not in supported_formats:
            return None, f"Unsupported file format: {file_extension}"

        response = requests.get(image_url, stream=True)
        response.raise_for_status()

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
        with open(temp_file.name, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        return temp_file.name, None

    except Exception as e:
        return None, str(e)

def align_face_with_retinaface(image_path, to_grayscale=True,downscale_factor=0.5):
    """Align the face in the image using RetinaFace and optionally convert to grayscale."""
    try:
        total_start_time = time.time()  # Start the total timer
        
        # Step 1: Load the image and optionally downscale it
        start_time = time.time()
        image = cv2.imread(image_path)
        if image is None:
            return None, "Image not found or could not be opened."


        original_size = image.shape[:2]  # (height, width)
        if downscale_factor < 1.0:
            image = cv2.resize(image, (int(original_size[1] * downscale_factor), int(original_size[0] * downscale_factor)))
        loading_and_resizing_time = time.time() - start_time
        print(f"Time taken for loading and resizing: {loading_and_resizing_time:.4f} seconds")

        # Step 2: Face detection with RetinaFace
        start_time = time.time()
        extracted_faces = RetinaFace.extract_faces(img_path=image, align=False)
        face_detection_time = time.time() - start_time
        print(f"Time taken for face detection: {face_detection_time:.4f} seconds")


        if len(extracted_faces) == 0:
            return None, "No faces detected."

        # Step 2: Grayscale conversion (if required)
        start_time = time.time()
        if to_grayscale:
            processed_face = cv2.cvtColor(extracted_faces[0], cv2.COLOR_BGR2GRAY)
        else:
            processed_face = extracted_faces[0]
        grayscale_conversion_time = time.time() - start_time
        print(f"Time taken for grayscale conversion: {grayscale_conversion_time:.4f} seconds")

        # Step 3: Saving the processed image to a temporary file
        start_time = time.time()
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        cv2.imwrite(temp_file.name, processed_face)
        saving_time = time.time() - start_time
        print(f"Time taken for saving the image: {saving_time:.4f} seconds")

        total_elapsed_time = time.time() - total_start_time
        print(f"Total time taken for alignment: {total_elapsed_time:.4f} seconds")
        print(f"Saved aligned face to: {temp_file.name}")

        return temp_file.name, None

    except Exception as e:
        return None, str(e)
    
    
def align_face_with_mtcnn(image_path, to_grayscale=True, downscale_factor=0.5):
    """Align the face in the image using MTCNN, optionally convert to grayscale, and save to a file."""
    try:
        total_start_time = time.time()  # Start the total timer

        # Step 1: Load the image and optionally downscale it
        start_time = time.time()
        image = cv2.imread(image_path)
        if image is None:
            return None, "Image not found or could not be opened."

        original_size = image.shape[:2]  # (height, width)
        if downscale_factor < 1.0:
            image = cv2.resize(image, (int(original_size[1] * downscale_factor), int(original_size[0] * downscale_factor)))
        loading_and_resizing_time = time.time() - start_time
        # print(f"Time taken for loading and resizing: {loading_and_resizing_time:.4f} seconds")

        # Step 2: Face detection with MTCNN
        start_time = time.time()
        detector = MTCNN()
        faces = detector.detect_faces(image)
        face_detection_time = time.time() - start_time
        # print(f"Time taken for face detection: {face_detection_time:.4f} seconds")

        if len(faces) == 0:
            return None, "No faces detected."

        # Get the bounding box of the first detected face
        x, y, width, height = faces[0]['box']
        x, y = max(0, x), max(0, y)
        face_image = image[y:y + height, x:x + width]

        # Step 3: Grayscale conversion (if required)
        start_time = time.time()
        if to_grayscale:
            processed_face = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
        else:
            processed_face = face_image
        grayscale_conversion_time = time.time() - start_time
        # print(f"Time taken for grayscale conversion: {grayscale_conversion_time:.4f} seconds")

        # Step 4: Save the processed face to a temporary file
        start_time = time.time()
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        cv2.imwrite(temp_file.name, processed_face)
        saving_time = time.time() - start_time
        # print(f"Time taken for saving the image: {saving_time:.4f} seconds")

        total_elapsed_time = time.time() - total_start_time
        # print(f"Total time taken for alignment: {total_elapsed_time:.4f} seconds")

        # Return the file path of the saved image
        return temp_file.name, None

    except Exception as e:
        return None, str(e)



# def process_image(image_path, result_queue, target_size=(224, 224), to_grayscale=True):
#     """Process the image: align the face and check detection."""
#     print(f"Processing image: {image_path}")
#     aligned_image_path, error = align_face_with_mtcnn(image_path, to_grayscale)
#     if aligned_image_path is None:
#         result_queue.put((False, f"Alignment failed: {error}"))
#         return

#     result_queue.put((True, aligned_image_path))

def process_image(image_path, target_size=(224, 224), to_grayscale=True):
    """Process the image: align the face and check detection."""
    print(f"Processing image: {image_path}")
    aligned_image_path, error = align_face_with_mtcnn(image_path, to_grayscale)
    if aligned_image_path is None:
        return False, f"Alignment failed: {error}"
    return True, aligned_image_path



def compare_faces(image1_path, image2_path):
    """Compare two faces using DeepFace without multiprocessing."""
    # Process the first image
    result1, aligned_image1_path = process_image(image1_path)
    if not result1:
        aligned_image1_path = image1_path  # Use original if alignment fails

    # Process the second image
    result2, aligned_image2_path = process_image(image2_path)
    if not result2:
        aligned_image2_path = image2_path  # Use original if alignment fails

    try:
        # Compare the aligned faces using the loaded DeepFace model
        result = DeepFace.verify(
            img1_path=aligned_image1_path,
            img2_path=aligned_image2_path,
            model_name=model_name,
            enforce_detection=False
        )
        return result, [aligned_image1_path, aligned_image2_path]
    except Exception as e:
        return False, str(e)

# def compare_faces(image1_path, image2_path):
#     """Compare two faces using DeepFace in a multiprocessing way."""
#     result_queue1 = Queue()
#     result_queue2 = Queue()

#     process1 = Process(target=process_image, args=(image1_path, result_queue1))
#     process2 = Process(target=process_image, args=(image2_path, result_queue2))
#     process1.start()
#     process2.start()

#     process1.join()
#     process2.join()

#     result1, aligned_image1_path = result_queue1.get()
#     result2, aligned_image2_path = result_queue2.get()

#     if not result1:
#         # return False, f"First image processing failed: {aligned_image1_path}"
#         aligned_image1_path = image1_path
#     if not result2:
#         # return False, f"Second image processing failed: {aligned_image2_path}"
#         aligned_image2_path = image2_path

#     # print("this stage has gotten here",aligned_image1_path,aligned_image2_path)
#     try:
#         # Compare the aligned faces using the loaded DeepFace model
#         result = DeepFace.verify(
#             img1_path=aligned_image1_path, img2_path=aligned_image2_path,
#             model_name=model_name, enforce_detection=False
#         )
        
#         return result, [aligned_image1_path,aligned_image2_path]
#     except Exception as e:
#         return False, str(e)

# Example usage
if __name__ == "__main__":
    image_url1 = 'https://support.umoeno.com/images/users/d290c070-d031-42c2-a7cb-6142e5be113d.png'
    image_url2 = 'https://support.umoeno.com/images/users/d290c070-d031-42c2-a7cb-6142e5be113d.png'

    image1_path, error1 = download_image_to_temp_file(image_url1)
    image2_path, error2 = download_image_to_temp_file(image_url2)
    image1_path = "download (4).jpeg"
    image2_path = "download.jpeg"
    if image1_path is None or image2_path is None:
        print(f"Error downloading images: {error1 or error2}")
    else:
        # Compare the faces using multiprocessing
        verified, message = compare_faces(image1_path, image2_path)
        print(f"Verification result: {verified}, Message: {message}")
