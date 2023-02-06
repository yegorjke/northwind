from functools import partial
from typing import Any

import pytest

from northwind.utils import make_api_url, make_object_factory


class ATest:
    def __init__(self, a, b=None):
        self.a = a
        self.b = b


@pytest.mark.parametrize(["a"], [(None,), ("1",)])
def test_make_object_factory_passing_only_one_positional_argument(a):
    func = make_object_factory(ATest)
    o = func(a)

    assert isinstance(o, ATest)
    assert o.a == a
    assert o.b is None


@pytest.mark.parametrize(["b"], [(None,), ("1",)])
def test_make_object_factory_passing_only_one_keyword_argument_raises_type_error(b):
    func = make_object_factory(ATest)
    with pytest.raises(TypeError):
        func(b=b)


@pytest.mark.parametrize(["a", "b"], [(None, None), ("1", "2"), ("1", None)])
def test_make_object_factory_passing_both_positional_and_keyword_arguments(a, b):
    func = make_object_factory(ATest)
    o = func(a, b)

    assert isinstance(o, ATest)
    assert o.a == a
    assert o.b == b


@pytest.mark.parametrize(
    ["prefix", "path", "query", "expected"],
    [
        ("api", None, None, "api"),
        ("/api", None, None, "/api"),
        ("/api", [], {}, "/api"),
        ("/api", ["resource"], None, "/api/resource"),
        ("/api", ["resource", "1"], None, "/api/resource/1"),
        ("/api", ["resource", "1"], None, "/api/resource/1"),
        ("/api", ["resource", "1"], {"q": 1}, "/api/resource/1?q=1"),
        ("/api", ["resource", "1"], {"q": 1, "w": 2}, "/api/resource/1?q=1&w=2"),
        ("/api", None, {"q": 1}, "/api?q=1"),
        ("/api", None, {"q": 1, "w": 2}, "/api?q=1&w=2"),
    ],
)
def test_make_api_url(prefix: str, path: list[str], query: dict[str, Any], expected: str):
    factory = partial(make_api_url, prefix)

    if path:
        factory = partial(factory, *path)

    if query:
        factory = partial(factory, **query)

    url = factory()

    assert url == expected
