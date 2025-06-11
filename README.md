# turn-python

## Documentation Links
- [Turn API documentation](https://whatsapp.turn.io/docs/index.html)
- [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)

## Usage

1. Get an API token from [Turn](https://app.turn.io/) (currently only tokens are supported, not username / passwords)

1. Add this as an environment variable, or pass in to the turn client

    ``` bash
    $ export TURN_AUTH_TOKEN={your token}
    ```

1. Usage

    ``` python
    from turn import TurnClient
    
    turn_client = TurnClient(token={optionally add your token here})

    # Get a user's whatsapp id
    wa_id = turn_client.contacts.get_whatsapp_id('123456')

    # Send a message
    turn_client.messages.send_text(wa_id, 'Hello')
   
    # Send a media file
    with open("example.jpg", "rb") as file:
        turn_client.messages.send_media(
            whatsapp_id=wa_id,
            file=file,
            content_type="image/jpeg",
            media_type="image",
            caption="Here’s an image"
        )
    ```
