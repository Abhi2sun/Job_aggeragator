import os
from twilio.rest import Client
import http.client
import urllib
import smtplib
from email.mime.text import MIMEText
from typing import Dict


DO_TEXT = False
DO_PUSH = True
DO_EMAIL = True


class MessagingAgent:
    def __init__(self):
        """
        Initialize the MessagingAgent with support for SMS, push notifications, and email.
        """
        self.log("Messaging Agent is initializing")

        # Twilio setup for SMS
        if DO_TEXT:
            account_sid = os.getenv('TWILIO_ACCOUNT_SID', 'your-sid-if-not-using-env')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN', 'your-auth-if-not-using-env')
            self.me_from = os.getenv('TWILIO_FROM', 'your-phone-number-if-not-using-env')
            self.me_to = os.getenv('MY_PHONE_NUMBER', 'your-phone-number-if-not-using-env')
            self.client = Client(account_sid, auth_token)
            self.log("Twilio SMS initialized")

        # Pushover setup for push notifications
        if DO_PUSH:
            self.pushover_user = os.getenv('PUSHOVER_USER', 'your-pushover-user-if-not-using-env')
            self.pushover_token = os.getenv('PUSHOVER_TOKEN', 'your-pushover-token-if-not-using-env')
            self.log("Pushover notifications initialized")

        # Email setup
        if DO_EMAIL:
            self.smtp_server = os.getenv('SMTP_SERVER', 'your-smtp-server')
            self.smtp_port = int(os.getenv('SMTP_PORT', 587))
            self.email_user = os.getenv('EMAIL_USER', 'your-email')
            self.email_password = os.getenv('EMAIL_PASSWORD', 'your-email-password')
            self.email_to = os.getenv('EMAIL_TO', 'recipient-email')
            self.log("Email notifications initialized")

    def log(self, message: str):
        """
        Log a message to the console.
        """
        print(f"[LOG]: {message}")

    def send_sms(self, text: str):
        """
        Send an SMS message using Twilio.
        """
        self.log("Sending SMS notification")
        self.client.messages.create(
            from_=self.me_from,
            body=text,
            to=self.me_to
        )

    def send_push(self, text: str):
        """
        Send a push notification using Pushover.
        """
        self.log("Sending push notification")
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
                     urllib.parse.urlencode({
                         "token": self.pushover_token,
                         "user": self.pushover_user,
                         "message": text,
                         "sound": "cashregister"
                     }), {"Content-type": "application/x-www-form-urlencoded"})
        conn.getresponse()

    def send_email(self, subject: str, body: str):
        """
        Send an email notification.
        """
        self.log("Sending email notification")
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = self.email_user
        msg['To'] = self.email_to

        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.email_user, self.email_password)
            server.sendmail(self.email_user, [self.email_to], msg.as_string())

    def alert(self, preparation_plan: Dict):
        """
        Notify the user about the generated interview preparation plan.
        :param preparation_plan: A dictionary containing the preparation plan.
        """
        # Generate the alert content
        job_title = preparation_plan.get('job_title', 'Unknown Job Title')
        topics = ", ".join(preparation_plan.get('preparation_strategy', {}).get('topics_to_study', []))
        resources = ", ".join(preparation_plan.get('preparation_strategy', {}).get('resources', []))
        technical_questions = "\n".join([f"- {q['question']}" for q in preparation_plan.get('technical_questions', [])])
        behavioral_questions = "\n".join([f"- {q['question']}" for q in preparation_plan.get('behavioral_questions', [])])

        # Create the message content
        message = f"""
        Your Interview Preparation Plan:

        Job Title: {job_title}

        Topics to Study:
        {topics}

        Recommended Resources:
        {resources}

        Technical Questions:
        {technical_questions}

        Behavioral Questions:
        {behavioral_questions}
        """

        # Send notifications
        if DO_TEXT:
            self.send_sms(message[:160])  # SMS message should be short
        if DO_PUSH:
            self.send_push(f"Interview Plan for {job_title}: {topics}")
        if DO_EMAIL:
            self.send_email(f"Interview Preparation Plan for {job_title}", message)

        self.log("All notifications sent")
