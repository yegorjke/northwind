from functools import partial
from typing import Type, TypeVar

T = TypeVar("T")


def make_object_factory(c: Type[T], *defaults, **kwdefaults):
    def factory(*args, batch: int | None = None, **kwargs) -> T:
        # TODO: implement overriding defaults values

        if batch is not None:
            if batch < 1:
                raise ValueError("'batch' must be greater than 1")

            return [c(*args, **kwargs) for _ in range(batch)]
        else:
            return c(*args, **kwargs)

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
