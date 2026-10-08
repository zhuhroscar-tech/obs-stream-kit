from __future__ import annotations

from .applier import ObsError


class ObsClient:
    """Thin adapter: raw obs-websocket v5 request names in, response dicts out."""

    def __init__(self, host: str, port: int, password: str):
        import obsws_python as obs
        self._cl = obs.ReqClient(host=host, port=port, password=password, timeout=10)

    def call(self, req: str, data: dict | None = None) -> dict:
        from obsws_python.error import OBSSDKRequestError
        try:
            return self._cl.send(req, data or None, raw=True) or {}
        except OBSSDKRequestError as e:
            raise ObsError(e.code, str(e)) from e
