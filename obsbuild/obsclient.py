from __future__ import annotations

from .applier import ObsError


class ObsClient:
    """Thin adapter: raw obs-websocket v5 request names in, response dicts out."""

    def __init__(self, host: str, port: int, password: str):
        import logging

        import obsws_python as obs
        # The library logs a traceback for every non-200 response; 600 (not found) is a normal
        # control-flow signal for us, so keep the output clean and rely on ObsError instead.
        logging.getLogger("obsws_python").setLevel(logging.CRITICAL)
        self._cl = obs.ReqClient(host=host, port=port, password=password, timeout=10)

    def call(self, req: str, data: dict | None = None) -> dict:
        from obsws_python.error import OBSSDKRequestError
        try:
            return self._cl.send(req, data or None, raw=True) or {}
        except OBSSDKRequestError as e:
            raise ObsError(e.code, str(e)) from e
