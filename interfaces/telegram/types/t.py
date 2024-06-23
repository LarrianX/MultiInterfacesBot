import datetime
import logging
from typing import Any, Optional

import telethon.types
from telethon.tl.functions.messages import GetStickerSetRequest
from telethon.tl.patched import Message
from telethon.types import TLObject, DocumentAttributeSticker

from ...base import Interface
from ...base import types

PLATFORM = "Telegram"


class TelegramUser(types.User):
    def __init__(self, id: int, first_name: str, last_name: str, username: str, is_bot: bool, platform=PLATFORM,
                 source: object = None, caller: Interface = None):
        super().__init__(id=id, platform=platform, first_name=first_name, last_name=last_name, username=username,
                         is_bot=is_bot, source=source, caller=caller)

    @classmethod
    async def from_tl(cls, tl: telethon.types.PeerUser | telethon.types.User, caller: Interface):
        if isinstance(tl, telethon.types.PeerUser):
            tl: telethon.types.User = await caller.client.get_entity(tl.user_id)
        return cls(
            id=tl.id,
            first_name=tl.first_name or '',
            last_name=tl.last_name or '',
            username=tl.username or '',
            is_bot=tl.bot,
            source=tl,
            caller=caller
        )


class TelegramChat(types.Chat):
    def __init__(self, id: int, type: types.ChatType, title: str, members: list[types.User], platform=PLATFORM,
                 source: object = None, caller: Interface = None):
        super().__init__(id=id, platform=platform, type=type, title=title, members=members,
                         source=source, caller=caller)


class TelegramMedia(types.Media):
    def __init__(self, id: int, file_name: str, file_size: int,
                 source: object = None, caller: Interface = None):
        super().__init__(id=id, file_name=file_name, file_size=file_size, source=source, caller=caller)

    async def get(self) -> Optional[bytes]:
        if not self.source and self.caller and self.id:
            self.source = self.caller.get_entity(self.id)
            return await self.get()

        elif isinstance(self.source, TLObject) and self.caller:
            return await self.caller.client.download_media(self.source, file=bytes)

        elif isinstance(self.source, bytes):
            return self.source


class TelegramMessage(types.Message):
    def __init__(self, id: int, from_user: TelegramUser, chat: TelegramChat, date: datetime.datetime, text: str,
                 attachments: list[types.Attachment],
                 source: object = None, caller: Interface = None):
        super().__init__(id=id, from_user=from_user, chat=chat, date=date, text=text, attachments=attachments,
                         source=source, caller=caller)

    @classmethod
    async def from_tl(cls, tl: telethon.types.Message, caller: Interface):
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


class TelegramSticker(types.Sticker, TelegramMedia):
    def __init__(self, id: int, file_size: int, alt: str, sticker_set: Any, file_name: str = "sticker.webp",
                 source: object = None, caller: Interface = None):
        super().__init__(id=id, file_size=file_size, file_name=file_name, alt=alt, sticker_set=sticker_set,
                         source=source, caller=caller)


class TelegramAnimatedSticker(types.AnimatedSticker, TelegramSticker):
    def __init__(self, id: int, file_size: int, duration: int | float, alt: str, sticker_set: Any,
                 file_name: str = "sticker.webm",
                 source: object = None, caller: Interface = None):
        super().__init__(id=id, file_name=file_name, file_size=file_size, duration=duration,
                         alt=alt, sticker_set=sticker_set, source=source, caller=caller)


class TelegramStickerSet(types.StickerSet):
    def __init__(self, id: int, title: str, count_stickers: int,
                 source: object = None, caller: Interface = None):
        super().__init__(id=id, title=title, count_stickers=count_stickers, source=source, caller=caller)

    @classmethod
    async def from_tl(cls, tl: telethon.types.InputStickerSetID, caller: Interface):
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
    def __init__(self, id: int, file_size: int, file_name: str = "image.jpg",
                 source: object = None, caller: Interface = None):
        super().__init__(id=id, file_size=file_size, file_name=file_name, source=source, caller=caller)

    @classmethod
    async def from_tl(cls, tl: telethon.types.Photo, caller: Interface):
        size: int = max(tl.sizes[-1].sizes)
        return TelegramPhoto(
            id=tl.id,
            file_size=size,
            source=tl,
            caller=caller
        )


class TelegramVideo(types.Video, TelegramMedia):
    def __init__(self, id: int, file_size: int, duration: int | float, file_name: str = "video.mp4",
                 source: object = None, caller: Interface = None):
        super().__init__(id=id, file_name=file_name, file_size=file_size, duration=duration,
                         source=source, caller=caller)
        # Также в принципе сюда можно добавить разрешение видео.


