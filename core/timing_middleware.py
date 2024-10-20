import time

class TimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        elapsed_time = time.time() - start_time
        print(f"Request took {elapsed_time:.4f} seconds")
        return response
