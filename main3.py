import os
import requests
import tempfile

def download_image_to_temp_file(image_url):
    """Download the image from a URL and save it to a temporary file."""
    try:
        # List of supported image formats
        supported_formats = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']

        # Determine the file extension from the URL
        file_extension = os.path.splitext(image_url)[-1].lower()
        if file_extension not in supported_formats:
            return None, f"Unsupported file format: {file_extension}"

        # Send a request to the image URL
        response = requests.get(image_url, stream=True)
        response.raise_for_status()

        # Create a temporary file with the correct file extension
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
        print(temp_file.name)
        with open(temp_file.name, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        return temp_file.name, None

    except Exception as e:
        # Handle any errors that occurred during the download process
        return None, str(e)


download_image_to_temp_file("https://support.umoeno.com/uploads/cache/c510a356-5443-4526-8fac-8e53c1571209.png")