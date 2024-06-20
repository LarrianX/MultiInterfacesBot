import datetime
import logging
from typing import Any, Optional

import telethon.types
from telethon.tl.functions.messages import GetStickerSetRequest
from telethon.tl.patched import Message
from telethon.types import TLObject, DocumentAttributeSticker

from ...base import Interface
from ...base import types


class TelegramMedia(types.Media):
    def __init__(self, id: int, file_size: int, file_name: str, source: Any = None, caller: Interface = None):
        super().__init__(id, file_size, file_name, source, caller)

    async def get(self) -> Optional[bytes]:
        if not self.source and self.caller and self.id:
            self.source = self.caller.get_entity(self.id)
            return await self.get()

        elif isinstance(self.source, TLObject) and self.caller:
            return await self.caller.client.download_media(self.source, file=bytes)

        elif isinstance(self.source, bytes):
            return self.source


class TelegramSticker(types.Sticker, TelegramMedia):
    def __init__(self, id: int, file_size: int, alt: str, sticker_set: Any, file_name: str = "sticker.webp",
                 source: Any = None, caller: Interface = None):
        super().__init__(id, file_size, alt, sticker_set, file_name, source, caller)


class TelegramAnimatedSticker(types.AnimatedSticker, TelegramSticker):
    def __init__(self, id: int, file_size: int, duration: int | float, alt: str, sticker_set: Any,
                 file_name: str = "sticker.webm",
                 source: Any = None, caller: Interface = None):
        super().__init__(id, file_size, duration, alt, sticker_set, file_name, source, caller)


class TelegramStickerSet(types.StickerSet):
    def __init__(self, id: int, title: str, count_stickers: int, source: Any = None, caller: object = None):
        super().__init__(id, title, count_stickers, source, caller)

    @classmethod
    async def from_tl(cls, tl: telethon.types.InputStickerSetID, caller: object):
        sticker_set: telethon.types.messages.StickerSet = await caller.client(GetStickerSetRequest(tl, 0))
        return TelegramStickerSet(
            id=sticker_set.set.id,
            title=sticker_set.set.title,
            count_stickers=sticker_set.set.count,
            source=sticker_set,
            caller=caller
        )

    async def get_sticker_by_index(self, index: int) -> TelegramSticker:
        return (await self.get_all_stickers())[index]

    async def get_all_stickers(self) -> list[TelegramSticker]:
        result = []
        for sticker in self.source.documents:
            # Ищем индекс атрибута
            index_of_attr = None
            index = 0
            for attr in sticker.attributes:
                if isinstance(attr, DocumentAttributeSticker):
                    index_of_attr = index
                index += 1
            sticker.attributes[index_of_attr].stickerset = self
            result.append(await self.caller.transform(sticker))  # TelegramInterface, логично
        return result


class TelegramPhoto(types.Photo, TelegramMedia):
    def __init__(self, id: int, file_size: int, file_name: str = "image.jpg", source: Any = None,
                 caller: Interface = None):
        super().__init__(id, file_size, file_name, source, caller)

    @classmethod
    async def from_tl(cls, tl: telethon.types.Photo, caller: Any = None):
        size: int = max(tl.sizes[-1].sizes)
        return TelegramPhoto(
            id=tl.id,
            file_size=size,
            source=tl,
            caller=caller
        )


class TelegramVideo(types.Video, TelegramMedia):
    def __init__(self, id: int, file_size: int, duration: int | float, file_name: str = "video.mp4",
                 source: Any = None, caller: Interface = None):
        super().__init__(id, file_size, duration, file_name, source, caller)
        # Также в принципе сюда можно добавить разрешение видео.


class TelegramAudio(types.Audio, TelegramMedia):
    def __init__(self, id: int, file_size: int, duration: int | float, file_name: str = "audio.ogg",
                 source: Any = None, caller: Interface = None):
        super().__init__(id, file_size, duration, file_name, source, caller)


