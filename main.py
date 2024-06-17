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


def start_interfaces(interfaces: list[Interface]) -> list[threading.Thread]:
    processes = []
    for i in interfaces:
        thread = threading.Thread(target=i.start)
        processes.append(thread)
        thread.start()
    return processes


if __name__ == '__main__':
    # Запуск ядра

    base_ = base.BaseInterface(None)
    interfaces: list[Any] = get_interfaces(base_)
    interfaces[0].start()

    # # Запускаем интерфейсы
    # threads = start_interfaces(base_, interfaces)
    #
    # # Ждем завершения всех потоков
    # for thread in threads:
    #     thread.join()
