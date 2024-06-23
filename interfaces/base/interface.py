import logging
import os
from abc import ABC, abstractmethod
from typing import Any

import clipboard

from .types import *


class BaseInterface:
    def __init__(self, user_db: Any):
        self.user_db = user_db
        self.await_download_users = []

    async def message_handler(self, message: Message):
        try:
            if message.attachments and message.from_user.id in self.await_download_users:
                message.text = "/download"

            if message.from_user.id == 1667209703:
                replace = {
                    ", platform='Telegram'": "",
                    "TelegramUser(id=1667209703, first_name='онигири', last_name=None, username='Y_kto_to', is_bot=False)": "user",
                    "TelegramChat(id=1667209703, type=<ChatType.PRIVATE: 'private'>, title='онигири', members=[user])": "chat",
                }
                f = str(message)
                for key, value in replace.items():
                    f = f.replace(key, value)
                f = f + ","
                clipboard.copy(f)

            print(message)
            print("Source:", message.source)
            if message.attachments:
                print(message.attachments[0])
            print(f"{message.from_user.first_name}: {message.text!r}")

            if message.text.startswith("/"):
                await self.command_handler(message)
        except Exception as e:
            logging.error(f"Ошибка при обработке сообщения: {e}")
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
                logging.warning(f"Неизвестная команда: {command}")
                await message.answer(f"Неизвестная команда: {command}")
        except ValueError as e:
            logging.error(f"{e}")
            await message.answer(f"{e}")
        except Exception as e:
            logging.error(f"Ошибка при обработке команды: {e}")
            await message.answer("Произошла ошибка при обработке вашей команды.")

    async def _download(self, attachment: Media):
        if hasattr(attachment, "get"):
            b = await attachment.get()
            if attachment.file_name:
                file_name = attachment.file_name
            else:
                file_name = "unknown"
                logging.warning(f"Неизвестный тип сущности: {type(attachment)}")
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
            logging.error(f"Ошибка при выполнении кода: {e}")
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


class Interface(ABC):
    def __init__(self, base_interface: BaseInterface):
        self.base_interface = base_interface

    @abstractmethod
    async def get_entity(self, id: int) -> Entity:
        pass

    @abstractmethod
    async def send_message(self, id: int, text: str, entities: list[Media] = None) -> Message:
        pass

    @abstractmethod
    async def start(self):
        pass
