# services/email_service.py
from flask import current_app, render_template_string
from flask_mail import Message
from datetime import datetime
from models import db, EmailHistory
import os

def send_email(to_email, subject, template_name, context=None):
    """
    Send email using Flask-Mail with Jinja2 template
    """
    if context is None:
        context = {}

    try:
        # Load template from templates/email_templates/
        template_path = os.path.join(
            current_app.root_path, 
            'templates', 
            'email_templates', 
            template_name
        )

        if not os.path.exists(template_path):
            # Fallback to simple text if template missing
            html_body = f"<p>{subject}</p><p>{context.get('message', 'No content')}</p>"
        else:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()

            # Render template with context
            html_body = render_template_string(template_content, **context)

        # Create message
        msg = Message(
            subject=subject,
            recipients=[to_email],
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            html=html_body
        )

        # Send email
        current_app.mail.send(msg)

        # Log to database (optional - for tracking)
        # You can extend this to link with Contact or Order if needed

        print(f"✅ Email sent successfully to {to_email} | Subject: {subject}")
        return True, "Email sent successfully"

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Email sending failed: {error_msg}")
        return False, f"Failed to send email: {error_msg}"


# Specific helper functions for common email types

def send_welcome_email(user):
    """Send welcome email after registration"""
    context = {
        'full_name': user.full_name or user.email.split('@')[0],
        'our_company': current_app.config.get('COMPANY_NAME', 'Book Haven'),
        'date': datetime.now().strftime("%B %d, %Y")
    }
    return send_email(
        to_email=user.email,
        subject=f"Welcome to {current_app.config.get('COMPANY_NAME', 'Book Haven')}!",
        template_name="welcome_email.html",
        context=context
    )


def send_order_confirmation(order, user):
    """Send order confirmation after successful payment"""
    context = {
        'full_name': user.full_name,
        'order_id': order.id,
        'total_amount': order.total_amount,
        'our_company': current_app.config.get('COMPANY_NAME', 'Book Haven'),
        'date': datetime.now().strftime("%B %d, %Y")
    }
    return send_email(
        to_email=user.email,
        subject=f"Order Confirmation #{order.id} - Book Haven",
        template_name="order_confirmation.html",
        context=context
    )


def send_pdf_download_link(user, book, download_link):
    """Send secure one-time PDF download link"""
    context = {
        'full_name': user.full_name or user.email.split('@')[0],
        'book_title': book.title,
        'download_url': f"{current_app.config.get('BASE_URL', 'http://127.0.0.1:5000')}/downloads/pdf/{download_link.token}",
        'expires_at': download_link.expires_at.strftime("%B %d, %Y at %H:%M"),
        'our_company': current_app.config.get('COMPANY_NAME', 'Book Haven')
    }
    return send_email(
        to_email=user.email,
        subject=f"Your PDF Download Link - {book.title}",
        template_name="pdf_download_link.html",
        context=context
    )


def send_custom_email(to_email, subject, message):
    """Send completely custom email"""
    context = {
        'message': message,
        'our_company': current_app.config.get('COMPANY_NAME', 'Book Haven')
    }
    return send_email(
        to_email=to_email,
        subject=subject,
        template_name="custom_email.html",
        context=context
    )