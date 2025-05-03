import logging
import os

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from resolve_erp.celery import shared_task

# Get an instance of a logger
logger = logging.getLogger(__name__)

@shared_task
def send_invitation_email(user_id):
    from .models import User
    logger.info(f"Starting send_invitation_email task for user_id: {user_id}")
    try:
        user = User.objects.get(pk=user_id)
        logger.info(f"User found: {user.email}")
    except User.DoesNotExist:
        logger.warning(f"User with id {user_id} does not exist.")
        return
    except Exception as e:
        logger.error(f"Error fetching user with id {user_id}: {e}", exc_info=True)
        return

    try:
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        logger.debug(f"Generated token for user {user.email}")

        reset_url = os.environ.get('FRONTEND_RESET_PASSWORD_URL')
        if not reset_url:
            logger.error("FRONTEND_RESET_PASSWORD_URL environment variable not set.")
            return

        reset_url_with_token = f"{reset_url}?token={token}&uid={user.pk}"
        logger.info(f"Generated invitation link for user {user.email}")

        context = {
            'user': user,
            'invitation_link': reset_url_with_token
        }
        subject = 'Você foi convidado para o sistema'
        logger.info(f"Rendering email template for subject: '{subject}'")
        html_content = render_to_string('invitation-email.html', context)
        logger.debug("Email template rendered successfully.")

        email = EmailMessage(
            subject=subject,
            body=html_content,
            to=[user.email]
        )
        email.content_subtype = "html"
        logger.info(f"Sending invitation email to: {user.email}")
        email.send()
        logger.info(f"Invitation email sent successfully to {user.email}")
    except Exception as e:
        logger.error(f"An error occurred while sending the invitation email to {user.email}: {e}", exc_info=True)

