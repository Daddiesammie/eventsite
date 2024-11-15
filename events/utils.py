import requests
from django.conf import settings
from django.urls import reverse
from django.core.mail import send_mail
from django.template.loader import render_to_string
import qrcode
import io
import base64

# Existing payment functions
def initialize_payment(email, amount, reference, request, purchase_id):
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    callback_url = request.build_absolute_uri(
        reverse('events:purchase_confirmation', kwargs={'purchase_id': purchase_id})
    )
    
    data = {
        "email": email,
        "amount": int(amount * 100),
        "reference": reference,
        "callback_url": callback_url
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def verify_payment(reference):
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"
    }
    response = requests.get(url, headers=headers)
    return response.json()

# New email function
import logging
logger = logging.getLogger(__name__)

def send_ticket_email(purchase):
    logger.info(f"Starting email generation for purchase {purchase.id}")
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(f"Ticket ID: {purchase.id}\nEvent: {purchase.ticket.event.title}")
    qr.make(fit=True)
    qr_image = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    qr_image.save(buffer, format='PNG')
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    context = {
        'purchase': purchase,
        'qr_code': qr_code_base64,
        'event': purchase.ticket.event
    }
    
    email_html = render_to_string('events/email/ticket_email.html', context)
    
    logger.info(f"Sending email to {purchase.user.email}")
    send_mail(
        subject=f'Your Tickets for {purchase.ticket.event.title}',
        message='Your tickets are attached',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[purchase.user.email],
        html_message=email_html
    )
    logger.info(f"Email sent successfully for purchase {purchase.id}")
