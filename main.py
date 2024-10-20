import face_recognition
from deepface import DeepFace

# Paths to the two images
image1_path = 'download (3).jpeg'
image2_path = 'download (3).jpeg'

# --------- Using face_recognition ---------
# Load the images
image1 = face_recognition.load_image_file(image1_path)
image2 = face_recognition.load_image_file(image2_path)

# Get face encodings for each image
print(face_recognition.face_encodings(image1))
face_encoding1 = face_recognition.face_encodings(image1)[0]
face_encoding2 = face_recognition.face_encodings(image2)[0]

# Compare the two face encodings
results = face_recognition.compare_faces([face_encoding1], face_encoding2)
distance = face_recognition.face_distance([face_encoding1], face_encoding2)

print(f"face_recognition: Are the faces identical? {results[0]}")
print(f"face_recognition: Face distance (lower is more similar): {distance[0]}")

# --------- Using DeepFace ---------
try:
    # Compare faces using DeepFace
    result = DeepFace.verify(img1_path=image1_path, img2_path=image2_path, enforce_detection=True,model_name='OpenFace')
    print("DeepFace: Are the faces identical?", result["verified"])
    print("DeepFace: Similarity score:", result["distance"])
except Exception as e:
    print(f"DeepFace comparison failed: {e}")