class TelegramAudio(types.Audio, TelegramMedia):
    def __init__(self, id: int, file_size: int, duration: int | float, file_name: Optional[str] = "audio.ogg",
                 source: object = None, caller: Interface = None):
        super().__init__(id=id, file_name=file_name, file_size=file_size, duration=duration,
                         source=source, caller=caller)


class TelegramDocument(types.Document, TelegramMedia):
    def __init__(self, id: int, file_size: int, file_name: str,
                 source: object = None, caller: Interface = None):
        super().__init__(id=id, file_name=file_name, file_size=file_size, source=source, caller=caller)

    @classmethod
    async def from_tl(cls, tl: telethon.types.Document, caller: Interface):
        """
        Возвращает не только TelegramDocument.
        """
        size: int = tl.size

        kwargs = {
            "id": tl.id,
            "file_size": size,
            "source": tl,
            "caller": caller,
        }

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

        if file_name:
            kwargs['file_name'] = file_name

        if sticker_attributes:
            # Обработка стикеров
            if isinstance(sticker_attributes.stickerset, telethon.types.InputStickerSetID):
                sticker_set = await TelegramStickerSet.from_tl(sticker_attributes.stickerset, caller=caller)
            else:
                sticker_set = sticker_attributes.stickerset

            kwargs['sticker_set'] = sticker_set
            kwargs['alt'] = sticker_attributes.alt

            if image_attributes:
                return TelegramSticker(**kwargs)
            elif video_attributes:
                return TelegramAnimatedSticker(**kwargs, duration=video_attributes.duration)
            else:
                logging.error("Ни рыба, ни мясо")

        elif video_attributes:
            # Видео
            return TelegramVideo(**kwargs, duration=video_attributes.duration)
        elif audio_attributes:
            # Аудио
            return TelegramAudio(**kwargs, duration=audio_attributes.duration)
        else:
            return cls(**kwargs)


class TelegramPollAnswer(types.PollAnswer):
    def __init__(self, id: int, text: str, voters: int | list[types.User], correct: Optional[bool],
                 source: object = None, caller: Interface = None):
        super().__init__(id=id, text=text, voters=voters, correct=correct, source=source, caller=caller)


class TelegramPoll(types.Poll):
    def __init__(self, id: int, question: str, answers: list[TelegramPollAnswer], voters: int | list[types.User],
                 public_votes: bool, multiple_choice: bool, quiz: bool, solution: Optional[str], closed: bool,
                 close_period: Optional[int], close_date: Optional[datetime.datetime],
                 source: object = None, caller: Interface = None):
        super().__init__(id=id, question=question, answers=answers, voters=voters, public_votes=public_votes,
                         multiple_choice=multiple_choice, quiz=quiz, solution=solution, closed=closed,
                         close_period=close_period, close_date=close_date, source=source, caller=caller)

    @classmethod
    async def from_tl(cls, tl: telethon.types.MessageMediaPoll, caller: Interface = None):
        answers = []
        for ans in tl.poll.answers:
            answers.append(TelegramPollAnswer(
                id=tl.poll.id,
                text=ans.text,
                voters=0,
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
                 source: object = None, caller: Interface = None):
        super().__init__(id=id, latitude=latitude, longitude=longitude, accuracy=accuracy,
                         source=source, caller=caller)

    @classmethod
    async def from_tl(cls, tl: telethon.types.GeoPoint, caller: Interface = None):
        return TelegramGeoPoint(
            id=0,
            longitude=tl.long,
            latitude=tl.lat,
            accuracy=tl.accuracy_radius,
            source=tl,
            caller=caller
        )


class TelegramVenue(types.Venue):
    def __init__(self, id: int | str, geo: TelegramGeoPoint, title: str, address: str,
                 source: object = None, caller: Interface = None):
        if isinstance(id, str):
            id = int(id, 16)
        super().__init__(id=id, geo=geo, title=title, address=address, source=source, caller=caller)

    @classmethod
    async def from_tl(cls, tl: telethon.types.MessageMediaVenue, caller: Interface):
        return cls(
            id=tl.venue_id,
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
                 source: object = None, caller: Interface = None):
        super().__init__(id=id, phone_number=phone_number, first_name=first_name, last_name=last_name,
                         username=username, source=source, caller=caller)

    @classmethod
    async def from_tl(cls, tl: telethon.types.MessageMediaContact, caller: Interface):
        return cls(
            id=tl.user_id,
            phone_number=tl.phone_number,
            first_name=tl.first_name,
            last_name=tl.last_name,
            username=tl.vcard,
            source=tl,
            caller=caller
        )


async def process_attachment(tl: TLObject, caller: Interface) -> types.Attachment:
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
