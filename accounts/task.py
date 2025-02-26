from resolve_erp.celery import shared_task
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import os
from django.contrib.auth.tokens import PasswordResetTokenGenerator

@shared_task
def send_invitation_email(user_id):
    from .models import User  
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return

    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)
    reset_url = os.environ.get('FRONTEND_RESET_PASSWORD_URL')
    reset_url_with_token = f"{reset_url}?token={token}&uid={user.pk}"

    context = {
        'user': user,
        'invitation_link': reset_url_with_token
    }
    subject = 'Você foi convidado para o sistema'
    html_content = render_to_string('invitation-email.html', context)

    email = EmailMessage(
        subject=subject,
        body=html_content,
        to=[user.email]
    )
    email.content_subtype = "html"
    email.send()
