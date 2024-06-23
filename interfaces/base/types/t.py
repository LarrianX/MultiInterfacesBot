import datetime
import enum
from abc import ABC, abstractmethod
from typing import Optional

BLOCK_VARS = ["source", "caller"]


def format_bytes(size):
    power = 2 ** 10
    n = 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}B"


class ChatType(enum.Enum):
    """
    Типы чатов.
    """
    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"


class Entity:
    def __init__(self, id: int, source: object = None, caller: object = None):
        """
        Базовый класс для всех сущностей.
        :param id: ID объекта
        :param source: Если преобразовано из другого типа данных, то указывается он
        :param caller: Интерфейс, создавший этот объект
        """
        self.id = id
        self.source = source
        self.caller = caller

    def __str__(self):
        attrs = vars(self)
        attr_str = ', '.join(f'{key}={value!r}' for key, value in attrs.items() if key != 'source' and key != 'caller')
        return f'{self.__class__.__name__}({attr_str})'

    def __repr__(self):
        return str(self)

    def __xor__(self, other):
        if isinstance(other, self.__class__):
            diff = {}
            dict1 = vars(self)
            dict2 = vars(other)
            for key in dict1:
                try:
                    if dict1[key] != dict2[key] and not key.startswith("_") and key not in BLOCK_VARS:
                        diff[key] = (dict1[key], dict2[key])
                except KeyError:
                    continue
            return diff

        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (self ^ other) == {}
        return NotImplemented


class Attachment(Entity):
    """
    Базовый класс для всех типов вложений.
    """
    pass


class Unsupported(Attachment):
    """
    Класс для вложений, которые не поддерживаются в данный момент.
    Есть ряд функций которые реализовываться не будут из-за их специфичности
    """


class Media(Attachment, ABC):
    def __init__(self, id: int, file_name: str, file_size: int, source: object = None, caller: object = None):
        """
        Базовый класс для всех медиа.
        :param id: ID объекта
        :param file_name: Имя файла
        :param file_size: Размер файла
        :param source: Если преобразовано из другого типа данных, то указывается он
        :param caller: Интерфейс, создавший этот объект
        """
        super().__init__(id, source, caller)
        self.file_size = file_size
        self.file_name = file_name

    @abstractmethod
    async def get(self):
        pass

    # def __str__(self):
    #     return f"{self.__class__.__name__} {format_bytes(self.file_size)}"


class User(Entity, ABC):
    def __init__(self, id: int, platform: str, first_name: str, last_name: str, username: str, is_bot: bool,
                 source: object = None, caller: object = None):
        """
        Пользователь.
        :param id: ID объекта
        :param platform: Платформа на которой расположен пользователь. Пример: Discord
        :param first_name: Имя
        :param last_name: Фамилия
        :param username: Никнейм
        :param is_bot: Является ли ботом
        :param source: Если преобразовано из другого типа данных, то указывается он
        :param caller: Интерфейс, создавший этот объект
        """
        super().__init__(id, source, caller)
        self.platform = platform  # e.g. discord
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.is_bot = is_bot


class Chat(Entity, ABC):
    def __init__(self, id: int, platform: str, type: ChatType, title: str, members: list[User],
                 source: object = None, caller: object = None):
        """
        Чат или группа.
        :param id: ID объекта
        :param platform: Платформа на которой расположен чат. Пример: Telegram
        :param type: Тип чата
        :param title: Название чата
        :param members: Участники чата
        :param source: Если преобразовано из другого типа данных, то указывается он
        :param caller: Интерфейс, создавший этот объект
        """
        super().__init__(id, source, caller)
        self.platform = platform
        self.type = type
        self.title = title
        self.members = members


class Message(Entity, ABC):
    def __init__(self, id: int, from_user: User, chat: Chat, date: datetime.datetime, text: str,
                 attachments: list[Attachment],
                 source: object = None, caller: object = None):
        """
        Обычное сообщение
        :param id: ID объекта
        :param from_user: Кто прислал сообщение
        :param chat: Чат этого сообщения
        :param date: Дата отправки
        :param text: Текст сообщения
        :param attachments: Вложения
        :param source: Если преобразовано из другого типа данных, то указывается он
        :param caller: Интерфейс, создавший этот объект
        """
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


class Sticker(Media, ABC):
    def __init__(self, id: int, file_name: str, file_size: int, alt: str, sticker_set: object,
                 source: object = None, caller: object = None):
        """
        Стикер.
        :param id: ID объекта
        :param file_name: Имя файла
        :param file_size: Размер файла
        :param alt: Смайл, сходный с содержанием со стикером
        :param sticker_set: Набор стикеров данного стикера
        :param source: Если преобразовано из другого типа данных, то указывается он
        :param caller: Интерфейс, создавший этот объект
        """
        super().__init__(id, file_name, file_size, source, caller)
        self.alt = alt  # смайл, сходный с содержанием со стикером
        self.sticker_set = sticker_set


class AnimatedSticker(Sticker, ABC):
    def __init__(self, id: int, file_name: str, file_size: int, duration: int | float, alt: str, sticker_set: object,
                 source: object = None, caller: object = None):
        """
        Анимированный стикер.
        :param id: ID объекта
        :param file_name: Имя файла
        :param file_size: Размер файла
        :param duration: Длина анимации
        :param alt: Смайл, сходный с содержанием со стикером
        :param sticker_set: Набор стикеров данного стикера
        :param source: Если преобразовано из другого типа данных, то указывается он
        :param caller: Интерфейс, создавший этот объект
        """
        super().__init__(id, file_name, file_size, alt, sticker_set, source, caller)
        self.duration = duration


