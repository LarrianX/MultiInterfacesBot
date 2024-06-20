import datetime
import logging
import os
from typing import Any, Optional

import telethon
import telethon.tl.patched  # TODO: избавиться от этого и сделать как ниже
from telethon.tl.functions.messages import GetStickerSetRequest

import base
from base import Entity, Media, User

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


class TelegramMedia(base.Media):
    def __init__(self, id: int, file_size: int, file_name: str, source: Any = None, caller: base.Interface = None):
        super().__init__(id, file_size, file_name, source, caller)

    async def get(self) -> Optional[bytes]:
        if not self.source and self.caller and self.id:
            self.source = self.caller.get_entity(self.id)
            return await self.get()

        elif isinstance(self.source, telethon.types.TLObject) and self.caller:
            return await self.caller.client.download_media(self.source, file=bytes)

        elif isinstance(self.source, bytes):
            return self.source


class TelegramSticker(base.Sticker, TelegramMedia):
    def __init__(self, id: int, file_size: int, alt: str, sticker_set: Any, file_name: str = "sticker.webp",
                 source: Any = None, caller: base.Interface = None):
        super().__init__(id, file_size, alt, sticker_set, file_name, source, caller)


class TelegramAnimatedSticker(base.AnimatedSticker, TelegramSticker):
    def __init__(self, id: int, file_size: int, duration: int | float, alt: str, sticker_set: Any,
                 file_name: str = "sticker.webm",
                 source: Any = None, caller: base.Interface = None):
        super().__init__(id, file_size, duration, alt, sticker_set, file_name, source, caller)


class TelegramStickerSet(base.StickerSet):
    def __init__(self, id: int, title: str, count_stickers: int, source: Any = None, caller: object = None):
        super().__init__(id, title, count_stickers, source, caller)

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
    def __init__(self, id: int, file_size: int, file_name: str = "image.jpg", source: Any = None,
                 caller: base.Interface = None):
        # TelegramMedia.__init__(self, id, file_size, source, caller)
        super().__init__(id, file_size, file_name, source, caller)
        # Также в принципе сюда можно добавить разрешение картинки.


class TelegramVideo(base.Video, TelegramMedia):
    def __init__(self, id: int, file_size: int, duration: int | float, file_name: str = "video.mp4",
                 source: Any = None, caller: base.Interface = None):
        super().__init__(id, file_size, duration, file_name, source, caller)
        # Также в принципе сюда можно добавить разрешение видео.


class TelegramAudio(base.Audio, TelegramMedia):
    def __init__(self, id: int, file_size: int, duration: int | float, file_name: str = "audio.ogg",
                 source: Any = None, caller: base.Interface = None):
        super().__init__(id, file_size, duration, file_name, source, caller)


class TelegramDocument(base.Document, TelegramMedia):
    def __init__(self, id: int, file_size: int, file_name: str, source: Any = None, caller: base.Interface = None):
        super().__init__(id, file_size, file_name, source, caller)


class TelegramUser(base.User):
    def __init__(self, id: int, first_name: Optional[str], last_name: Optional[str], username: Optional[str],
                 is_bot: bool,
                 source: Any = None, caller: object = None):
        super().__init__(id, "Telegram", first_name, last_name, username, is_bot, source, caller)


class TelegramChat(base.Chat):
    def __init__(self, id: int, type: base.ChatType, title: str, members: list[User],
                 source: Any = None, caller: object = None):
        super().__init__(id, type, title, members, source, caller)


class TelegramPollAnswer(base.PollAnswer):
    def __init__(self, id: int, text: str, voters: int | list[User], correct: Optional[bool],
                 source: Any = None, caller: object = None):
        super().__init__(id, text, voters, correct, source, caller)


class TelegramPoll(base.Poll):
    def __init__(self, id: int, question: str, answers: list[TelegramPollAnswer], voters: int | list[User],
                 public_votes: bool, multiple_choice: bool, quiz: bool, solution: Optional[str], closed: bool,
                 close_period: Optional[int], close_date: Optional[datetime.datetime],
                 source: Any = None, caller: object = None):
        super().__init__(id, question, answers, voters, public_votes, multiple_choice, quiz, solution,
                         closed, close_period, close_date, source, caller)


