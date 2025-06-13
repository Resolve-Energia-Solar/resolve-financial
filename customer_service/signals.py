from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Ticket
from .task import send_ticket_info_to_teams


@receiver(post_save, sender=Ticket)
def post_save_ticket(sender, instance, created, **kwargs):
    """
    Signal to handle actions after a Ticket is saved.
    If the ticket is newly created, send its information to Teams.
    """
    send_ticket_info_to_teams.delay(instance.id)
