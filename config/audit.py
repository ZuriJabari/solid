from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
import logging
import json
from datetime import datetime

# Configure audit logger
audit_logger = logging.getLogger('audit')
audit_logger.setLevel(logging.INFO)

# File handler for audit logs
handler = logging.FileHandler('audit.log')
handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
audit_logger.addHandler(handler)

def log_action(user, obj, action_flag, change_message=''):
    """
    Log an action in both admin log and audit log
    """
    if not user:
        user_id = None
        username = 'system'
    else:
        user_id = user.id
        username = user.username

    # Create admin log entry
    LogEntry.objects.log_action(
        user_id=user_id,
        content_type_id=ContentType.objects.get_for_model(obj).pk,
        object_id=obj.pk,
        object_repr=force_str(obj),
        action_flag=action_flag,
        change_message=change_message
    )

    # Create audit log entry
    action_type = {
        ADDITION: 'CREATE',
        CHANGE: 'UPDATE',
        DELETION: 'DELETE'
    }.get(action_flag, 'UNKNOWN')

    log_data = {
        'timestamp': datetime.now().isoformat(),
        'user': username,
        'action': action_type,
        'model': obj._meta.model_name,
        'object_id': obj.pk,
        'changes': change_message
    }

    audit_logger.info(json.dumps(log_data))

class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log request
        self._log_request(request)
        
        response = self.get_response(request)
        
        # Log response
        self._log_response(request, response)
        
        return response

    def _log_request(self, request):
        if hasattr(request, 'user'):
            username = request.user.username if request.user.is_authenticated else 'anonymous'
        else:
            username = 'anonymous'

        log_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'REQUEST',
            'user': username,
            'method': request.method,
            'path': request.path,
            'ip': request.META.get('REMOTE_ADDR'),
        }

        audit_logger.info(json.dumps(log_data))

    def _log_response(self, request, response):
        if hasattr(request, 'user'):
            username = request.user.username if request.user.is_authenticated else 'anonymous'
        else:
            username = 'anonymous'

        log_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'RESPONSE',
            'user': username,
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
        }

        audit_logger.info(json.dumps(log_data)) 