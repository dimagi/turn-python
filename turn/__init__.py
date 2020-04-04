import os
import requests
import json

from turn.exceptions import WhatsAppContactNotFound


class TurnRequest:
    base_url = "https://whatsapp.turn.io/v1/"
    endpoint_name = None
    method = None

    def __init__(self, token):
        self.token = token

    def headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def do_request(self, data=None):
        return requests.request(
            self.method,
            f"{self.base_url}{self.endpoint_name}",
            headers=self.headers(),
            data=json.dumps(data),
        )


class TurnContacts(TurnRequest):
    endpoint_name = "contacts"
    method = "POST"

    def get_whatsapp_id(self, number):
        response = self.do_request(data={"blocking": "wait", "contacts": [number]})
        try:
            if response.json()["contacts"][0]["input"] == number:
                return response.json()["contacts"][0]["wa_id"]
            else:
                raise WhatsAppContactNotFound
        except KeyError:
            raise WhatsAppContactNotFound


class TurnClient:
    def __init__(self, token=None):
        token = token or os.environ.get("TURN_AUTH_TOKEN")
        self.contacts = TurnContacts(token)
