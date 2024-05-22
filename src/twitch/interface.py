import requests
from requests import RequestException
from pydantic import (
    BaseModel,
    TypeAdapter,
    ValidationError,
)

from json import JSONDecodeError
from typing import (
    Any,
    Dict,
    List,
    Type,
    TypeVar,
    Optional,
)

from src.twitch.models import (
    TwitchEventSubscription,
    TwitchEventSubscriptionCondition,
    TwitchEventSubscriptionTransport,
)


class TwitchError(Exception):
    pass


T = TypeVar("T", bound=BaseModel)


class TwitchInterface:
    BASE_URL = "https://api.twitch.tv/helix"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        bearer_token: Optional[str] = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        if not bearer_token:
            bearer_token = self.get_client_credentials_token()

        self.bearer_token = bearer_token
        self.validate_token()

    def _send_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str] = None,
        payload: Dict[str, Any] = None,
        DataType: Type[T] = None,
    ) -> T:
        """
        Wrapper for sending a request and marshalling the response into some data type.
        """
        try:
            response = requests.request(method, url, headers=headers, json=payload)
            response.raise_for_status()
            response_json = response.json()
            if DataType == None:
                return response_json
            else:
                return TypeAdapter(DataType).validate_python(response_json["data"])
        except (RequestException, JSONDecodeError, ValidationError) as e:
            raise TwitchError from e

    def get_client_credentials_token(self) -> str:
        """
        Generate a bearer token (for account-only scope) using the client ID/secret pair.
        """
        url = "https://id.twitch.tv/oauth2/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }
        response = self._send_request("POST", url, payload=payload)
        return response["access_token"]

    def validate_token(self):
        """
        Validate the bearer token is still valid.
        """
        url = "https://id.twitch.tv/oauth2/validate"
        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        self._send_request("GET", url, headers=headers)

    def get_event_subscriptions(self) -> List[TwitchEventSubscription]:
        """
        Retrieve the current list of event subscriptions.
        """
        url = f"{self.BASE_URL}/eventsub/subscriptions"
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Client-Id": self.client_id,
        }
        return self._send_request(
            "GET",
            url,
            headers=headers,
            DataType=List[TwitchEventSubscription],
        )

    def create_event_subscription(
        self,
        subscription_type: str,
        version: str,
        condition: Dict[str, str],
        transport: Dict[str, str],
    ) -> List[TwitchEventSubscription]:
        """
        Generate a bearer token using the client ID/secret pair.
        """
        url = f"{self.BASE_URL}/eventsub/subscriptions"
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Client-Id": self.client_id,
        }
        transport["secret"] = f"bryti.{subscription_type}.{version}"
        payload = {
            "type": subscription_type,
            "version": version,
            "condition": condition,
            "transport": transport,
        }
        return self._send_request(
            "POST",
            url,
            headers=headers,
            payload=payload,
            DataType=List[TwitchEventSubscription],
        )

    def send_chat_message(
        self,
        broadcaster_id: str,
        sender_id: str,
        message: str,
        reply_message_id: Optional[str] = None,
    ):
        """
        Send a message in the broadcaster's chat.
        """
        url = f"{self.BASE_URL}/chat/messages"
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Client-Id": self.client_id,
        }
        payload = {
            "broadcaster_id": broadcaster_id,
            "sender_id": sender_id,
            "message": message,
            "reply_parent_message_id": reply_message_id,
        }
        return self._send_request(
            "POST",
            url,
            headers=headers,
            payload=payload,
        )
