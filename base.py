import datetime
import logging
import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional

import clipboard

logger = logging.getLogger(__name__)


def format_bytes(size):
    # 2**10 = 1024
    power = 2 ** 10
    n = 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}B"


class ChatType(Enum):
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
        # Сюда можно добавить разрешение


class Video(Media, ABC):
    def __init__(self, id: int, file_size: int, duration: int | float, file_name: str = "", source: Any = None,
                 caller: object = None):
        super().__init__(id, file_size, file_name, source, caller)
        self.duration = duration
        # И сюда тоже


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
    async def edit(self, text: str, attachmentss: list[Attachment] = None):
        pass


class BaseInterface:
    def __init__(self, user_db: Any):
        self.user_db = user_db
        # В будущем этого недоразумения не будет
        self.await_download_users = []
        self.await_test_users = []

    async def message_handler(self, message: Message):
        try:

            if message.attachments and message.from_user.id in self.await_download_users:
                message.text = "/download"

            if message.from_user.id == 1667209703:
                clipboard.copy(str(message).replace("<ChatType.PRIVATE: 'private'>", "base.ChatType.PRIVATE").replace(
                    ", platform='Telegram'", "") + ",")

            print(message)
            print("Source:", message.source)
            if message.attachments:
                print(message.attachments[0])
            print(f"{message.from_user}: {message.text!r}")

            if message.text.startswith("/"):
                await self.command_handler(message)
        # except SystemExit as e:
        #     pass
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {e}")
            await message.answer("Произошла ошибка при обработке вашего сообщения.")

    async def command_handler(self, message: Message):
        try:
            raw = message.text[1:].split(" ")
            command = raw[0]
            args = raw[1:]
            func = getattr(self, command, None)
            if func:
                num_args_expected = func.__code__.co_argcount - 2  # Вычитаем 1, так как первый аргумент это self
                num_args_provided = len(args)
                if num_args_provided < num_args_expected:
                    raise ValueError(
                        f"Недостаточно аргументов. Ожидалось как минимум: {num_args_expected}, получено: {num_args_provided}")
                result = await func(message, *args)
                if result:
                    await message.reply(result)
            else:
                logger.warning(f"Неизвестная команда: {command}")
                await message.answer(f"Неизвестная команда: {command}")
        except ValueError as e:
            logger.error(f"{e}")
            await message.answer(f"{e}")
        except Exception as e:
            logger.error(f"Ошибка при обработке команды: {e}")
            await message.answer("Произошла ошибка при обработке вашей команды.")

    async def _download(self, attachment: Media):
        if hasattr(attachment, "get"):
            b = await attachment.get()
            if attachment.file_name:
                file_name = attachment.file_name
            else:
                file_name = "unknown"
                logger.warning(f"Неизвестный тип сущности: {type(attachment)}")
            with open(file_name, "wb") as f:
                f.write(b)

    async def echo(self, message: Message, *args):
        return message.text

    async def system(self, message: Message, *args):
        return f"Exit code: {str(os.system(" ".join(args)))}"

    async def exec(self, message: Message, *args):
        code = " ".join(args)
        local_vars = locals()
        try:
            exec(f"""async def __exec():\n\t{code}""", local_vars)
            await local_vars["__exec"]()
            return "Код выполнен успешно."
        except Exception as e:
            logger.error(f"Ошибка при выполнении кода: {e}")
            return f"Ошибка при выполнении кода: {e}"

    async def download(self, message: Message, *args):
        if message.attachments:
            for media in message.attachments:
                if isinstance(media, Media):
                    await self._download(media)
            return "Скачано!"
        else:
            self.await_download_users.append(message.from_user.id)
            print(self.await_download_users)  # TODO: использовать logging
            return "Ожидаю медиа..."

    async def test(self, message: Message, *args):
        results = await message.caller.tests()
        return f"Тестирование завершено: вот результаты: \n{'\n'.join(f'{key} -- {value}' for key, value in results.items())}"


class Interface(ABC):
    def __init__(self, base_interface: BaseInterface):
        self.base_interface = base_interface
        # так должно быть в классе наследнике

    @abstractmethod
    async def fetch_entity(self, id: int) -> Entity:
        pass

    @abstractmethod
    async def get_entity(self, id: int) -> Entity:
        pass

    @abstractmethod
    async def send_message(self, id: int, text: str, entities: list[Media] = None) -> Message:
        pass

    @abstractmethod
    async def start(self):
        pass

    @abstractmethod
    async def tests(self):
        pass
