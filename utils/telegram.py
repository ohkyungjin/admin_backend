import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

def send_telegram_message(message):
    """텔레그램으로 메시지를 전송합니다."""
    try:
        bot_token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID
        
        logger.debug(f"Bot token: {bot_token}")
        logger.debug(f"Chat ID: {chat_id}")
        logger.info(f"Sending telegram message to chat_id: {chat_id}")
        logger.info(f"Message content: {message}")
        
        url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        data = {'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'}
        
        logger.debug(f"Sending request to URL: {url}")
        logger.debug(f"Request data: {data}")
        
        response = requests.post(url, data=data, timeout=10)
        response_data = response.json()
        
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.headers)}")
        logger.debug(f"Response data: {response_data}")
        
        if not response.ok:
            logger.error(f"Telegram API error. Status code: {response.status_code}, Response: {response_data}")
            return False
            
        logger.info(f"Telegram message sent successfully. Response: {response_data}")
        return True
    except requests.Timeout:
        logger.error("Telegram API request timed out after 10 seconds")
        return False
    except requests.RequestException as e:
        logger.error(f"Network error while sending telegram message: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while sending telegram message: {str(e)}")
        logger.exception("Full traceback:")
        return False

def format_purchase_order_message(instance, action):
    """발주서 관련 텔레그램 메시지를 포맷팅합니다."""
    try:
        logger.debug(f"Formatting message for purchase order: {instance.order_number}, action: {action}")
        
        # 상태별 이모지와 제목
        action_info = {
            'created': ('📝', '발주서 작성'),
            'pending': ('⏳', '발주서 승인 요청'),
            'approved': ('✅', '발주서 승인 완료'),
            'ordered': ('📦', '발주서 발주 완료'),
            'received': ('🚚', '발주서 입고 완료'),
            'cancelled': ('❌', '발주서 취소')
        }
        
        emoji, title = action_info.get(action, ('❓', '발주서 상태 변경'))
        
        # 처리자 정보
        user_info = {
            'created': instance.created_by,
            'pending': instance.created_by,
            'approved': instance.approved_by,
            'ordered': instance.ordered_by,
            'received': instance.received_by,
            'cancelled': instance.created_by
        }
        
        # 메시지 구성
        message = f"{emoji} {title}\n\n"
        message += "📋 발주 정보\n"
        message += f"- 발주번호: {instance.order_number}\n"
        message += f"- 공급업체: {instance.supplier.name}\n"
        message += f"- 발주금액: {'{:,}'.format(instance.total_amount)}원\n"
        message += f"- 상태: {instance.get_status_display()}\n\n"
        
        message += "📦 발주 품목\n"
        for item in instance.items.all():
            message += f"- {item.item.name}: {item.quantity}개 x {'{:,}'.format(item.unit_price)}원\n"
        
        message += f"\n👤 처리자: {user_info[action].name}"
        
        logger.debug(f"Formatted message: {message}")
        return message
    except Exception as e:
        logger.error(f"Failed to format purchase order message. Error: {str(e)}")
        logger.error(f"Instance data: order_number={instance.order_number}, action={action}")
        logger.exception("Full traceback:")
        raise
