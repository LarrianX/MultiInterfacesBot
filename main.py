import asyncio
import importlib
import os
from typing import Any

from interfaces.base import Interface, BaseInterface

DIRECTORY = "interfaces"


def load_interfaces(base_interface: BaseInterface, directory=DIRECTORY):
    results = []

    # Проходим по всем папкам в указанной директории
    for root, dirs, files in os.walk(directory):
        # Ищем каталоги с __init__.py
        if '__init__.py' in files and root != directory:
            # Определяем модульное имя по пути
            module_name = os.path.relpath(root, os.getcwd()).replace(os.sep, '.')

            try:
                # Импортируем модуль
                module = importlib.import_module(module_name)

                # Проверяем наличие метода get
                if hasattr(module, 'get') and callable(getattr(module, 'get')):
                    # Вызываем метод get и добавляем результат в список
                    class_ = module.get()
                    results.append(class_(base_interface))

            except Exception as e:
                print(f"Ошибка при импорте модуля {module_name}: {e}")

    return results


async def async_start(interfaces: list[Interface]):
    coroutines = [i.start() for i in interfaces]
    await asyncio.gather(*coroutines)


if __name__ == '__main__':
    # Запуск ядра

    base = BaseInterface(None)
    interfaces: list[Any] = load_interfaces(base)
    # print(interfaces)

    coro = async_start(interfaces)
    for i in interfaces:
        # Костыль
        if i.__class__.__name__ == "TelegramInterface":
            with i.client:
                i.client.loop.run_until_complete(coro)
                break
    else:
        asyncio.run(coro)
