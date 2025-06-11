from io import BytesIO

import responses
from mock import patch

from turn import TurnClient
from turn.request_types import TurnRequest


class MockResponse:
    def __init__(self, json_data, status_code):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        return self._json


@responses.activate
def test_send_message_success():
    expected_message_id = "gBEGkYiEB1VXAglK1ZEqA1YKPrU"
    responses.add(
        responses.Response(
            method="POST",
            url=f"{TurnRequest.base_url}messages",
            json={"messages": [{"id": expected_message_id}]},
        )
    )
    client = TurnClient(token="123")
    message_id = client.messages.send_text(whatsapp_id="123321", text="Hi there")
    assert message_id == expected_message_id


@responses.activate
def test_get_media():
    media_id = "123"
    responses.add(
        responses.Response(
            method="GET",
            url=f"{TurnRequest.base_url}media/{media_id}",
            body=b"some-binary",
        )
    )
    client = TurnClient(token="123")
    response = client.media.get_media(media_id=media_id)
    assert response.content.decode() == "some-binary"


def test_upload_media_overrides_content_type():
    content = b"x01"
    with patch("turn.request_types.requests.request") as request_mock:
        client = TurnClient(token="123")
        client.media.upload_media(media_content=content, content_type="audio/ogg")
        call_args = list(request_mock.call_args_list[0])
        headers = call_args[1]["headers"]
        data = call_args[1]["data"]
        assert headers["Content-Type"] == "audio/ogg"
        assert data == content


@patch("turn.request_types.requests.request")
def test_send_media_success(mock_request):
    mock_request.side_effect = [
        MockResponse({"media": [{"id": "mock-media-id"}]}, 200),
        MockResponse({"messages": [{"id": "mock-message-id"}]}, 200),
    ]

    client = TurnClient(token="dummy-token")
    fake_file = BytesIO(b"fake-binary-data")

    result = client.messages.send_media(
        whatsapp_id="123456",
        file=fake_file,
        content_type="image/jpeg",
        media_type="image",
        caption="Hello world!",
    )
    assert result == "mock-message-id"
    assert mock_request.call_count == 2
