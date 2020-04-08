import os
import requests
import json

from turn.exceptions import WhatsAppContactNotFound


class TurnRequest:
    base_url = "https://whatsapp.turn.io/v1/"
    endpoint_name = None
    method = "POST"

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
            data=json.dumps(data) if data is not None else None,
        )


class TurnContacts(TurnRequest):
    endpoint_name = "contacts"

    def get_whatsapp_id(self, number):
        response = self.do_request(data={"blocking": "wait", "contacts": [number]})
        try:
            if response.json()["contacts"][0]["input"] == number:
                return response.json()["contacts"][0]["wa_id"]
            else:
                raise WhatsAppContactNotFound
        except KeyError:
            raise WhatsAppContactNotFound


class TurnMessages(TurnRequest):
    endpoint_name = "messages"

    def send_text(self, whatsapp_id, text):
        response = self.do_request(
            data={
                "to": whatsapp_id,
                "recipient_type": "individual",
                "type": "text",
                "text": {"body": text}
            }
        )
        if response.status_code == requests.codes.ok:
            return response.json()["messages"][0]["id"]
        elif response.status_code == requests.codes.not_found:
            raise WhatsAppContactNotFound


class TurnClient:
    def __init__(self, token=None):
        token = token or os.environ.get("TURN_AUTH_TOKEN")
        self.contacts = TurnContacts(token)
        self.messages = TurnMessages(token)


class TurnBusinessManagementRequest:
    base_url = "https://whatsapp.turn.io/v3.3/"
    endpoint_name = None
    method = "GET"

    def __init__(self, business_id, token):
        self.business_id = business_id
        self.token = token

    def params(self):
        return {
            "access_token": self.token
        }

    def do_request(self):
        return requests.request(
            self.method,
            f"{self.base_url}{self.business_id}/{self.endpoint_name}",
            params=self.params()
        )


class TurnMessageTemplates(TurnBusinessManagementRequest):
    endpoint_name = "message_templates"

    # TODO: is there a way to get business_id from other data?
    def get_message_templates(self):
        response = self.do_request()
        print(response.json())


class TurnBusinessManagementClient:
    def __init__(self, business_id=None, token=None):
        business_id = business_id or os.environ.get("TURN_BUSINESS_ID")
        token = token or os.environ.get("TURN_BUSINESS_AUTH_TOKEN")
        self.message_templates = TurnMessageTemplates(business_id, token)
