from dataclasses import dataclass
from typing import Any
import datetime
import os

import base
from base import Entity, Media, User

import telethon
import telethon.tl.patched

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")


def encode(word: str, id_: int, encoding="utf-8") -> int:
    byte_data = f"{word} {id_}".encode(encoding=encoding)
    return int.from_bytes(byte_data, byteorder="big")


def decode(n: int, encoding="utf-8") -> tuple[str, int]:
    byte_length = (n.bit_length() + 7) // 8  # Corrected byte length calculation
    byte_data = n.to_bytes(byte_length, byteorder="big")
    values = byte_data.decode(encoding=encoding).split(" ")
    return values[0], int(values[1])


class TelegramMedia(base.Media):
    def __init__(self, id_: int, file_size: int, source: Any = None, caller: base.Interface = None):
        super().__init__(id_, file_size, source, caller)

    async def get(self):
        if isinstance(self.source, bytes):
            return self.source
        elif isinstance(self.source, telethon.types.TLObject) and self.caller:
            return await self.caller.client.download_media(self.source, file=bytes)


class TelegramPhoto(base.Photo, TelegramMedia):
    def __init__(self, id_: int, file_size: int, source: Any = None, caller: base.Interface = None):
        # TelegramMedia.__init__(self, id_, file_size, source, caller)
        super().__init__(id_, file_size, source, caller)
        # Я не совсем понимаю какой конструктор в этом случае вызывать. Кажется я уже погряз в этом ООП.
        # Буду исходить из base
        # Также в принципе сюда можно добавить разрешение картинки.


class TelegramVideo(base.Video, TelegramMedia):
    def __init__(self, id_: int, file_size: int, duration: int | float, source: Any = None, caller: base.Interface = None):
        super().__init__(id_, file_size, duration, source, caller)
        # Также в принципе сюда можно добавить разрешение видео.


class TelegramAudio(base.Audio, TelegramMedia):
    def __init__(self, id_: int, file_size: int, duration: int | float, source: Any = None, caller: base.Interface = None):
        super().__init__(id_, file_size, duration, source, caller)


class TelegramDocument(base.Document, TelegramMedia):
    def __init__(self, id_: int, file_size: int, file_name: str, source: Any = None, caller: base.Interface = None):
        super().__init__(id_, file_size, file_name, source, caller)


class TelegramUser(base.User):
    def __init__(self, id_: int, first_name: str, last_name: str, username: str, is_bot: bool,
                 source: Any = None, caller: object = None):
        super().__init__(id_, "Telegram", first_name, last_name, username, is_bot, source, caller)


class TelegramChat(base.Chat):
    def __init__(self, id_: int, type_: base.ChatType, title: str, members: list[User],
                 source: Any = None, caller: object = None):
        super().__init__(id_, type_, title, members, source, caller)


class TelegramMessage(base.Message):
    def __init__(self, id_: int, from_user: TelegramUser, chat: TelegramChat, date: datetime.datetime, text: str,
                 entities: list[TelegramMedia],
                 source: Any = None, caller: object = None):
        super().__init__(id_, from_user, chat, date, text, entities, source, caller)

    async def reply(self, text: str, entities: list[Media] = None):
        if isinstance(self.source, telethon.tl.patched.Message):
            await self.source.reply(text)

    async def answer(self, text: str, entities: list[Media] = None):
        if isinstance(self.source, telethon.tl.patched.Message):
            await self.source.respond(text)

    async def edit(self, text: str, entities: list[Media] = None):
        if isinstance(self.source, telethon.tl.patched.Message):
            await self.source.edit(text)


class TelegramInterface(base.Interface):
    def __init__(self, base_interface: base.BaseInterface,
                 api_id: int = API_ID,
                 api_hash: str = API_HASH,
                 bot_token: str = BOT_TOKEN,
                 session_name: str = "main"):
        super().__init__(base_interface)
        self.api_id = api_id
        self.api_hash = api_hash
        self.bot_token = bot_token
        self.client = telethon.TelegramClient(
            session_name,
            self.api_id,
            self.api_hash,
        )
        self.base_interface = base_interface
        self.buffer: Any = None

        # Добавляем обработчик сообщений
        self.client.add_event_handler(self._handle_message, telethon.events.NewMessage())

    async def _handle_message(self, event: telethon.events.NewMessage.Event):
        try:
            # Преобразуем сообщение в объект Entity
            entity: TelegramMessage = await self.transform(event.message)

            # Вызываем обработчик сообщения из base_interface
            await self.base_interface.message_handler(entity)
        except Exception as e:
            print(f"Error handling message: {e}")

    async def transform(self, object_: telethon.types.TLObject) -> Entity:
        if isinstance(object_, telethon.types.PeerUser):
            user: telethon.types.TLObject = await self.client.get_entity(object_.user_id)
            return await self.transform(user)

        elif isinstance(object_, telethon.types.User):
            return TelegramUser(
                object_.id,
                object_.first_name,
                object_.last_name,
                object_.username,
                object_.bot,
                source=object_,
                caller=self
            )

        elif isinstance(object_, telethon.types.Message):
            entities = []
            if object_.media:
                media = object_.media

                if isinstance(media, telethon.types.MessageMediaPhoto):
                    size: int = max(media.photo.sizes[-1].sizes)
                    entities.append(TelegramPhoto(
                        media.photo.id,
                        size,
                        source=media,
                        caller=self
                    ))

                if isinstance(media, telethon.types.MessageMediaDocument):
                    size: int = media.document.size
                    video_attributes = None
                    file_name: str = "non defined"
                    for attr in media.document.attributes:
                        if isinstance(attr, telethon.types.DocumentAttributeFilename):
                            file_name: str = attr.file_name
                        elif isinstance(attr, telethon.types.DocumentAttributeVideo):
                            video_attributes = attr
                    if video_attributes:
                        entities.append(TelegramVideo(
                            media.document.id,
                            size,
                            video_attributes.duration,
                            source=media,
                            caller=self
                        ))
                    else:
                        entities.append(TelegramDocument(
                            media.document.id,
                            size,
                            file_name,
                            source=media,
                            caller=self
                        ))

            user: TelegramUser = await self.transform(object_.peer_id)
            return TelegramMessage(
                object_.id,
                user,
                TelegramChat(
                    object_.peer_id.user_id,
                    base.ChatType.PRIVATE,
                    user.first_name,
                    [user],
                    source=object_,
                    caller=self
                ),
                object_.date,
                object_.message,
                entities,
                source=object_,
                caller=self
            )

        else:
            raise ValueError(f"Unsupported TLObject type: {type(object_)}")

    async def fetch_entity(self, id_: int) -> Entity:
        tl_object = await self.client.get_entity(id_)
        return await self.transform(tl_object)

    async def get_entity(self, id_: int) -> Entity:
        tl_object = await self.client.get_entity(id_)
        return await self.transform(tl_object)

    async def send_message(self, id_: int, text: str, entities: list[Media] = None) -> Entity:
        tl_object = await self.client.send_message(id_, text)
        return await self.transform(tl_object)

    async def _start(self):
        print("Client has started.")
        await self.send_message(1667209703, "Бот запущен.")
        await self.client.start(self.bot_token)
        await self.client.run_until_disconnected()

    def start(self):
        with self.client:
            self.client.loop.run_until_complete(self._start())


def get():
    return TelegramInterface
