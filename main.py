import asyncio
import os
import threading
from typing import Any

import base
from base import BaseInterface, Interface

DIRECTORY = "interfaces"


def get_interfaces(base: BaseInterface):
    result = []
    dirs = os.listdir(os.path.join(os.getcwd(), DIRECTORY))
    for i in dirs:
        if i.endswith(".py") and i != "__init__.py":
            module_name = i[:-3]
            try:
                module = __import__(f"{DIRECTORY}.{module_name}", fromlist=[''])
                if hasattr(module, 'get'):
                    interface = module.get()
                    if hasattr(interface, "__init__"):
                        result.append(interface(base))
            except ImportError as e:
                continue
    return result


async def async_start(interfaces: list[Interface]):
    coroutines = [i.start() for i in interfaces]
    await asyncio.gather(*coroutines)


if __name__ == '__main__':
    # Запуск ядра

    base_ = base.BaseInterface(None)
    interfaces: list[Any] = get_interfaces(base_)
    print(interfaces)

    coro = async_start(interfaces)
    for i in interfaces:
        if i.__class__.__name__ == "TelegramInterface":
            with i.client:
                i.client.loop.run_until_complete(coro)
                break
    else:
        asyncio.run(coro)
