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
    
    # Get a user's whatsapp id
    TurnClient(token={optionally add your token here}).contacts.get_whatsapp_id('123456')
    ```
