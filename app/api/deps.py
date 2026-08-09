from fastapi import Depends, Request

from app.api.auth import workspace_dep
from app.llm import Runtime


def runtime_dep(request: Request) -> Runtime:
    return request.app.state.runtime


def session_factory_dep(request: Request):
    return request.app.state.session_factory


def settings_dep(request: Request):
    return request.app.state.settings


def rate_limited_workspace_dep(
    request: Request, workspace_id: str = Depends(workspace_dep)
) -> str:
    """Resolve the workspace, then spend one of its tokens.

    Applied only to the endpoints that invoke models; reads are cheap and
    stay unthrottled.
    """
    request.app.state.rate_limiter.check(workspace_id)
    return workspace_id
