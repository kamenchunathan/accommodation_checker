import os

from twilio.rest import Client

from logger import log_message


class TwilioLiveSMSBackend:
    """
    An SMS backend to handle sending messages from a preconfigured twilio number to a recipient specified bu calling
    the send message method
    """

    def __init__(self):
        account_sid = os.environ['TWILIO_ACCOUNT_SID']
        auth_token = os.environ['TWILIO_AUTH_TOKEN']
        self.client = Client(account_sid, auth_token)
        self.sender_phone_number = from_phone_number = os.environ['FROM_PHONE_NUMBER']

    @log_message
    def send_message(self, recipient_phone_no, message_body):
        message = self.client.messages.create(
            body=message_body,
            from_=self.sender_phone_number,
            to=recipient_phone_no
        )
        return message


class ConsoleBackend:
    """A test message provider that prints messages to the console for testing purposes"""

    def send_message(self, recipient_phone_no, message_body):
        print('to: {to}, body:{body}'.format(body=message_body, to=recipient_phone_no))


class Messenger:
    """Responsible for sending messages using a selected backend"""

    def __init__(self, backend=None):
        """
        Defaults the backend to console backend if unspecified
        :param backend:
        """
        self.message_backend = backend if backend else ConsoleBackend()

    def send_message(self, *args, **kwargs):
        return self.message_backend.send_message(*args, **kwargs)
