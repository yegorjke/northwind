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


@pytest.mark.parametrize(["n"], [(1,), (3,)])
def test_make_object_factory_passing_batch_argument_to_factory(n: int):
    func = make_object_factory(ATest)
    objects: list = func("a", "b", batch=n)

    assert isinstance(objects, list)
    assert len(objects) == n
    assert isinstance(objects[0], ATest)


@pytest.mark.parametrize(["n"], [(0,), (-1,)])
def test_make_object_factory_passing_incorrect_batch_argument_raises_value_error(n: int):
    func = make_object_factory(ATest)
    with pytest.raises(ValueError):
        func("a", "b", batch=n)


@pytest.mark.parametrize(["default_a", "b"], [("1", "1")])
def test_make_object_factory_with_default_positional_arg(default_a, b):
    func = make_object_factory(ATest, default_a)
    o = func(b=b)

    assert isinstance(o, ATest)
    assert o.a == default_a
    assert o.b == b


@pytest.mark.parametrize(["a", "default_b"], [("1", "1")])
def test_make_object_factory_with_default_keyword_arg(a, default_b):
    func = make_object_factory(ATest, b=default_b)
    o = func(a)

    assert isinstance(o, ATest)
    assert o.a == a
    assert o.b == default_b


@pytest.mark.xfail
@pytest.mark.parametrize(["default_a", "default_b", "override_a", "override_b"], [("1", "1", "2", "2")])
def test_make_object_factory_override_passed_default_values(default_a, default_b, override_a, override_b):
    # TODO: implement overriding defaults values
    func = make_object_factory(ATest, default_a, b=default_b)
    o = func(override_a, b=override_b)

    assert isinstance(o, ATest)
    assert o.a == override_a
    assert o.b == override_b


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
        ("/api", None, {"q": None, "w": None}, "/api"),
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
