import logging
import json
from typing import Text, List, Any, Dict, Optional, Callable, Awaitable

from rasa.core.channels.channel import InputChannel, OutputChannel, UserMessage
from sanic import Blueprint, response
from sanic.request import Request
from sanic.response import HTTPResponse
import requests

logger = logging.getLogger(__name__)

class WhatsAppConnector(InputChannel):
    """A custom connector for WhatsApp Cloud API."""

    @classmethod
    def name(cls) -> Text:
        return "whatsapp"

    def __init__(
        self,
        verify_token: Text,
        app_secret: Text,
        page_access_token: Text,
        phone_number_id: Text,
    ) -> None:
        self.verify_token = verify_token
        self.app_secret = app_secret
        self.page_access_token = page_access_token
        self.phone_number_id = phone_number_id

    @classmethod
    def from_credentials(cls, credentials: Optional[Dict[Text, Any]]) -> "WhatsAppConnector":
        """Create WhatsAppConnector from credentials."""
        if not credentials:
            raise ValueError("WhatsAppConnector requires credentials")
        
        return cls(
            verify_token=credentials.get("verify_token"),
            app_secret=credentials.get("app_secret"),
            page_access_token=credentials.get("page_access_token"),
            phone_number_id=credentials.get("phone_number_id"),
        )

    def blueprint(
        self, on_new_message: Callable[[UserMessage], Awaitable[Any]]
    ) -> Blueprint:
        custom_webhook = Blueprint("custom_webhook_{}".format(type(self).__name__))

        @custom_webhook.route("/", methods=["GET"])
        async def health(request: Request) -> HTTPResponse:
            return response.json({"status": "ok"})

        @custom_webhook.route("/webhook", methods=["GET"])
        async def verify(request: Request) -> HTTPResponse:
            """Verification for Facebook/WhatsApp webhook."""
            if request.args.get("hub.mode") == "subscribe" and request.args.get(
                "hub.verify_token"
            ) == self.verify_token:
                return response.text(request.args.get("hub.challenge"))
            return response.text("Error, wrong validation token", status=403)

        @custom_webhook.route("/webhook", methods=["POST"])
        async def receive(request: Request) -> HTTPResponse:
            """Receive messages from WhatsApp."""
            payload = request.json
            
            # Log incoming payload for debugging
            logger.debug(f"Received payload: {json.dumps(payload, indent=2)}")

            if not payload:
                return response.text("No payload", status=400)

            # Check if this is a WhatsApp status update or message
            if "entry" in payload:
                for entry in payload["entry"]:
                    for change in entry.get("changes", []):
                        value = change.get("value", {})
                        
                        if "messages" in value:
                            for message in value["messages"]:
                                sender_id = message.get("from")
                                text = ""
                                
                                if message.get("type") == "text":
                                    text = message["text"]["body"]
                                elif message.get("type") == "button":
                                    text = message["button"]["text"]
                                elif message.get("type") == "interactive":
                                    if message["interactive"]["type"] == "button_reply":
                                        text = message["interactive"]["button_reply"]["title"]
                                    elif message["interactive"]["type"] == "list_reply":
                                        text = message["interactive"]["list_reply"]["title"]
                                
                                if sender_id and text:
                                    out_channel = WhatsAppOutput(
                                        self.page_access_token,
                                        self.phone_number_id
                                    )
                                    
                                    await on_new_message(
                                        UserMessage(
                                            text,
                                            out_channel,
                                            sender_id,
                                            input_channel=self.name(),
                                            metadata={"name": value.get("contacts", [{}])[0].get("profile", {}).get("name")}
                                        )
                                    )

            return response.text("EVENT_RECEIVED")

        return custom_webhook


class WhatsAppOutput(OutputChannel):
    """Output channel for WhatsApp Cloud API."""

    def __init__(self, page_access_token: Text, phone_number_id: Text) -> None:
        self.page_access_token = page_access_token
        self.phone_number_id = phone_number_id
        self.api_url = f"https://graph.facebook.com/v17.0/{self.phone_number_id}/messages"

    async def send_text_message(
        self, recipient_id: Text, text: Text, **kwargs: Any
    ) -> None:
        """Send a text message."""
        headers = {
            "Authorization": f"Bearer {self.page_access_token}",
            "Content-Type": "application/json",
        }
        
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_id,
            "type": "text",
            "text": {"body": text}
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    async def send_custom_json(
        self, recipient_id: Text, json_message: Dict[Text, Any], **kwargs: Any
    ) -> None:
        """Send a custom JSON payload (for buttons, lists, etc)."""
        headers = {
            "Authorization": f"Bearer {self.page_access_token}",
            "Content-Type": "application/json",
        }
        
        # Ensure mandatory fields
        json_message["messaging_product"] = "whatsapp"
        json_message["to"] = recipient_id
        
        try:
            response = requests.post(self.api_url, headers=headers, json=json_message)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to send custom json: {e}")