class TelegramDocument(types.Document, TelegramMedia):
    def __init__(self, id: int, file_size: int, file_name: str, source: Any = None, caller: Interface = None):
        super().__init__(id, file_size, file_name, source, caller)

    @classmethod
    async def from_tl(cls, tl: telethon.types.Document, caller):
        """
        Возвращает не только TelegramDocument
        """
        size: int = tl.size

        sticker_attributes = audio_attributes = image_attributes = video_attributes = file_name = None
        for attr in tl.attributes:
            if isinstance(attr, telethon.types.DocumentAttributeFilename):
                file_name = attr.file_name
            elif isinstance(attr, telethon.types.DocumentAttributeSticker):
                sticker_attributes = attr
            elif isinstance(attr, telethon.types.DocumentAttributeAudio):
                audio_attributes = attr
            elif isinstance(attr, telethon.types.DocumentAttributeImageSize):
                image_attributes = attr
            elif isinstance(attr, telethon.types.DocumentAttributeVideo):
                video_attributes = attr

        if sticker_attributes:
            # Обработка стикеров
            if isinstance(sticker_attributes.stickerset, telethon.types.InputStickerSetID):
                sticker_set = await TelegramStickerSet.from_tl(sticker_attributes.stickerset, caller=caller)
            else:
                sticker_set = sticker_attributes.stickerset

            if image_attributes:
                return TelegramSticker(
                    id=tl.id,
                    file_size=size,
                    alt=sticker_attributes.alt,
                    sticker_set=sticker_set,
                    file_name=file_name,
                    source=tl,
                    caller=caller
                )
            elif video_attributes:
                return TelegramAnimatedSticker(
                    id=tl.id,
                    file_size=size,
                    duration=video_attributes.duration,
                    alt=sticker_attributes.alt,
                    sticker_set=sticker_set,
                    file_name=file_name,
                    source=tl,
                    caller=caller
                )
            else:
                logging.warning("Ни рыба, ни мясо")

        elif video_attributes:
            # Видео
            return TelegramVideo(
                id=tl.id,
                file_size=size,
                duration=video_attributes.duration,
                file_name=file_name,
                source=tl,
                caller=caller
            )
        elif audio_attributes:
            # Аудио
            return TelegramAudio(
                id=tl.id,
                file_size=size,
                duration=audio_attributes.duration,
                file_name=file_name,
                source=tl,
                caller=caller
            )
        else:
            return cls(
                id=tl.id,
                file_size=size,
                file_name=file_name,
                source=tl,
                caller=caller
            )


class TelegramUser(types.User):
    def __init__(self, id: int, first_name: Optional[str], last_name: Optional[str], username: Optional[str],
                 is_bot: bool,
                 source: Any = None, caller: object = None):
        super().__init__(id, "Telegram", first_name, last_name, username, is_bot, source, caller)

    @classmethod
    async def from_tl(cls, tl: telethon.types.PeerUser | telethon.types.User, caller: object):
        if isinstance(tl, telethon.types.PeerUser):
            tl: telethon.types.User = await caller.client.get_entity(tl.user_id)
        return cls(
            id=tl.id,
            first_name=tl.first_name,
            last_name=tl.last_name,
            username=tl.username,
            is_bot=tl.bot,
            source=tl,
            caller=caller
        )


class TelegramChat(types.Chat):
    def __init__(self, id: int, type: types.ChatType, title: str, members: list[types.User],
                 source: Any = None, caller: object = None):
        super().__init__(id, type, title, members, source, caller)


class TelegramPollAnswer(types.PollAnswer):
    def __init__(self, id: int, text: str, voters: int | list[types.User], correct: Optional[bool],
                 source: Any = None, caller: object = None):
        super().__init__(id, text, voters, correct, source, caller)


class TelegramPoll(types.Poll):
    def __init__(self, id: int, question: str, answers: list[TelegramPollAnswer], voters: int | list[types.User],
                 public_votes: bool, multiple_choice: bool, quiz: bool, solution: Optional[str], closed: bool,
                 close_period: Optional[int], close_date: Optional[datetime.datetime],
                 source: Any = None, caller: object = None):
        super().__init__(id, question, answers, voters, public_votes, multiple_choice, quiz, solution,
                         closed, close_period, close_date, source, caller)

    @classmethod
    async def from_tl(cls, tl: telethon.types.MessageMediaPoll, caller: Any = None):
        answers = []
        for ans in tl.poll.answers:
            answers.append(TelegramPollAnswer(
                id=tl.poll.id,
                text=ans.text,
                voters=123,  # TODO:
                correct=None,
                source=tl.poll,
                caller=caller
            ))

        if tl.results.recent_voters:
            voters = []
            for user in tl.results.recent_voters:
                voters.append(await TelegramUser.from_tl(user, caller=caller))
        else:
            voters = tl.results.total_voters

        solution = tl.results.solution if tl.poll.quiz and tl.results.solution else None

        return cls(
            id=tl.poll.id,
            question=tl.poll.question,
            answers=answers,
            voters=voters,
            public_votes=tl.poll.public_voters,
            multiple_choice=tl.poll.multiple_choice,
            quiz=tl.poll.quiz,
            solution=solution,
            closed=tl.poll.closed,
            close_period=tl.poll.close_period,
            close_date=tl.poll.close_date,
            source=tl.poll,
            caller=caller
        )


class TelegramGeoPoint(types.GeoPoint):
    def __init__(self, id: int, latitude: float, longitude: float, accuracy: Optional[float] = None,
                 source: Any = None, caller: object = None):
        super().__init__(id, latitude, longitude, accuracy, source, caller)

    @classmethod
    async def from_tl(cls, tl: telethon.types.GeoPoint, caller: Any = None):
        return TelegramGeoPoint(
            id=0,
            longitude=tl.long,
            latitude=tl.lat,
            accuracy=tl.accuracy_radius,
            source=tl,
            caller=caller
        )