class TelegramGeoPoint(base.GeoPoint):
    def __init__(self, id: int, latitude: float, longitude: float, accuracy: Optional[float] = None,
                 source: Any = None, caller: object = None):
        super().__init__(id, latitude, longitude, accuracy, source, caller)


class TelegramVenue(base.Venue):
    def __init__(self, venue_id: str, geo: TelegramGeoPoint, title: str, address: str,
                 source: Any = None, caller: object = None):
        super().__init__(int(venue_id, 16), geo, title, address, source, caller)

    def get_venue_id(self):
        return hex(self.id)[2:]


class TelegramContact(base.Contact):
    def __init__(self, id: int, phone_number: str, first_name: str, last_name: str, username: str,
                 source: Any = None, caller: object = None):
        super().__init__(id, phone_number, first_name, last_name, username, source, caller)


class TelegramMessage(base.Message):
    def __init__(self, id: int, from_user: TelegramUser, chat: TelegramChat, date: datetime.datetime, text: str,
                 attachments: list[base.Attachment],
                 source: Any = None, caller: object = None):
        super().__init__(id, from_user, chat, date, text, attachments, source, caller)

    async def reply(self, text: str, attachments: list[base.Attachment] = None):
        if not self.source and self.caller:
            self.source = self.caller.get_entity(self.id)
            await self.reply(text, attachments)
        elif isinstance(self.source, telethon.tl.patched.Message):
            await self.source.reply(text)

    async def answer(self, text: str, attachments: list[base.Attachment] = None):
        if not self.source and self.caller:
            self.source = self.caller.get_entity(self.id)
            await self.answer(text, attachments)
        elif isinstance(self.source, telethon.tl.patched.Message):
            await self.source.respond(text)

    async def edit(self, text: str, attachments: list[base.Attachment] = None):
        if not self.source and self.caller:
            self.source = self.caller.get_entity(self.id)
            await self.reply(text, attachments)
        elif isinstance(self.source, telethon.tl.patched.Message):
            await self.source.edit(text)


