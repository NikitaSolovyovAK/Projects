import time
from logger import logger
from functools import wraps


def log_action(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Вызов функции {func.__name__} с args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"Результат {func.__name__}: {result}")
            return result
        except Exception as e:
            logger.error(f"Ошибка в {func.__name__}: {e}")
            raise
    return wrapper


def timed(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            start = time.perf_counter()
            result = func(*args, **kwargs)
            end = time.perf_counter()
            elapsed = end - start
            logger.info(f"Время работы {func.__name__}: {elapsed:.4f} сек")
            return result
        except Exception as e:
            logger.error(f"Ошибка в {func.__name__}: {e}")
            raise
    return wrapper
