import logging
import json
import time
from django.http import HttpResponse

logger = logging.getLogger('funeral')

class FuneralLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Request 로깅
        start_time = time.time()
        
        # Request body 로깅
        if request.body:
            try:
                body = json.loads(request.body)
            except json.JSONDecodeError:
                body = request.body.decode('utf-8')
        else:
            body = None

        request_log = {
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.GET),
            'body': body,
            'headers': dict(request.headers),
        }
        
        logger.debug(f'Request: {json.dumps(request_log, ensure_ascii=False, indent=2)}')

        # Response 처리
        response = self.get_response(request)
        
        # Response 로깅
        if isinstance(response, HttpResponse):
            try:
                if hasattr(response, 'content'):
                    if 'application/json' in response.get('Content-Type', ''):
                        response_body = json.loads(response.content.decode('utf-8'))
                    else:
                        response_body = response.content.decode('utf-8')
                else:
                    response_body = None
            except:
                response_body = 'Unable to decode response body'
        else:
            response_body = 'Non-HttpResponse object'

        process_time = time.time() - start_time
        
        response_log = {
            'status_code': getattr(response, 'status_code', None),
            'headers': dict(getattr(response, 'headers', {})),
            'body': response_body,
            'process_time': f'{process_time:.3f}s'
        }
        
        logger.debug(f'Response: {json.dumps(response_log, ensure_ascii=False, indent=2)}')

        return response
