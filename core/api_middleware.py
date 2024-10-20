# middleware.py
import os
from django.http import JsonResponse
from dotenv import load_dotenv
from django.urls import resolve

# Load environment variables
load_dotenv()

class APIKeyValidationMiddleware:
    """
    Middleware to check if the request contains a valid API key in the headers.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.valid_api_key = os.getenv('API_KEY', "ddfdddd")

    def __call__(self, request):
        url_name = resolve(request.path_info).url_name

        if url_name in ['schema-swagger-ui', 'schema-redoc']:
            # For debugging purposes
            return self.get_response(request)

        # Get the API key from the request header
        api_key = request.headers.get('X-API-Key')

        # Check if the API key is present and valid
        if not api_key or api_key != self.valid_api_key:
            return JsonResponse({'error': 'Invalid or missing API key'}, status=403)

        # Proceed to the next middleware or view
        response = self.get_response(request)
        return response
