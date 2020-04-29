class TurnException(Exception):
    pass


class WhatsAppContactNotFoundError(TurnException):
    pass


class WhatsAppBadRequestError(TurnException):
    pass


class WhatsAppAuthenticationError(TurnException):
    pass


class WhatsAppUnknownError(TurnException):
    pass


class WhatsAppTemplateNotFoundError(TurnException):
    pass
