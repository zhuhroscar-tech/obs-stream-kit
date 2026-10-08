"""Idempotent operations against obs-websocket v5. `client.call(requestType, data) -> dict`."""
from __future__ import annotations

from .layout import Item

ALIGN_TOP_LEFT = 5          # OBS_ALIGN_LEFT (1) | OBS_ALIGN_TOP (4)
NOT_FOUND = 600             # obs-websocket ResourceNotFound


class ObsError(Exception):
    def __init__(self, code: int, message: str = ""):
        super().__init__(f"{code}: {message}")
        self.code = code


class Applier:
    def __init__(self, client):
        self.c = client
        self.log: list[str] = []

    def ensure_collection(self, name: str) -> None:
        r = self.c.call("GetSceneCollectionList")
        if name not in r["sceneCollections"]:
            self.c.call("CreateSceneCollection", {"sceneCollectionName": name})
            self.log.append(f"+ collection {name}")
        elif r["currentSceneCollectionName"] != name:
            self.c.call("SetCurrentSceneCollection", {"sceneCollectionName": name})

    def ensure_profile(self, name: str) -> None:
        r = self.c.call("GetProfileList")
        if name not in r["profiles"]:
            self.c.call("CreateProfile", {"profileName": name})
            self.log.append(f"+ profile {name}")
        elif r["currentProfileName"] != name:
            self.c.call("SetCurrentProfile", {"profileName": name})

    def ensure_scene(self, name: str) -> None:
        if name not in {s["sceneName"] for s in self.c.call("GetSceneList")["scenes"]}:
            self.c.call("CreateScene", {"sceneName": name})
            self.log.append(f"+ scene {name}")

    def ensure_input(self, scene: str, name: str, kind: str, settings: dict) -> None:
        if name in {i["inputName"] for i in self.c.call("GetInputList")["inputs"]}:
            self.c.call("SetInputSettings", {"inputName": name, "inputSettings": settings, "overlay": True})
        else:
            self.c.call("CreateInput", {"sceneName": scene, "inputName": name, "inputKind": kind,
                                        "inputSettings": settings, "sceneItemEnabled": True})
            self.log.append(f"+ input {name}")

    def ensure_item(self, scene: str, source: str) -> int:
        try:
            return self.c.call("GetSceneItemId", {"sceneName": scene, "sourceName": source})["sceneItemId"]
        except ObsError as e:
            if e.code != NOT_FOUND:
                raise
        self.log.append(f"+ item {scene} / {source}")
        return self.c.call("CreateSceneItem", {"sceneName": scene, "sourceName": source})["sceneItemId"]

    def place(self, scene: str, item_id: int, item: Item) -> None:
        b = item.box
        self.c.call("SetSceneItemTransform", {"sceneName": scene, "sceneItemId": item_id, "sceneItemTransform": {
            "positionX": b.x, "positionY": b.y, "alignment": ALIGN_TOP_LEFT, "rotation": 0.0,
            "boundsType": "OBS_BOUNDS_SCALE_INNER", "boundsAlignment": item.align,
            "boundsWidth": b.w, "boundsHeight": b.h,
            "cropLeft": 0, "cropRight": 0, "cropTop": 0, "cropBottom": 0}})
        self.c.call("SetSceneItemEnabled", {"sceneName": scene, "sceneItemId": item_id, "sceneItemEnabled": item.visible})

    def build_scene(self, scene: str, items, prune: bool = False) -> None:
        self.ensure_scene(scene)
        ids = []
        for it in items:
            iid = self.ensure_item(scene, it.source)
            self.place(scene, iid, it)
            ids.append(iid)
        if prune:
            for si in self.c.call("GetSceneItemList", {"sceneName": scene})["sceneItems"]:
                if si["sceneItemId"] not in ids:
                    self.c.call("RemoveSceneItem", {"sceneName": scene, "sceneItemId": si["sceneItemId"]})
                    self.log.append(f"- item {scene} / {si['sourceName']}")
        for index, iid in enumerate(ids):
            self.c.call("SetSceneItemIndex", {"sceneName": scene, "sceneItemId": iid, "sceneItemIndex": index})

    def ensure_filter(self, source: str, name: str, kind: str, settings: dict) -> None:
        names = {f["filterName"] for f in self.c.call("GetSourceFilterList", {"sourceName": source})["filters"]}
        if name in names:
            self.c.call("SetSourceFilterSettings", {"sourceName": source, "filterName": name,
                                                    "filterSettings": settings, "overlay": True})
        else:
            self.c.call("CreateSourceFilter", {"sourceName": source, "filterName": name,
                                               "filterKind": kind, "filterSettings": settings})
            self.log.append(f"+ filter {source} / {name}")

    def select_device(self, input_name: str, prop: str, wanted: str) -> None:
        items = self.c.call("GetInputPropertiesListPropertyItems",
                            {"inputName": input_name, "propertyName": prop})["propertyItems"]
        for it in items:
            if it["itemName"] == wanted:
                self.c.call("SetInputSettings", {"inputName": input_name,
                                                 "inputSettings": {prop: it["itemValue"]}, "overlay": True})
                return
        choices = ", ".join(i["itemName"] for i in items)
        raise ValueError(f"{wanted!r} not found for {input_name}.{prop}; available: {choices}")
