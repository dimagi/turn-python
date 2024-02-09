from turn import TurnClient, TurnRequest
import responses

@responses.activate
def test_send_message_success():
    expected_message_id = "gBEGkYiEB1VXAglK1ZEqA1YKPrU"
    responses.add(
        responses.Response(
            method="POST",
            url=f"{TurnRequest.base_url}messages",
            json={"messages": [{ "id": expected_message_id}]},
        )
    )
    client = TurnClient(token="123")
    message_id = client.messages.send_text(whatsapp_id="123321", text="Hi there")
    assert message_id == expected_message_id

@responses.activate
def test_get_media():
    media_id="123"
    responses.add(
        responses.Response(
            method="GET",
            url=f"{TurnRequest.base_url}media/{media_id}",
            body=b'some-binary',
        )
    )
    client = TurnClient(token="123")
    response = client.media.get_media(media_id=media_id)
    assert response.content.decode() == "some-binary"