class StickerSet(Attachment, ABC):
    def __init__(self, id: int, title: str, count_stickers: int,
                 source: object = None, caller: object = None):
        """
        Набор стикеров.
        :param id: ID объекта
        :param title: Название набора
        :param count_stickers: Количество стикеров в наборе
        :param source: Если преобразовано из другого типа данных, то указывается он
        :param caller: Интерфейс, создавший этот объект
        """
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
    def __init__(self, id: int, file_name: str, file_size: int, source: object = None, caller: object = None):
        """
        Фотография.
        :param id: ID объекта
        :param file_name: Имя файла
        :param file_size: Размер файла
        :param source: Если преобразовано из другого типа данных, то указывается он
        :param caller: Интерфейс, создавший этот объект
        """
        super().__init__(id, file_name, file_size, source, caller)


class Video(Media, ABC):
    def __init__(self, id: int, file_name: str, file_size: int, duration: int | float, source: object = None,
                 caller: object = None):
        """
        Видео.
        :param id: ID объекта
        :param file_name: Имя файла
        :param file_size: Размер файла
        :param duration: Длина видео
        :param source: Если преобразовано из другого типа данных, то указывается он
        :param caller: Интерфейс, создавший этот объект
        """
        super().__init__(id, file_name, file_size, source, caller)
        self.duration = duration


class Audio(Media, ABC):
    def __init__(self, id: int, file_name: str, file_size: int, duration: int | float, source: object = None,
                 caller: object = None):
        """
        Аудио или голосовые сообщения.
        :param id: ID объекта
        :param file_name: Имя файла
        :param file_size: Размер файла
        :param duration: Длина аудио
        :param source: Если преобразовано из другого типа данных, то указывается он
        :param caller: Интерфейс, создавший этот объект
        """
        super().__init__(id, file_name, file_size, source, caller)
        self.duration = duration


class Document(Media, ABC):
    def __init__(self, id: int, file_name: str, file_size: int, source: object = None, caller: object = None):
        """
        Документ или любой файл.
        :param id: ID объекта
        :param file_name: Имя файла
        :param file_size: Размер файла
        :param source: Если преобразовано из другого типа данных, то указывается он
        :param caller: Интерфейс, создавший этот объект
        """
        super().__init__(id, file_name, file_size, source, caller)


class PollAnswer(Entity, ABC):
    def __init__(self, id: int, text: str, voters: int | list[User], correct: Optional[bool],
                 source: object = None, caller: object = None):
        """
        Вариант ответа на вопрос.
        :param id: ID объекта
        :param text: Текст параметра
        :param voters: Участники, которые выбрали этот вариант
        :param correct: Если опрос в режиме викторины, правильный ли данный ответ, иначе None
        :param source: Если преобразовано из другого типа данных, то указывается он
        :param caller: Интерфейс, создавший этот объект
        """
        super().__init__(id, source, caller)
        self.text = text
        self.voters = voters
        self.correct = correct  # Только если public_votes


class Poll(Attachment, ABC):
    def __init__(self, id: int, question: str, answers: list[PollAnswer], voters: int | list[User],
                 public_votes: bool, multiple_choice: bool, quiz: bool, solution: Optional[PollAnswer], closed: bool,
                 close_period: Optional[int], close_date: Optional[datetime.datetime],
                 source: object = None, caller: object = None):
        """
        Опрос.
        :param id: ID объекта
        :param question: Вопрос
        :param answers: Варианты ответа
        :param voters: Проголосовавшие люди
        :param public_votes: Видно ли кто проголосовал
        :param multiple_choice: Разрешено несколько вариантов ответа
        :param quiz: Режим викторины
        :param solution: Если в режиме викторины, правильный ответ, иначе None
        :param closed: Закрыт ли опрос
        :param close_period: Время в секундах до окончания опроса
        :param close_date: Время окончания опроса
        :param source: Если преобразовано из другого типа данных, то указывается он
        :param caller: Интерфейс, создавший этот объект
        """
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
                 source: object = None, caller: object = None):
        """
        Геопозиция.
        :param id: ID объекта
        :param latitude: Широта
        :param longitude: Долгота
        :param accuracy: Точность в метрах
        :param source: Если преобразовано из другого типа данных, то указывается он
        :param caller: Интерфейс, создавший этот объект
        """
        super().__init__(id, source, caller)
        self.latitude = latitude
        self.longitude = longitude
        self.accuracy = accuracy


class Venue(Attachment, ABC):
    def __init__(self, id: int, geo: GeoPoint, title: str, address: str,
                 source: object = None, caller: object = None):
        """
        Место на карте.
        :param id: ID объекта
        :param geo: Геопозиция
        :param title: Название
        :param address: Адрес
        :param source: Если преобразовано из другого типа данных, то указывается он
        :param caller: Интерфейс, создавший этот объект
        """
        super().__init__(id, source, caller)
        self.geo = geo
        self.title = title
        self.address = address


class Contact(Attachment, ABC):
    def __init__(self, id: int, phone_number: str, first_name: str, last_name: str, username: str,
                 source: object = None, caller: object = None):
        """
        Контакт.
        :param id: ID объекта
        :param phone_number: Номер телефона
        :param first_name: Имя
        :param last_name: Фамилия
        :param username: Никнейм
        :param source: Если преобразовано из другого типа данных, то указывается он
        :param caller: Интерфейс, создавший этот объект
        """
        super().__init__(id, source, caller)
        self.phone_number = phone_number
        self.first_name = first_name
        self.last_name = last_name
        self.username = username

