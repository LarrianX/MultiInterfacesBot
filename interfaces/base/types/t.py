import datetime
import enum
from abc import ABC, abstractmethod
from typing import Any, Optional


def format_bytes(size):
    # 2**10 = 1024
    power = 2 ** 10
    n = 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}B"


class ChatType(enum.Enum):
    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"


class Entity:
    def __init__(self, id: int, source: Any = None, caller: object = None):
        self.id = id
        self.source = source
        self.caller = caller

    def __str__(self):
        attrs = vars(self)
        attr_str = ', '.join(f'{key}={value!r}' for key, value in attrs.items() if key != 'source' and key != 'caller')
        return f'{self.__class__.__name__}({attr_str})'

    def __repr__(self):
        return str(self)


class Attachment(Entity):
    """
    Базовый класс для всех типов вложений.
    """
    pass


class Media(Attachment, ABC):
    def __init__(self, id: int, file_size: int, file_name: str, source: Any = None, caller: object = None):
        super().__init__(id, source, caller)
        self.file_size = file_size
        self.file_name = file_name

    @abstractmethod
    async def get(self):
        pass

    # def __str__(self):
    #     return f"{self.__class__.__name__} {format_bytes(self.file_size)}"

    # def __repr__(self):
    #     return f"{self.__class__.__name__} {format_bytes(self.file_size)}"


class Sticker(Media, ABC):
    def __init__(self, id: int, file_size: int, alt: str, sticker_set: Any, file_name: str = "",
                 source: Any = None, caller: object = None):
        super().__init__(id, file_size, file_name, source, caller)
        self.alt = alt  # смайл, сходный с содержанием со стикером
        self.sticker_set = sticker_set


class AnimatedSticker(Sticker, ABC):
    def __init__(self, id: int, file_size: int, duration: int | float, alt: str, sticker_set: Any, file_name: str = "",
                 source: Any = None, caller: object = None):
        super().__init__(id, file_size, alt, sticker_set, file_name, source, caller)
        self.duration = duration


class StickerSet(Attachment, ABC):
    def __init__(self, id: int, title: str, count_stickers: int, source: Any = None, caller: object = None):
        super().__init__(id, source, caller)
        self.title = title
        self.count_stickers = count_stickers

    @abstractmethod
    async def get_all_stickers(self) -> list[Sticker]:
        pass

    @abstractmethod
    async def get_sticker_by_index(self, index: int) -> Sticker:
        pass


class Photo(Media, ABC):
    def __init__(self, id: int, file_size: int, file_name: str = "", source: Any = None, caller: object = None):
        super().__init__(id, file_size, file_name, source, caller)


class Video(Media, ABC):
    def __init__(self, id: int, file_size: int, duration: int | float, file_name: str = "", source: Any = None,
                 caller: object = None):
        super().__init__(id, file_size, file_name, source, caller)
        self.duration = duration


class Audio(Media, ABC):
    def __init__(self, id: int, file_size: int, duration: int | float, file_name: str = "", source: Any = None,
                 caller: object = None):
        super().__init__(id, file_size, file_name, source, caller)
        self.duration = duration


class Document(Media, ABC):
    def __init__(self, id: int, file_size: int, file_name: str, source: Any = None, caller: object = None):
        super().__init__(id, file_size, file_name, source, caller)


class User(Entity, ABC):
    def __init__(self, id: int, platform: str, first_name: Optional[str], last_name: Optional[str],
                 username: Optional[str], is_bot: bool,
                 source: Any = None, caller: object = None):
        super().__init__(id, source, caller)
        self.platform = platform  # e.g. discord
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.is_bot = is_bot


class Chat(Entity, ABC):
    def __init__(self, id: int, type_: ChatType, title: str, members: list[User],
                 source: Any = None, caller: object = None):
        super().__init__(id, source, caller)
        self.type = type_
        self.title = title
        self.members = members


class PollAnswer(Entity, ABC):
    def __init__(self, id: int, text: str, voters: int | list[User], correct: Optional[bool],
                 source: Any = None, caller: object = None):
        super().__init__(id, source, caller)
        self.text = text
        self.voters = voters
        self.correct = correct  # Только если public_votes


class Poll(Attachment, ABC):
    def __init__(self, id: int, question: str, answers: list[PollAnswer], voters: int | list[User],
                 public_votes: bool, multiple_choice: bool, quiz: bool, solution: Optional[str], closed: bool,
                 close_period: Optional[int], close_date: Optional[datetime.datetime],
                 source: Any = None, caller: object = None):
        super().__init__(id, source, caller)
        self.question = question
        self.answers = answers
        self.voters = voters
        self.public_votes = public_votes
        self.multiple_choice = multiple_choice
        self.quiz = quiz
        self.solution = solution
        self.closed = closed
        self.close_period = close_period
        self.close_date = close_date


class GeoPoint(Attachment, ABC):
    def __init__(self, id: int, latitude: float, longitude: float, accuracy: Optional[float] = None,
                 source: Any = None, caller: object = None):
        super().__init__(id, source, caller)
        self.latitude = latitude
        self.longitude = longitude
        self.accuracy = accuracy


# class GeoPointLive(GeoPoint, ABC):


class Venue(Attachment, ABC):
    def __init__(self, id: int, geo: GeoPoint, title: str, address: str,
                 source: Any = None, caller: object = None):
        super().__init__(id, source, caller)
        self.geo = geo
        self.title = title
        self.address = address


class Contact(Attachment, ABC):
    def __init__(self, id: int, phone_number: str, first_name: str, last_name: str, username: str,
                 source: Any = None, caller: object = None):
        super().__init__(id, source, caller)
        self.phone_number = phone_number
        self.first_name = first_name
        self.last_name = last_name
        self.username = username


class Unsupported(Attachment):
    """
    Класс для вложений, которые не поддерживаются в данный момент.
    Есть ряд функций которые реализовываться не будут из-за их специфичности
    """


class Message(Entity, ABC):
    def __init__(self, id: int, from_user: User, chat: Chat, date: datetime.datetime, text: str,
                 attachments: list[Attachment],
                 source: Any = None, caller: object = None):
        super().__init__(id, source, caller)
        self.from_user = from_user
        self.chat = chat
        self.date = date
        self.text = text
        self.attachments = attachments

    @abstractmethod
    async def reply(self, text: str, attachments: list[Attachment] = None):
        pass

    @abstractmethod
    async def answer(self, text: str, attachments: list[Attachment] = None):
        pass

    @abstractmethod
    async def edit(self, text: str, attachments: list[Attachment] = None):
        pass
