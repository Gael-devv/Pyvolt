from __future__ import annotations

from typing import Dict, List, Optional, TYPE_CHECKING, Any, Tuple, Union

if TYPE_CHECKING:
    from aiohttp import ClientResponse, ClientWebSocketResponse

    try:
        from requests import Response

        _ResponseType = Union[ClientResponse, Response]
    except ModuleNotFoundError:
        _ResponseType = ClientResponse

__all__ = (
    "RevoltException",
    "HTTPException",
    "Forbidden",
    "NotFound",
    "RevoltServerError"
)


class RevoltException(Exception):
    """Base exception class for pyvolt

    Ideally speaking, this could be caught to handle any exceptions raised from this library.
    """


def _flatten_error_dict(d: Dict[str, Any], key: str = '') -> Dict[str, str]:
    items: List[Tuple[str, str]] = []
    for k, v in d.items():
        new_key = key + '.' + k if key else k

        if isinstance(v, dict):
            try:
                _errors: List[Dict[str, Any]] = v['_errors']
            except KeyError:
                items.extend(_flatten_error_dict(v, new_key).items())
            else:
                items.append((new_key, ' '.join(x.get('message', '') for x in _errors)))
        else:
            items.append((new_key, v))

    return dict(items)


class HTTPException(RevoltException):
    """Exception that's raised when an HTTP request operation fails.

    Attributes
    ------------
    response: :class:`aiohttp.ClientResponse`
        The response of the failed HTTP request. This is an
        instance of :class:`aiohttp.ClientResponse`. In some cases
        this could also be a :class:`requests.Response`.

    text: :class:`str`
        The text of the error. Could be an empty string.
    status: :class:`int`
        The status code of the HTTP request.
    """

    def __init__(self, response: _ResponseType, message: Optional[Union[str, Dict[str, Any]]]):
        self.response: _ResponseType = response
        self.status: int = response.status  # type: ignore

        self.text: str
        if isinstance(message, dict):
            base = message.get('message', '')
            errors = message.get('errors')
            if errors:
                errors = _flatten_error_dict(errors)
                helpful = '\n'.join('In %s: %s' % t for t in errors.items())
                self.text = base + '\n' + helpful
            else:
                self.text = base
        else:
            self.text = message or ''

        fmt = '{0.status} {0.reason}'
        if len(self.text):
            fmt += ': {1}'

        super().__init__(fmt.format(self.response, self.text))
        

class Forbidden(HTTPException):
    """Exception that's raised for when status code 403 occurs.

    Subclass of :exc:`HTTPException`
    """


class NotFound(HTTPException):
    """Exception that's raised for when status code 404 occurs.

    Subclass of :exc:`HTTPException`
    """
    
    
class RevoltServerError(HTTPException):
    """Exception that's raised for when a 500 range status code occurs.

    Subclass of :exc:`HTTPException`.
    """
    

class ClientException(RevoltException):
    """Exception that's raised when an operation in the :class:`Client` fails.

    These are usually for exceptions that happened due to user input.
    """


class LoginFailure(ClientException):
    """Exception that's raised when the :meth:`Client.login` function
    fails to log you in from improper credentials or some other misc.
    failure.
    """