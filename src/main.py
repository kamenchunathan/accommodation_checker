import os

from twilio.rest import Client

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
to_phone_number = os.environ['TO_PHONE_NUMBER']
from_phone_number = os.environ['FROM_PHONE_NUMBER']

client = Client(account_sid, auth_token)

message = client.messages.create(
    body="IT WOOOOOOORKSS!!!!!",
    from_=from_phone_number,
    to='+254705493474'
)

print(message.sid)
