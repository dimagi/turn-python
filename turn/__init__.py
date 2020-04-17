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

    def send_templated_message(self, whatsapp_id, namespace, name, language, template_params=[]):
        """
        whatsapp_id: The whatsapp_id or whatsapp_group_id to send the message to.

        namespace: The template namespace for this template (TODO: should this be a stored value?).
        You can find this in in the API & Webhooks > Generate API username and password
        on Turn.
        TODO: Move this up to the client itself.

        name: The name of the template to send.

        langauge: Specify language code to use for this template.
        This must match exactly, so be careful with distinction of cases
        such as en vs en_US.

        template_params: A list of the strings to use for filling in the template.
        Currently does not support currency or date_time params.
        """

        localizable_params = [{"default": param} for param in template_params]

        response = self.do_request(
            data={
                "to": whatsapp_id,
                "type": "hsm",
                "hsm": {
                    "namespace": namespace,
                    "element_name": name,
                    "language": {
                        "code": language,
                        "policy": "deterministic",
                    },
                    "localizable_params": localizable_params
                }
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
    base_url = "https://whatsapp.turn.io/v3.3"
    endpoint_name = None
    method = None

    def __init__(self, business_id, token):
        self.business_id = business_id
        self.token = token

    def params(self):
        return {
            "access_token": self.token
        }

    def do_request(self, data=None):
        return requests.request(
            self.method,
            f"{self.base_url}/{self.business_id}/{self.endpoint_name}",
            # Only send data if passed in, but if it's a query that
            # needs the data field, then auth has to be in here and not params
            data=data if data is not None else None,
            params=self.params() if data is None else None
        )


class TurnMessageTemplates(TurnBusinessManagementRequest):
    endpoint_name = "message_templates"

    def get_message_templates(self):
        self.method = 'GET'
        response = self.do_request()

        if response.status_code == requests.codes.ok:
            return response.json()["data"]
        else:
            raise Exception(response.json())

    def create_message_template(self, name, category, body):
        """
        name: This field is used to identify the template when sending later.

        category: See docs for valid category options.
        https://whatsapp.turn.io/docs/index.html#message-template-api

        body: Text for body of the template.
        """
        self.method = 'POST'

        # NOTE: Turn only supports the body component, and doesn't allow
        # header or footer components to be sent.
        components = [{
            "type": "BODY",
            "text": body
        }]

        response = self.do_request(
            data={
                "name": name,
                "category": category,
                "components": json.dumps(components),
                "access_token": self.token,
                "language": "en_US"
            }
        )

        if response.status_code == requests.codes.created:
            return response.json()["id"]
        else:
            raise Exception(response.json())


class TurnBusinessManagementClient:
    def __init__(self, business_id=None, token=None):
        business_id = business_id or os.environ.get("TURN_BUSINESS_ID")
        token = token or os.environ.get("TURN_BUSINESS_AUTH_TOKEN")
        self.message_templates = TurnMessageTemplates(business_id, token)
