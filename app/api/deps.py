from fastapi import Request

from app.llm import Runtime


def runtime_dep(request: Request) -> Runtime:
    return request.app.state.runtime


def session_factory_dep(request: Request):
    return request.app.state.session_factory
