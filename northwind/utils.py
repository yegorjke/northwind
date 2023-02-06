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


def make_api_url(prefix: str = "/", *args, **kwargs) -> str:
    url = f"{prefix}"

    if args:
        path = "/".join(args)
        url = f"{url}/{path}"

    if kwargs:
        query_params = "&".join([f"{k}={v}" for k, v in kwargs.items()])
        url = f"{url}?{query_params}"

    return url
