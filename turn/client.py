import os
from .request_types import TurnContacts, TurnMessages, TurnMedia

class TurnClient:
    def __init__(self, token=None):
        token = token or os.environ.get("TURN_AUTH_TOKEN")
        self.contacts = TurnContacts(token)
        self.messages = TurnMessages(token)
        self.media = TurnMedia(token)