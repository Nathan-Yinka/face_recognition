import re
import base64
import urllib.request
import tempfile
import requests
import os
from rest_framework import serializers

class FaceComparisonSerializer(serializers.Serializer):
    image1 = serializers.CharField(required=True)
    image2 = serializers.CharField(required=True)

    MAX_FILE_SIZE_MB = 1  # Maximum allowed size in MB

    def validate_image_format(self, value, field_name):
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
                {field_name: "The provided value must be either a valid URL or a Base64-encoded image."}
            )

    def validate_file_size(self, file_path, field_name):
        """Validate that the file size does not exceed the allowed limit."""
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)  # Convert bytes to MB
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            raise serializers.ValidationError(
                {field_name: f"The file size must not exceed {self.MAX_FILE_SIZE_MB}MB. Provided size: {file_size_mb:.2f}MB."}
            )

    def download_image_to_temp_file(self, image_url):
        """Download the image from a URL and save it to a temporary file."""
        try:
            supported_formats = ['.jpg', '.jpeg', '.png']
            file_extension = os.path.splitext(image_url)[-1].lower()
            if file_extension not in supported_formats:
                raise serializers.ValidationError(f"Unsupported file format: {file_extension}")

            # Create a temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)

            # Download the image directly into the temporary file
            urllib.request.urlretrieve(image_url, temp_file.name)

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
        image1_type = self.validate_image_format(data.get("image1"), "image1")
        image2_type = self.validate_image_format(data.get("image2"), "image2")

        # Download images or decode Base64 strings to temporary files
        if image1_type == "url":
            try:
                image1_temp_path = self.download_image_to_temp_file(data.get("image1"))
            except serializers.ValidationError as e:
                raise serializers.ValidationError({"image1": str(e)})
        else:
            try:
                image1_temp_path = self.decode_base64_image(data.get("image1"))
            except serializers.ValidationError as e:
                raise serializers.ValidationError({"image1": str(e)})

        # Validate image1 size
        self.validate_file_size(image1_temp_path, "image1")

        if image2_type == "url":
            try:
                image2_temp_path = self.download_image_to_temp_file(data.get("image2"))
            except serializers.ValidationError as e:
                raise serializers.ValidationError({"image2": str(e)})
        else:
            try:
                image2_temp_path = self.decode_base64_image(data.get("image2"))
            except serializers.ValidationError as e:
                raise serializers.ValidationError({"image2": str(e)})

        # Validate image2 size
        self.validate_file_size(image2_temp_path, "image2")

        # Store the temporary file paths in the validated data for later use
        data["image1_temp_path"] = image1_temp_path
        data["image2_temp_path"] = image2_temp_path
        data["image1"] = data.get("image1")
        data["image2"] = data.get("image2")

        return data
