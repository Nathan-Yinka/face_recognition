# serializers.py
import re
import base64
import tempfile
import requests
import os
from rest_framework import serializers

class FaceComparisonSerializer(serializers.Serializer):
    image1 = serializers.CharField(required=True)
    image2 = serializers.CharField(required=True)

    def validate_image_format(self, value):
        """Helper method to validate if the value is a URL or a Base64 string and return the type."""
        # Regex for checking if the string is a URL
        url_regex = re.compile(
            r'^(https?|ftp):\/\/[^\s/$.?#].[^\s]*$', re.IGNORECASE
        )
        # Regex for checking if the string is a Base64 image
        base64_regex = re.compile(
            r'^data:image\/[a-zA-Z]+;base64,([^\s]+)$', re.IGNORECASE
        )

        # Check if the input is a valid URL
        if url_regex.match(value):
            return "url"
        # Check if the input is a valid Base64-encoded string
        elif base64_regex.match(value):
            return "base64"
        else:
            raise serializers.ValidationError(
                "The provided value must be either a valid URL or a Base64-encoded image."
            )

    def download_image_to_temp_file(self, image_url):
        """Download the image from a URL and save it to a temporary file."""
        try:
            supported_formats = ['.jpg', '.jpeg', '.png']
            file_extension = os.path.splitext(image_url)[-1].lower()
            if file_extension not in supported_formats:
                raise serializers.ValidationError(f"Unsupported file format: {file_extension}")

            response = requests.get(image_url, stream=True)
            response.raise_for_status()

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
            with open(temp_file.name, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

            return temp_file.name
        except Exception as e:
            raise serializers.ValidationError(f"Failed to download the image from URL: {str(e)}")

    def decode_base64_image(self, base64_str):
        """Decode a base64 string and save it to a temporary file."""
        try:
            # Decode the Base64 string (remove the prefix "data:image/...;base64,")
            image_data = base64.b64decode(re.sub(r'^data:image\/[a-zA-Z]+;base64,', '', base64_str))

            # Create a temporary file to save the decoded image
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            with open(temp_file.name, "wb") as file:
                file.write(image_data)

            return temp_file.name
        except Exception as e:
            raise serializers.ValidationError(f"Failed to decode Base64 image: {str(e)}")

    def validate(self, data):
        # Validate both image1 and image2 fields
        image1_type = self.validate_image_format(data.get("image1"))
        image2_type = self.validate_image_format(data.get("image2"))

        # Download images or decode Base64 strings to temporary files
        if image1_type == "url":
            image1_temp_path = self.download_image_to_temp_file(data.get("image1"))
        else:
            image1_temp_path = self.decode_base64_image(data.get("image1"))

        if image2_type == "url":
            image2_temp_path = self.download_image_to_temp_file(data.get("image2"))
        else:
            image2_temp_path = self.decode_base64_image(data.get("image2"))

        # Store the temporary file paths in the validated data for later use
        data["image1_temp_path"] = image1_temp_path
        data["image2_temp_path"] = image2_temp_path
        data['image1'] = data.get("image1")
        data["image2"] = data.get("image2")

        return data
