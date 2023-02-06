from functools import partial
from typing import Type, TypeVar

T = TypeVar("T")


def make_object_factory(c: Type[T], *defaults, **kwdefaults):
    def factory(*args, batch: int = 1, **kwargs) -> T:
        if batch < 1:
            raise ValueError("'batch' must be greater than 1")
        if batch == 1:
            return c(*args, **kwargs)
        else:
            return [c(*args, **kwargs) for _ in range(batch)]

    if defaults:
        factory = partial(factory, *defaults)

    if kwdefaults:
        factory = partial(factory, **kwdefaults)

    return factory


def make_api_url(prefix: str = "/", *path, **query) -> str:
    url = f"{prefix}"

    if path:
        url = f"{url}/{'/'.join(path)}"

    if query:
        url = f"{url}?{'&'.join([f'{k}={v}' for k, v in query.items()])}"

    return url
