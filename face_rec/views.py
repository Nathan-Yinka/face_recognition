# views.py
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import FaceComparisonSerializer
from .utils.deepface_service import compare_faces

class FaceComparisonView(APIView):
    """API view to handle face comparison requests."""

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
        serializer = FaceComparisonSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
        fixed_threshold = 50
            
        if result:
            confidence_level,fixed_threshold,verified = self.calculate_confidence(result,fixed_threshold)
            payload = {
                "status": verified,
                "reason": None,
                "confidenceLevel": confidence_level,
                "threshold": fixed_threshold,
                "match": result["verified"],
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


    def calculate_confidence(self, result, fixed_threshold=80):
        print(result)
        # Extract the original distance
        distance = result.get('distance', 0.0)
        confidence_level = (1 - distance) * 100
        print(confidence_level)

        confidence_level = max(min(confidence_level, 100), 0)

        verified = confidence_level >= fixed_threshold
        
        return confidence_level, fixed_threshold,verified

        
    # def calculate_confidence_level(self,result):
    #     distance = result.get('distance')
    #     threshold = result.get('threshold', 1.0)

    #     normalized_distance = min(distance / threshold, 1)

    #     # Scale the confidence level to be between 80 and 100
    #     confidence_level = 100 - (normalized_distance * 20)

    #     return int(confidence_level)
