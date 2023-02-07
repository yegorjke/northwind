import pytest
from fastapi import FastAPI

from northwind.main import create_app


def test_create_app():
    app = create_app()
    assert isinstance(app, FastAPI)
    assert len(app.router.routes)
    print(app.router.routes)
