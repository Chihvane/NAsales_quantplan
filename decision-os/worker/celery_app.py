from __future__ import annotations

try:
    from celery import Celery
except ModuleNotFoundError:  # pragma: no cover
    class Celery:  # type: ignore
        def __init__(self, *args, **kwargs) -> None:
            self.args = args
            self.kwargs = kwargs

        def task(self, func=None, **_kwargs):
            if func is None:
                def decorator(inner):
                    return inner
                return decorator
            return func


celery_app = Celery("decision_os")
