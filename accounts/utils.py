from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework.exceptions import ValidationError as DRFValidationError

def custom_exception_handler(exc, context):
    """
    Custom exception handler for REST framework that handles Django and DRF exceptions.
    """
    if isinstance(exc, DjangoValidationError):
        exc = DRFValidationError(detail={"error": exc.messages})

    if isinstance(exc, Http404):
        exc = DRFValidationError(detail={
            "error": "요청하신 리소스를 찾을 수 없습니다.",
            "detail": str(exc)
        })

    response = exception_handler(exc, context)

    if response is None:
        if isinstance(exc, Exception):
            return Response(
                {"error": "서버 오류가 발생했습니다.", "detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return None

    if isinstance(exc, DRFValidationError):
        response_data = {
            "status": "error",
            "status_code": response.status_code,
            "errors": response.data,
            "request_path": context["request"].path,
            "request_method": context["request"].method,
        }
        
        # 필드별 오류 메시지를 한글로 변환
        if isinstance(response.data, dict):
            for field, errors in response.data.items():
                if isinstance(errors, list):
                    translated_errors = []
                    for error in errors:
                        if "This field is required" in str(error):
                            translated_errors.append(f"{field} 필드는 필수입니다.")
                        elif "This field may not be blank" in str(error):
                            translated_errors.append(f"{field} 필드는 비워둘 수 없습니다.")
                        elif "Enter a valid email address" in str(error):
                            translated_errors.append("유효한 이메일 주소를 입력해주세요.")
                        else:
                            translated_errors.append(str(error))
                    response_data["errors"][field] = translated_errors

        response.data = response_data

    return response
