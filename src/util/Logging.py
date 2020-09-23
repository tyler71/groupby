import logging

from functools import wraps

log_levels = {
    0: None,
    5: "DEBUG",
    4: "INFO",
    3: "WARNING",
    2: "ERROR",
    1: "CRITICAL"
}

log = logging.getLogger(__name__)


def func_call(func):
    ''' Takes func and logs its call as DEBUG '''

    @wraps(func)
    def wrapper_func(*args, **kwargs):
        result = func(*args, **kwargs)
        log.debug('function({args} {kwargs}) -> {result}'.format(
            function=func.__qualname__,
            args=args,
            kwargs=kwargs,
            result=result))
        return result
    return wrapper_func
