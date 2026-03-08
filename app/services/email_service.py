from flask_mail import Mail, Message
from flask import current_app, render_template
from threading import Thread
import os

mail = Mail()

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
            current_app.logger.info(f"Email sent to {msg.recipients}")
        except Exception as e:
            current_app.logger.error(f"Failed to send email: {str(e)}")

def send_email(subject, recipients, text_body, html_body, sender=None):
    msg = Message(
        subject=subject,
        recipients=recipients if isinstance(recipients, list) else [recipients],
        sender=sender or current_app.config['MAIL_DEFAULT_SENDER'],
        body=text_body,
        html=html_body
    )
    
    # Send asynchronously
    Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    ).start()

def send_password_reset_email(user, token):
    reset_url = f"https://{current_app.config['DOMAIN']}/auth/reset-password/{token}"
    
    send_email(
        subject="Reset Your ConstructFlix Password",
        recipients=user.email,
        text_body=render_template('email/reset_password.txt', user=user, reset_url=reset_url),
        html_body=render_template('email/reset_password.html', user=user, reset_url=reset_url)
    )

def send_welcome_email(user):
    verify_url = f"https://{current_app.config['DOMAIN']}/auth/verify-email/{user.verification_token}"
    
    send_email(
        subject="Welcome to ConstructFlix!",
        recipients=user.email,
        text_body=render_template('email/welcome.txt', user=user, verify_url=verify_url),
        html_body=render_template('email/welcome.html', user=user, verify_url=verify_url)
    )