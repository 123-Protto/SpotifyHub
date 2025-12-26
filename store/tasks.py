# rural_sports/store/tasks.py
from rural_sports.rural_sports.celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Order

@shared_task(bind=True)
def send_order_confirmation_email_task(self, order_id):
    """
    Sends an order confirmation email to the user.
    This task is designed to be executed asynchronously by a Celery worker.

    Args:
        order_id (int): The ID of the Order object to send the email for.

    Raises:
        Order.DoesNotExist: If the order with the given ID is not found.
    """
    try:
        order = Order.objects.get(id=order_id)
        
        # You can use an HTML template for a more professional-looking email
        html_message = render_to_string('store/email/order_confirmation.html', {'order': order})
        plain_message = strip_tags(html_message)
        
        subject = f"Order #{order.id} Confirmation"
        email_from = settings.DEFAULT_FROM_EMAIL
        recipient_list = [order.user.email]
        
        send_mail(
            subject,
            plain_message,
            email_from,
            recipient_list,
            html_message=html_message,
        )
        
    except Order.DoesNotExist:
        # Log this error instead of failing silently
        print(f"Order with ID {order_id} not found. Email not sent.")
        # You can also retry the task if it's a temporary database issue
        # self.retry(exc=e, countdown=60)
    except Exception as e:
        # Handle other potential errors, like network issues or mail server problems
        print(f"Failed to send email for order {order_id}: {e}")
        # self.retry(exc=e, countdown=60)