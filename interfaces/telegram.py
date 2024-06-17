from dataclasses import dataclass
from typing import Any
import datetime
import logging
import os

import base
from base import Entity, Media, User

import telethon
import telethon.tl.patched  # TODO: избавиться от этого и сделать как ниже
from telethon.tl.functions.messages import GetStickerSetRequest, GetStickersRequest

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
    def __init__(self, id_: int, file_size: int, file_name: str, source: Any = None, caller: base.Interface = None):
        super().__init__(id_, file_size, file_name, source, caller)

    async def get(self):
        if isinstance(self.source, bytes):
            return self.source
        elif isinstance(self.source, telethon.types.TLObject) and self.caller:
            return await self.caller.client.download_media(self.source, file=bytes)


class TelegramSticker(base.Sticker, TelegramMedia):
    def __init__(self, id_: int, file_size: int, alt: str, sticker_set: Any, file_name: str = "sticker.webp",
                 source: Any = None, caller: base.Interface = None):
        super().__init__(id_, file_size, alt, sticker_set, file_name, source, caller)


class TelegramAnimatedSticker(base.AnimatedSticker, TelegramSticker):
    def __init__(self, id_: int, file_size: int, duration: int | float, alt: str, sticker_set: Any,
                 file_name: str = "sticker.webm",
                 source: Any = None, caller: base.Interface = None):
        super().__init__(id_, file_size, duration, alt, sticker_set, file_name, source, caller)


class TelegramStickerSet(base.StickerSet):
    def __init__(self, id_: int, title: str, count_stickers: int, source: Any = None, caller: object = None):
        super().__init__(id_, title, count_stickers, source, caller)

    async def get_sticker_by_index(self, index: int) -> TelegramSticker:
        return (await self.get_all_stickers())[index]

    async def get_all_stickers(self) -> list[TelegramSticker]:
        result = []
        for sticker in self.source.documents:
            # Ищем индекс атрибута
            index_of_attr = None
            index = 0
            for attr in sticker.attributes:
                if isinstance(attr, telethon.types.DocumentAttributeSticker):
                    index_of_attr = index
                index += 1
            sticker.attributes[index_of_attr].stickerset = self
            result.append(await self.caller.transform(sticker))  # TelegramInterface, логично
        return result


class TelegramPhoto(base.Photo, TelegramMedia):
    def __init__(self, id_: int, file_size: int, file_name: str = "image.jpg", source: Any = None,
                 caller: base.Interface = None):
        # TelegramMedia.__init__(self, id_, file_size, source, caller)
        super().__init__(id_, file_size, file_name, source, caller)
        # Также в принципе сюда можно добавить разрешение картинки.


class TelegramVideo(base.Video, TelegramMedia):
    def __init__(self, id_: int, file_size: int, duration: int | float, file_name: str = "video.mp4",
                 source: Any = None, caller: base.Interface = None):
        super().__init__(id_, file_size, duration, file_name, source, caller)
        # Также в принципе сюда можно добавить разрешение видео.


class TelegramAudio(base.Audio, TelegramMedia):
    def __init__(self, id_: int, file_size: int, duration: int | float, file_name: str = "audio.ogg",
                 source: Any = None, caller: base.Interface = None):
        super().__init__(id_, file_size, duration, file_name, source, caller)


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
        ).start(bot_token=self.bot_token)
        self.base_interface = base_interface
        self.buffer: Any = None

        # Добавляем обработчик сообщений
        self.client.add_event_handler(self._handle_message, telethon.events.NewMessage())

    async def _handle_message(self, event: telethon.events.NewMessage.Event):
        # Преобразуем сообщение в объект Entity
        entity: TelegramMessage = await self.transform(event.message)  # type: ignore

        # Вызываем обработчик сообщения из base_interface
        await self.base_interface.message_handler(entity)

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

                elif isinstance(media, telethon.types.MessageMediaDocument):
                    entities.append(await self.transform(media.document))

            user: TelegramUser = await self.transform(object_.peer_id)  # type: ignore
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

        elif isinstance(object_, telethon.types.Document):
            size: int = object_.size
            sticker_attributes = audio_attributes = image_attributes = video_attributes = None
            file_name: str = "unknown"
            for attr in object_.attributes:
                if isinstance(attr, telethon.types.DocumentAttributeFilename):
                    file_name: str = attr.file_name
                elif isinstance(attr, telethon.types.DocumentAttributeSticker):
                    sticker_attributes = attr
                elif isinstance(attr, telethon.types.DocumentAttributeAudio):
                    audio_attributes = attr
                elif isinstance(attr, telethon.types.DocumentAttributeImageSize):
                    image_attributes = attr
                elif isinstance(attr, telethon.types.DocumentAttributeVideo):
                    video_attributes = attr

            if sticker_attributes:
                if isinstance(sticker_attributes.stickerset, telethon.types.InputStickerSetID):
                    sticker_set = await self.transform(sticker_attributes.stickerset)  # type: ignore
                elif isinstance(sticker_attributes.stickerset, TelegramStickerSet):
                    sticker_set = sticker_attributes.stickerset  # type: ignore

                if image_attributes:
                    return TelegramSticker(
                        object_.id,
                        size,
                        sticker_attributes.alt,
                        sticker_set,
                        file_name=file_name,
                        source=object_,
                        caller=self
                    )
                elif video_attributes:
                    return TelegramAnimatedSticker(
                        object_.id,
                        size,
                        video_attributes.duration,
                        sticker_attributes.alt,
                        sticker_set,
                        file_name=file_name,
                        source=object_,
                        caller=self
                    )
                else:
                    logging.warning("Ни рыба, ни мясо")

            elif video_attributes:
                return TelegramVideo(
                    object_.id,
                    size,
                    video_attributes.duration,
                    file_name=file_name,
                    source=object_,
                    caller=self
                )
            elif audio_attributes:
                return TelegramAudio(
                    object_.id,
                    size,
                    audio_attributes.duration,
                    file_name=file_name,
                    source=object_,
                    caller=self
                )
            else:
                return TelegramDocument(
                    object_.id,
                    size,
                    file_name=file_name,
                    source=object_,
                    caller=self
                )

        elif isinstance(object_, telethon.types.InputStickerSetID):
            sticker_set: telethon.types.messages.StickerSet = await self.client(GetStickerSetRequest(object_, 0))
            return TelegramStickerSet(
                sticker_set.set.id,
                sticker_set.set.title,
                sticker_set.set.count,
                source=sticker_set,
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

    async def start(self):
        print("Клиент запущен.")
        await self.send_message(1667209703, "Бот запущен.")
        await self.client.run_until_disconnected()


def get():
    return TelegramInterface
