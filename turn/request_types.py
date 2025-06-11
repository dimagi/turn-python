import os
import requests
import json

from turn.exceptions import (
    WhatsAppContactNotFoundError,
    WhatsAppBadRequestError,
    WhatsAppAuthenticationError,
    WhatsAppUnknownError,
    WhatsAppTemplateNotFoundError,
)


class TurnRequest:
    base_url = "https://whatsapp.turn.io/v1/"
    endpoint_name = None

    def __init__(self, token):
        self.token = token

    def headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    @property
    def url(self):
        return f"{self.base_url}{self.endpoint_name}"

    def _make_request(self, method, url, data=None, extra_headers={}):
        return requests.request(
            method,
            url,
            headers=self.headers() | extra_headers,
            data=data,
        )

    def _post(self, data=None):
        return self._make_request(
            method="POST",
            url=self.url,
            data=json.dumps(data) if data is not None else None,
        )

    def _get(self, resource):
        return self._make_request(
            method="GET",
            url=f"{self.url}/{resource}",
        )

    def get_error(self, response):
        try:
            return response.json()["errors"][0]
        except (KeyError, IndexError):
            return None


class TurnContacts(TurnRequest):
    endpoint_name = "contacts"

    def get_whatsapp_id(self, number):
        response = self._post(data={"blocking": "wait", "contacts": [number]})
        status = response.status_code

        if status == requests.codes.not_found:
            # WhatsApp user contact not found

            error = self.get_error(response)
            raise WhatsAppContactNotFoundError(error["details"])
        elif "errors" in response.json():
            # If we didn't more accurately catch anything that errored, but
            # the request has errors, just raise a more generic exception
            # with whatever information was received from Turn

            error = self.get_error(response)
            raise WhatsAppUnknownError(error["details"])

        try:
            if response.json()["contacts"][0]["input"] == number:
                return response.json()["contacts"][0]["wa_id"]
            else:
                raise WhatsAppContactNotFoundError
        except KeyError:
            raise WhatsAppContactNotFoundError


class TurnMessages(TurnRequest):
    endpoint_name = "messages"

    def send_text(self, whatsapp_id, text):
        payload = {
            "to": whatsapp_id,
            "recipient_type": "individual",
            "type": "text",
            "text": {"body": text},
        }
        return self._send_message(payload)

    def send_media(self, whatsapp_id, file, content_type, media_type, caption=None):
        """
        Send media (image/video/document/audio) to a WhatsApp user.
        Uploads media first, then sends it using the correct message type.
        """
        media_id = TurnMedia(self.token).upload_media(file, content_type)

        payload = {
            "to": whatsapp_id,
            "recipient_type": "individual",
            "type": media_type,
            media_type: {"id": media_id},
        }

        if caption and media_type in ["image", "video", "document"]:
            payload[media_type]["caption"] = caption

        return self._send_message(payload)

    def _send_message(self, payload):
        response = self._post(data=payload)
        status = response.status_code

        # Check known possible errors, given the little information we receive
        # from Turn when something goes wrong.
        if status == requests.codes.not_found:
            # WhatsApp user contact not found

            error = self.get_error(response)
            raise WhatsAppContactNotFoundError(error["details"])
        elif status == requests.codes.bad_request:
            # Poorly formed text param will cause a bad request

            error = self.get_error(response)
            raise WhatsAppBadRequestError(error["details"])
        elif status == requests.codes.forbidden:
            # Caused by bad token
            # No JSON response on this, no additional info to pass upwards

            raise WhatsAppAuthenticationError
        elif "errors" in response.json():
            # If we didn't more accurately catch anything that errored, but
            # the request has errors, just raise a more generic exception
            # with whatever information was received from Turn

            error = self.get_error(response)
            raise WhatsAppUnknownError(error["details"])

        # TODO handle malformed response data
        return response.json()["messages"][0]["id"]

    def send_templated_message(
        self, whatsapp_id, namespace, name, language, template_params=[]
    ):
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
        Too few and message is sent without filling in template values, too many
        and only the number that are required are used when sending message.
        """

        localizable_params = [{"default": param} for param in template_params]

        response = self._post(
            data={
                "to": whatsapp_id,
                "type": "hsm",
                "hsm": {
                    "namespace": namespace,
                    "element_name": name,
                    "language": {"code": language, "policy": "deterministic"},
                    "localizable_params": localizable_params,
                },
            }
        )
        status = response.status_code

        # Check known possible errors, given the little information we receive
        # from Turn when something goes wrong.
        if status == requests.codes.not_found:
            error = self.get_error(response)

            # For templates, not found can mean either a template or user,
            # this is distinguished by the error code received

            if error["code"] == 1006:
                # 1006 is WhatsApp user contact not found
                raise WhatsAppContactNotFoundError(error["details"])
            elif error["code"] == -1:
                # -1 is returned when template namespace or element name
                # are not found
                raise WhatsAppTemplateNotFoundError(error["details"])
            else:
                raise WhatsAppUnknownError(error["details"])
        elif status == requests.codes.forbidden:
            # Caused by bad token
            # No JSON response on this, no additional info to pass upwards

            raise WhatsAppAuthenticationError
        elif "errors" in response.json():
            # If we didn't more accurately catch anything that errored, but
            # the request has errors, just raise a more generic exception
            # with whatever information was received from Turn

            error = self.get_error(response)
            raise WhatsAppUnknownError(error["details"])

        # TODO handle malformed response data
        return response.json()["messages"][0]["id"]


class TurnMedia(TurnRequest):
    endpoint_name = "media"

    def get_media(self, media_id):
        return self._get(resource=media_id)

    def upload_media(self, media_content, content_type):
        response = self._make_request(
            method="POST",
            url=self.url,
            data=media_content,
            extra_headers={"Content-Type": content_type},
        )

        return response.json()["media"][0]["id"]


class TurnBusinessManagementRequest:
    base_url = "https://whatsapp.turn.io/v3.3"
    endpoint_name = None

    def __init__(self, business_id, token):
        self.business_id = business_id
        self.token = token

    def params(self):
        return {"access_token": self.token}

    def do_request(self, method, data=None):
        return requests.request(
            method,
            f"{self.base_url}/{self.business_id}/{self.endpoint_name}",
            # Only send data if passed in, but if it's a query that
            # needs the data field, then auth has to be in here and not params
            data=data if data is not None else None,
            params=self.params() if data is None else None,
        )


class TurnMessageTemplates(TurnBusinessManagementRequest):
    endpoint_name = "message_templates"

    def get_message_templates(self):
        response = self.do_request(method="GET")

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

        # NOTE: Turn only supports the body component, and doesn't allow
        # header or footer components to be sent.
        components = [{"type": "BODY", "text": body}]

        response = self.do_request(
            method="POST",
            data={
                "name": name,
                "category": category,
                "components": json.dumps(components),
                "access_token": self.token,
                "language": "en_US",
            },
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
