import time
import functools
import logging

def log_execution_time(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"DEBUG: {func.__name__} executed in {end - start:.4f}s")
        return result
    return wrapper