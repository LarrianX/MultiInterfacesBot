import os
from typing import Any, Optional

import telethon
from telethon import TelegramClient
from telethon.events import NewMessage

from .types import *
from ..base import Interface, BaseInterface
from ..base import types as base

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

PLATFORM = "Telegram"


def encode(word: str, id: int, encoding="utf-8") -> int:
    byte_data = f"{word} {id}".encode(encoding=encoding)
    return int.from_bytes(byte_data, byteorder="big")


def decode(n: int, encoding="utf-8") -> tuple[str, int]:
    byte_length = (n.bit_length() + 7) // 8  # Corrected byte length calculation
    byte_data = n.to_bytes(byte_length, byteorder="big")
    values = byte_data.decode(encoding=encoding).split(" ")
    return values[0], int(values[1])


class TelegramInterface(Interface):
    def __init__(self, base_interface: BaseInterface,
                 api_id: int = API_ID,
                 api_hash: str = API_HASH,
                 bot_token: str = BOT_TOKEN,
                 session_name: str = "main"):
        super().__init__(base_interface)
        self.api_id = api_id
        self.api_hash = api_hash
        self.bot_token = bot_token
        self.client = TelegramClient(
            session_name,
            self.api_id,
            self.api_hash,
        ).start(bot_token=self.bot_token)
        self.base_interface = base_interface
        self.buffer: Any = None

        # Добавляем обработчик сообщений
        self.client.add_event_handler(self._handle_message, NewMessage())

    async def _handle_message(self, event: NewMessage.Event):
        # Преобразуем сообщение в объект Entity
        entity: TelegramMessage = await self.transform(event.message)  # type: ignore

        # Вызываем обработчик сообщения из base_interface
        await self.base_interface.message_handler(entity)

    async def transform(self, tl: telethon.types.TLObject) -> base.Entity:
        if isinstance(tl, telethon.types.PeerUser) or isinstance(tl, telethon.types.User):
            return await TelegramUser.from_tl(tl, caller=self)

        elif isinstance(tl, telethon.types.Message):
            return await TelegramMessage.from_tl(tl, caller=self)

        elif isinstance(tl, telethon.types.Document):
            return await TelegramDocument.from_tl(tl, caller=self)

        elif isinstance(tl, telethon.types.InputStickerSetID):
            return await TelegramStickerSet.from_tl(tl, caller=self)

        elif isinstance(tl, telethon.types.GeoPoint):
            return await TelegramGeoPoint.from_tl(tl, caller=self)

        else:
            raise ValueError(f"Unsupported TLObject type: {type(tl)}")

    async def get_entity(self, n: int | TelegramMessage) -> Optional[base.Entity]:
        tl_object = None
        if isinstance(n, int):
            tl_object = await self.client.get_entity(n)
        elif isinstance(n, TelegramMessage):
            tl_object = await self.client.get_messages(n.from_user.id, ids=n.id)

        if tl_object:
            return await self.transform(tl_object)

    async def send_message(self, id: int, text: str, attachments: list[base.Media] = None) -> base.Entity:
        tl_object = await self.client.send_message(id, text)
        return await self.transform(tl_object)

    async def start(self):
        print("Клиент запущен.")
        await self.send_message(1667209703, "Бот запущен.")
        await self.client.run_until_disconnected()