class TelegramTestMessage(TelegramMessage):
    def _test(self, sth: Any):
        if self.caller:
            self.caller.buffer = sth

    async def answer(self, text: str, attachments: list[base.Attachment] = None):
        self._test(text)

    async def reply(self, text: str, attachments: list[base.Attachment] = None):
        self._test(text)

    async def edit(self, text: str, attachments: list[base.Attachment] = None):
        self._test(text)


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
            attachments = []
            if object_.media:
                media = object_.media

                if isinstance(media, telethon.types.MessageMediaPhoto):
                    attachments.append(await self.transform(media.photo))

                elif isinstance(media, telethon.types.MessageMediaPoll):
                    answers = []
                    for ans in media.poll.answers:
                        answers.append(TelegramPollAnswer(
                            media.poll.id,
                            ans.text,
                            0,
                            None,
                            source=media.poll,
                            caller=self
                        ))
                    if not media.results.results and media.results.total_voters:
                        logging.warning("Не удалось прочитать результаты голосования.")

                    if media.results.recent_voters:
                        voters = []
                        for user in media.results.recent_voters:
                            voters.append(await self.transform(user))
                    else:
                        voters = media.results.total_voters

                    solution = media.results.solution if media.poll.quiz and media.results.solution else None

                    attachments.append(TelegramPoll(
                        media.poll.id,
                        media.poll.question,
                        answers,
                        voters,
                        media.poll.public_voters,
                        media.poll.multiple_choice,
                        media.poll.quiz,
                        solution,
                        media.poll.closed,
                        media.poll.close_period,
                        media.poll.close_date,
                        source=media.poll,
                        caller=self
                    ))

                elif isinstance(media, telethon.types.MessageMediaDocument):
                    attachments.append(await self.transform(media.document))

                elif isinstance(media, telethon.types.MessageMediaGeo) or isinstance(media,
                                                                                     telethon.types.MessageMediaGeoLive):
                    # Показ текущей геопозиции
                    # (не работает в реальном времени если MessageMediaGeoLive)
                    # media=MessageMediaGeo(geo=GeoPoint(long=622.789884067036795, lat=456.400915578309075,
                    #       access_hash=-6887595758470973566, accuracy_radius=None))
                    attachments.append(await self.transform(media.geo))

                elif isinstance(media, telethon.types.MessageMediaVenue):
                    # Геолокация определённого места
                    # media=MessageMediaVenue(geo=GeoPoint(long=56.77694593822952, lat=54.40821162588403, access_hash=-6887595758470973566, accuracy_radius=None),
                    #       title='ЦЕНТРАЛЬНАЯ РАЙОННАЯ БИБЛИОТЕКА', address='Советская Ул., д. 37', provider='foursquare', venue_id='1bc3900fa85540c6dba8856b', venue_type='')
                    attachments.append(TelegramVenue(
                        media.venue_id,
                        await self.transform(media.geo),  # type: ignore
                        media.title,
                        media.address,
                        source=media,
                        caller=self
                    ))

                elif isinstance(media, telethon.types.MessageMediaContact):
                    # Контакт. Он же отправляется когда человек отправляет свой номер телефона.
                    # media=MessageMediaContact(phone_number='+79832321123', first_name='Александр', last_name='',
                    # vcard='BEGIN:VCARD\nVERSION:3.0\nFN:Александр\nTEL;MOBILE:+79832321123\nEND:VCARD', user_id=5234264123)
                    attachments.append(TelegramContact(
                        media.user_id,
                        media.phone_number,
                        media.first_name,
                        media.last_name,
                        media.vcard,
                        source=media,
                        caller=self
                    ))

                # elif isinstance(media, telethon.types.MessageMediaStory):
                #     # История
                #     # media=MessageMediaStory(peer=PeerChannel(channel_id=1823077620), id=239, via_mention=False, story=None)
                #     ...
                #
                # elif isinstance(media, telethon.types.MessageMediaGiveaway):
                #     # Розыгрыш телеграмм премиум
                #     # media=media=MessageMediaGiveaway(channels=[1921079211, 1620112243], quantity=5, months=3,
                #     #       until_date=datetime.datetime(2024, 6, 12, 18, 0, tzinfo=datetime.timezone.utc), only_new_subscribers=False,
                #     #       winners_are_visible=True, countries_iso2=[], prize_description=None)
                #     ...
                #
                # elif isinstance(media, telethon.types.MessageMediaGiveawayResults):
                #     # Результаты розыгрыша
                #     # media=MessageMediaGiveawayResults(channel_id=1696195455, launch_msg_id=3000, winners_count=10,
                #     #       unclaimed_count=0, winners=[156773740, 6708355865, 502047910, 6955687441, 692875593, 896706433, 1063861981, 5375091776, 6010353236, 6419125980],
                #     #       months=3, until_date=datetime.datetime(2024, 6, 17, 17, 0, tzinfo=datetime.timezone.utc),
                #     #       only_new_subscribers=False, refunded=False, additional_peers_count=None, prize_description='iPhone 15 Pro ')
                #     ...

                else:
                    logging.warning(f"Неизвестный или неподдерживаемый тип вложений: {type(media)}")
                    attachments.append(base.Unsupported(
                        0,
                        source=object_,
                        caller=self
                    ))

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
                attachments,
                source=object_,
                caller=self
            )

        elif isinstance(object_, telethon.types.Photo):
            size: int = max(object_.sizes[-1].sizes)
            return TelegramPhoto(
                object_.id,
                size,
                source=object_,
                caller=self
            )

        elif isinstance(object_, telethon.types.Document):
            size: int = object_.size
            sticker_attributes = audio_attributes = image_attributes = video_attributes = None
            file_name: str = ""
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
                else:
                    logging.warning("Ни рыба, ни мясо")
                    # Теоретически такой ситуации вообще не должно возникнуть
                    print(type(sticker_attributes.stickerset))
                    sticker_set = TelegramStickerSet(  # type: ignore
                        0, "", 0, source=sticker_attributes.stickerset, caller=self)  # type: ignore

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

        elif isinstance(object_, telethon.types.GeoPoint):
            return TelegramGeoPoint(
                0,
                object_.long,
                object_.lat,
                object_.accuracy_radius,
                source=object_,
                caller=self
            )

        else:
            raise ValueError(f"Unsupported TLObject type: {type(object_)}")

    async def fetch_entity(self, id: int) -> Entity:
        tl_object = await self.client.get_entity(id)
        return await self.transform(tl_object)

    async def get_entity(self, id: int) -> Entity:
        tl_object = await self.client.get_entity(id)
        return await self.transform(tl_object)

    async def send_message(self, id: int, text: str, attachments: list[Media] = None) -> Entity:
        tl_object = await self.client.send_message(id, text)
        return await self.transform(tl_object)

    async def start(self):
        print("Клиент запущен.")
        await self.send_message(1667209703, "Бот запущен.")
        await self.client.run_until_disconnected()

    async def tests(self) -> dict[str, bool]:
        logging.info("Начинаю тестирование...")