class TelegramVenue(types.Venue):
    def __init__(self, venue_id: str, geo: TelegramGeoPoint, title: str, address: str,
                 source: Any = None, caller: object = None):
        super().__init__(int(venue_id, 16), geo, title, address, source, caller)

    @classmethod
    async def from_tl(cls, tl: telethon.types.MessageMediaVenue, caller: object):
        return cls(
            venue_id=tl.venue_id,
            geo=await TelegramGeoPoint.from_tl(tl.geo),
            title=tl.title,
            address=tl.address,
            source=tl,
            caller=caller
        )

    def get_venue_id(self):
        return hex(self.id)[2:]


class TelegramContact(types.Contact):
    def __init__(self, id: int, phone_number: str, first_name: str, last_name: str, username: str,
                 source: Any = None, caller: object = None):
        super().__init__(id, phone_number, first_name, last_name, username, source, caller)

    @classmethod
    async def from_tl(cls, tl: telethon.types.MessageMediaContact, caller: object):
        return cls(
            id=tl.user_id,
            phone_number=tl.phone_number,
            first_name=tl.first_name,
            last_name=tl.last_name,
            username=tl.vcard,
            source=tl,
            caller=caller
        )


async def process_attachment(tl: TLObject, caller: object) -> types.Attachment:
    if isinstance(tl, telethon.types.MessageMediaPhoto):
        return await TelegramPhoto.from_tl(tl.photo, caller=caller)

    elif isinstance(tl, telethon.types.MessageMediaPoll):
        return await TelegramPoll.from_tl(tl, caller=caller)

    elif isinstance(tl, telethon.types.MessageMediaDocument):
        return await TelegramDocument.from_tl(tl.document, caller=caller)

    elif isinstance(tl, telethon.types.MessageMediaGeo) or isinstance(tl, telethon.types.MessageMediaGeoLive):
        return await TelegramGeoPoint.from_tl(tl.geo, caller=caller)

    elif isinstance(tl, telethon.types.MessageMediaVenue):
        return await TelegramVenue.from_tl(tl, caller=caller)

    elif isinstance(tl, telethon.types.MessageMediaContact):
        return await TelegramContact.from_tl(tl, caller=caller)

    else:
        logging.warning(f"Неизвестный или неподдерживаемый тип вложений: {type(tl)}")
        return types.Unsupported(
            0,
            source=tl,
            caller=caller
        )


class TelegramMessage(types.Message):
    def __init__(self, id: int, from_user: TelegramUser, chat: TelegramChat, date: datetime.datetime, text: str,
                 attachments: list[types.Attachment],
                 source: Any = None, caller: object = None):
        super().__init__(id, from_user, chat, date, text, attachments, source, caller)

    @classmethod
    async def from_tl(cls, tl: telethon.types.Message, caller: object):
        attachments = []
        if tl.media:
            attachments.append(await process_attachment(tl.media, caller=caller))

        user = await TelegramUser.from_tl(tl.peer_id, caller=caller)
        chat = TelegramChat(
            id=tl.peer_id.user_id,
            type=types.ChatType.PRIVATE,
            title=user.first_name,
            members=[user],
            source=tl,
            caller=caller,
        )
        return cls(
            id=tl.id,
            from_user=user,
            chat=chat,
            date=tl.date,
            text=tl.message,
            attachments=attachments,
            source=tl,
            caller=caller
        )

    async def reply(self, text: str, attachments: list[types.Attachment] = None):
        if not self.source and self.caller:
            self.source = self.caller.get_entity(self.id)
            await self.reply(text, attachments)
        elif isinstance(self.source, Message):
            await self.source.reply(text)

    async def answer(self, text: str, attachments: list[types.Attachment] = None):
        if not self.source and self.caller:
            self.source = self.caller.get_entity(self.id)
            await self.answer(text, attachments)
        elif isinstance(self.source, Message):
            await self.source.respond(text)

    async def edit(self, text: str, attachments: list[types.Attachment] = None):
        if not self.source and self.caller:
            self.source = self.caller.get_entity(self.id)
            await self.reply(text, attachments)
        elif isinstance(self.source, Message):
            await self.source.edit(text)


class TelegramTestMessage(TelegramMessage):
    def _test(self, sth: Any):
        if self.caller:
            self.caller.buffer = sth

    async def answer(self, text: str, attachments: list[types.Attachment] = None):
        self._test(text)

    async def reply(self, text: str, attachments: list[types.Attachment] = None):
        self._test(text)

    async def edit(self, text: str, attachments: list[types.Attachment] = None):
        self._test(text)
