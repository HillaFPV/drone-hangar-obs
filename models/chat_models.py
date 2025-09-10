from typing import Optional, List

from pydantic import BaseModel

class MessageEx(BaseModel):
    id: str
    txt: str
    url: str

class ChatAuthor(BaseModel):
    name: str
    imageUrl: str
    isVerified: bool
    isChatOwner: bool
    isChatSponsor: bool
    isChatModerator: bool

class ChatMessage(BaseModel):
    type: str
    id: str
    datetime: str
    author: ChatAuthor
    message: str
    amountValue: float
    amountString: str
    currency: str
    message: str
    messageEx: Optional[List[str | MessageEx]]

class BatteryMessage(BaseModel):
    volts: float

class TextMessage(BaseModel):
    text: str