# views.py
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import FaceComparisonSerializer
from .utils.deepface_service import compare_faces
from dotenv import load_dotenv
load_dotenv()
import os

class FaceComparisonView(APIView):
    """API view to handle face comparison requests."""
    fixed_threshold = int(os.getenv("FIXED_THRESHOLD",50))

    def handle_exception(self, exc):
        """
        Custom exception handler for this view only.
        """
        # Check if it's a validation error
        if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
            # Simplify error messages
            errors = {}
            for field, messages in exc.detail.items():
                if isinstance(messages, list):  # Handle list of error messages
                    # Extract only the message string, ignoring 'ErrorDetail' structure
                    errors[field] = " ".join(
                        str(message).split("string='")[1].split("',")[0] if "string='" in str(message) else str(message)
                        for message in messages
                    )
                else:
                    # Handle non-list error messages
                    errors[field] = str(messages)

            # Combine all error messages into a single string
            detailed_reason = " | ".join(f"{field}: {msg}" for field, msg in errors.items())

            # Create a custom payload similar to the 200 response format
            payload = {
                "status": False,
                "reason": detailed_reason,  # Clear and explanatory error message
                "confidenceLevel": None,
                "threshold": self.fixed_threshold,
                "match": False,
                "image1": self.request.data.get("image1", None),
                "image2": self.request.data.get("image2", None),
            }
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        # Default behavior for other exceptions
        return super().handle_exception(exc)


    @swagger_auto_schema(
        request_body=FaceComparisonSerializer,
        manual_parameters=[
            openapi.Parameter(
                'X-API-Key',
                openapi.IN_HEADER,
                description="API key for authentication",
                type=openapi.TYPE_STRING,
                required=True
            ),
        ],
        responses={
            200: openapi.Response(
                description="Successful Face Comparison",
                examples={
                    "application/json": {
                        "verified": True,
                        "message": "Similarity score: 0.25"
                    }
                }
            ),
            403: openapi.Response(
                description="Forbidden - Invalid API Key",
                examples={
                    "application/json": {
                        "error": "Invalid or missing API key"
                    }
                }
            ),
            400: openapi.Response(
                description="Validation Error",
                examples={
                    "application/json": {
                        "error": "Failed to download the first image: Invalid URL"
                    }
                }
            ),
        },
        operation_description="Compare two faces based on the provided images. The images can be provided as URLs or Base64-encoded strings.",
    )
    def post(self, request, *args, **kwargs):
        try:
            serializer = FaceComparisonSerializer(data=request.data)
            serializer.is_valid(raise_exception=True) 
            image1_path = serializer.validated_data["image1_temp_path"]
            image2_path = serializer.validated_data["image2_temp_path"]
            image1 = serializer.validated_data["image1"]
            image2 = serializer.validated_data["image2"]
            

            # Step 3: Compare the faces
            result,error_message_or_path = compare_faces(image1_path, image2_path)
            
            # clean up process
            temp_image_path = [image1_path,image2_path]
            if isinstance(error_message_or_path,list):
                temp_image_path = temp_image_path + error_message_or_path
        
            for path in temp_image_path:
                try:
                    os.remove(path)
                except:
                    continue
            
                
            if result:
                confidence_level,fixed_threshold,verified,reason = self.calculate_confidence(result,self.fixed_threshold)
                payload = {
                    "status": True,
                    "reason": reason,
                    "confidenceLevel": confidence_level,
                    "threshold": fixed_threshold,
                    "match": verified,
                    "image1": image1,
                    "image2": image2,
                }
                return Response(payload, status=status.HTTP_200_OK)
            
            else:
                payload = {
                    "status": False,
                    "reason": error_message_or_path,
                    "confidenceLevel": None,
                    "threshold":  fixed_threshold,
                    "match": False,
                    "image1": image1,
                    "image2": image2,
                }
                return Response({"error": payload}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            print(f"Exception caught in post method: {e}")
            raise e


    def calculate_confidence(self, result, fixed_threshold=80):
        print(result)
        # Extract the original distance
        distance = result.get('distance', 0.0)
        confidence_level = (1 - distance) * 100
        print(confidence_level)

        # Clamp and round the confidence level
        confidence_level = round(max(min(confidence_level, 100), 0))

        verified = confidence_level >= fixed_threshold
        reason = "Images Match" if verified else "Image does not match"
        
        return confidence_level, fixed_threshold,verified,reason