def get():
    return TelegramInterface


OBJECTS_TRANSFORM_TEST = [
    # Функция теста берёт id данных сообщений, и по ним получает source данного объекта.
    # Затем она обратно конвертирует source в TelegramMessage, и смотрит, одинаковый ли результат
    TelegramMessage(id=11155,
                    from_user=TelegramUser(id=1667209703, first_name='онигири', last_name=None, username='Y_kto_to',
                                           is_bot=False),
                    chat=TelegramChat(id=1667209703, type=base.ChatType.PRIVATE, title='онигири', members=[
                        TelegramUser(id=1667209703, first_name='онигири', last_name=None, username='Y_kto_to',
                                     is_bot=False)]),
                    date=datetime.datetime(2024, 6, 20, 16, 32, 31, tzinfo=datetime.timezone.utc), text='Тест.',
                    attachments=[]),
    TelegramMessage(id=11161,
                    from_user=TelegramUser(id=1667209703, first_name='онигири', last_name=None, username='Y_kto_to',
                                           is_bot=False),
                    chat=TelegramChat(id=1667209703, type=base.ChatType.PRIVATE, title='онигири', members=[
                        TelegramUser(id=1667209703, first_name='онигири', last_name=None, username='Y_kto_to',
                                     is_bot=False)]),
                    date=datetime.datetime(2024, 6, 20, 16, 45, 50, tzinfo=datetime.timezone.utc), text='',
                    attachments=[
                        TelegramSticker(id=5389103836629582879, file_size=11010, file_name='sticker.webp', alt='🐸',
                                        sticker_set=TelegramStickerSet(id=3564845975488957109,
                                                                       title='Больше стиков тут: @stikery4',
                                                                       count_stickers=120))]),
    TelegramMessage(id=11162,
                    from_user=TelegramUser(id=1667209703, first_name='онигири', last_name=None, username='Y_kto_to',
                                           is_bot=False),
                    chat=TelegramChat(id=1667209703, type=base.ChatType.PRIVATE, title='онигири', members=[
                        TelegramUser(id=1667209703, first_name='онигири', last_name=None, username='Y_kto_to',
                                     is_bot=False)]),
                    date=datetime.datetime(2024, 6, 20, 16, 47, 17, tzinfo=datetime.timezone.utc), text='',
                    attachments=[
                        TelegramAnimatedSticker(id=5267389286709219233, file_size=52249, file_name='sticker.webm',
                                                alt='🌟', sticker_set=TelegramStickerSet(id=481662835428950014,
                                                                                        title='Ssdiwchata :: @fStikBot',
                                                                                        count_stickers=68),
                                                duration=0.033)]),
    TelegramMessage(id=11163,
                    from_user=TelegramUser(id=1667209703, first_name='онигири', last_name=None, username='Y_kto_to',
                                           is_bot=False),
                    chat=TelegramChat(id=1667209703, type=base.ChatType.PRIVATE, title='онигири', members=[
                        TelegramUser(id=1667209703, first_name='онигири', last_name=None, username='Y_kto_to',
                                     is_bot=False)]),
                    date=datetime.datetime(2024, 6, 20, 16, 50, 55, tzinfo=datetime.timezone.utc), text='Тест.',
                    attachments=[TelegramPhoto(id=5449510911426550477, file_size=83784, file_name='image.jpg')]),
    TelegramMessage(id=11166,
                    from_user=TelegramUser(id=1667209703, first_name='онигири', last_name=None, username='Y_kto_to',
                                           is_bot=False),
                    chat=TelegramChat(id=1667209703, type=base.ChatType.PRIVATE, title='онигири', members=[
                        TelegramUser(id=1667209703, first_name='онигири', last_name=None, username='Y_kto_to',
                                     is_bot=False)]),
                    date=datetime.datetime(2024, 6, 20, 17, 1, 46, tzinfo=datetime.timezone.utc), text='Тест.',
                    attachments=[TelegramVideo(id=5449510910970318860, file_size=658706,
                                               file_name='Босс_в_террарии_🤯_#shorts_#short_#террария_#terraria_#мем_#мемы.mp4',
                                               duration=12.911)]),
    TelegramMessage(id=11170,
                    from_user=TelegramUser(id=1667209703, first_name='онигири', last_name=None, username='Y_kto_to',
                                           is_bot=False),
                    chat=TelegramChat(id=1667209703, type=base.ChatType.PRIVATE, title='онигири', members=[
                        TelegramUser(id=1667209703, first_name='онигири', last_name=None, username='Y_kto_to',
                                     is_bot=False)]),
                    date=datetime.datetime(2024, 6, 20, 17, 4, 17, tzinfo=datetime.timezone.utc), text='', attachments=[
            TelegramAudio(id=5449510910970318872, file_size=2412181, file_name='Bo Burnham - 1985.mp3', duration=146)]),
    TelegramMessage(id=11171,
                    from_user=TelegramUser(id=1667209703, first_name='онигири', last_name=None, username='Y_kto_to',
                                           is_bot=False),
                    chat=TelegramChat(id=1667209703, type=base.ChatType.PRIVATE, title='онигири', members=[
                        TelegramUser(id=1667209703, first_name='онигири', last_name=None, username='Y_kto_to',
                                     is_bot=False)]),
                    date=datetime.datetime(2024, 6, 20, 17, 7, 57, tzinfo=datetime.timezone.utc), text='', attachments=[
            TelegramAudio(id=5449510910970318877, file_size=87361, file_name='unknown', duration=4)]),
    TelegramMessage(id=11173,
                    from_user=TelegramUser(id=1667209703, first_name='онигири', last_name=None, username='Y_kto_to',
                                           is_bot=False),
                    chat=TelegramChat(id=1667209703, type=base.ChatType.PRIVATE, title='онигири', members=[
                        TelegramUser(id=1667209703, first_name='онигири', last_name=None, username='Y_kto_to',
                                     is_bot=False)]),
                    date=datetime.datetime(2024, 6, 20, 17, 31, 13, tzinfo=datetime.timezone.utc), text='Тест.',
                    attachments=[TelegramDocument(id=5449510910970318925, file_size=81, file_name='.gitignore')]),
    TelegramMessage(id=11174,
                    from_user=TelegramUser(id=1667209703, first_name='онигири', last_name=None, username='Y_kto_to',
                                           is_bot=False),
                    chat=TelegramChat(id=1667209703, type=base.ChatType.PRIVATE, title='онигири', members=[
                        TelegramUser(id=1667209703, first_name='онигири', last_name=None, username='Y_kto_to',
                                     is_bot=False)]),
                    date=datetime.datetime(2024, 6, 20, 17, 32, 41, tzinfo=datetime.timezone.utc), text='',
                    attachments=[TelegramPoll(id=5449510910970300382, question='Тестовый вопрос.', answers=[
                        TelegramPollAnswer(id=5449510910970300382, text='Тестовый ответ.', voters=0, correct=None),
                        TelegramPollAnswer(id=5449510910970300382, text='Тесты... Тесты...', voters=0, correct=None)],
                                              voters=0, public_votes=False, multiple_choice=False, quiz=False,
                                              solution=None, closed=False, close_period=None, close_date=None)]),
]
