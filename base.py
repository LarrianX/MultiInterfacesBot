import datetime
from abc import ABC, abstractmethod
from typing import Any
from enum import Enum
import logging
import os

logger = logging.getLogger(__name__)
# Проверка

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
    def __init__(self, id_: int, source: Any = None, caller: object = None):
        self.id = id_
        self.source = source
        self.caller = caller


class Media(Entity, ABC):
    def __init__(self, id_: int, file_size: int, file_name: str, source: Any = None, caller: object = None):
        super().__init__(id_, source, caller)
        self.file_size = file_size
        self.file_name = file_name

    @abstractmethod
    async def get(self):
        pass

    def __str__(self):
        return f"{self.__class__.__name__} {format_bytes(self.file_size)}"

    def __repr__(self):
        return f"{self.__class__.__name__} {format_bytes(self.file_size)}"


class Photo(Media, ABC):
    def __init__(self, id_: int, file_size: int, file_name: str = "", source: Any = None, caller: object = None):
        super().__init__(id_, file_size, file_name, source, caller)
        # Сюда можно добавить разрешение


class Video(Media, ABC):
    def __init__(self, id_: int, file_size: int, duration: int | float, file_name: str = "", source: Any = None,
                 caller: object = None):
        super().__init__(id_, file_size, file_name, source, caller)
        self.duration = duration
        # И сюда тоже


class Audio(Media, ABC):
    def __init__(self, id_: int, file_size: int, duration: int | float, file_name: str = "", source: Any = None,
                 caller: object = None):
        super().__init__(id_, file_size, file_name, source, caller)
        self.duration = duration


class Document(Media, ABC):
    def __init__(self, id_: int, file_size: int, file_name: str, source: Any = None, caller: object = None):
        super().__init__(id_, file_size, file_name, source, caller)


class User(Entity, ABC):
    def __init__(self, id_: int, platform: str, first_name: str, last_name: str, username: str, is_bot: bool,
                 source: Any = None, caller: object = None):
        super().__init__(id_, source, caller)
        self.platform = platform  # e.g. discord
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.is_bot = is_bot

    def __str__(self):
        return self.username

    def __repr__(self):
        return self.username


class Chat(Entity, ABC):
    def __init__(self, id_: int, type_: ChatType, title: str, members: list[User],
                 source: Any = None, caller: object = None):
        super().__init__(id_, source, caller)
        self.type = type_
        self.title = title
        self.members = members


class Message(Entity, ABC):
    def __init__(self, id_: int, from_user: User, chat: Chat, date: datetime.datetime, text: str, entities: list[Media],
                 source: Any = None, caller: object = None):
        super().__init__(id_, source, caller)
        self.from_user = from_user
        self.chat = chat
        self.date = date
        self.text = text
        self.entities = entities

    @abstractmethod
    async def reply(self, text: str, entities: list[Media] = None):
        pass

    @abstractmethod
    async def answer(self, text: str, entities: list[Media] = None):
        pass

    @abstractmethod
    async def edit(self, text: str, entities: list[Media] = None):
        pass


class BaseInterface:
    def __init__(self, user_db: Any):
        self.user_db = user_db

    async def message_handler(self, message: Message):
        try:
            text = message.text
            user = message.from_user
            print(message.source)
            print(message.entities)
            print(f"{user}: {text!r}")

            if text.startswith("/"):
                await self.command_handler(message)
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
                    await message.answer(result)
            else:
                logger.warning(f"Неизвестная команда: {command}")
                await message.answer(f"Неизвестная команда: {command}")
        except ValueError as e:
            logger.error(f"{e}")
            await message.answer(f"{e}")
        except Exception as e:
            logger.error(f"Ошибка при обработке команды: {e}")
            await message.answer("Произошла ошибка при обработке вашей команды.")

    async def echo(self, message: Message, *args):
        return message.text

    async def system(self, message: Message, *args):
        return f"Exit code: {str(os.system(" ".join(args)))}"

    async def exec(self, message: Message, *args):
        exec(eval("'''" + " ".join(args) + "'''"))

    async def download(self, message: Message, *args):
        if message.entities:
            for entity in message.entities:
                if hasattr(entity, "get"):
                    b = await entity.get()
                    if isinstance(entity, Photo):
                        file_name = "photo.jpg"
                    elif isinstance(entity, Video):
                        file_name = "video.mp4"
                    elif isinstance(entity, Audio):
                        file_name = "audio.mp3"
                    elif isinstance(entity, Document):
                        file_name = entity.file_name
                    else:
                        logger.warning(f"Неизвестный тип сущности: {type(entity)}")
                    with open(file_name, "wb") as f:
                        f.write(b)


class Interface(ABC):
    def __init__(self, base_interface: BaseInterface, caller: object = None):
        self.base_interface = base_interface
        self.caller = caller
        # так должно быть в классе наследнике

    @abstractmethod
    async def fetch_entity(self, id_: int) -> Entity:
        pass

    @abstractmethod
    async def get_entity(self, id_: int) -> Entity:
        pass

    @abstractmethod
    async def send_message(self, id_: int, text: str, entities: list[Media] = None) -> Message:
        pass

    @abstractmethod
    async def start(self):
        pass
