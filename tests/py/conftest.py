import pytest
from obsbuild.applier import ObsError


class FakeObs:
    """Minimal in-memory obs-websocket. Records every call as (requestType, data)."""

    def __init__(self):
        self.scenes = {}            # scene -> {source: sceneItemId}
        self.inputs = {}            # name -> (kind, settings)
        self.filters = {}           # source -> {filterName: (kind, settings)}
        self.collections = ["Untitled"]
        self.current_collection = "Untitled"
        self.profiles = ["Untitled"]
        self.current_profile = "Untitled"
        self.special = {"desktop1": None, "desktop2": None, "mic1": None, "mic2": None, "mic3": None, "mic4": None}
        self.video = {"baseWidth": 1920, "baseHeight": 1080, "outputWidth": 1280, "outputHeight": 720,
                      "fpsNumerator": 60, "fpsDenominator": 1}
        self.kinds = {"input": ["source-clone", "browser_source"], "filter": ["obs_composite_blur"],
                      "transition": ["move_transition", "fade_transition"]}
        self.calls = []
        self._next = 1

    def call(self, req, data=None):
        data = data or {}
        self.calls.append((req, data))
        handler = getattr(self, "_" + req, None)
        return (handler(data) if handler else None) or {}

    def _add(self, scene, source):
        iid = self._next
        self._next += 1
        self.scenes.setdefault(scene, {})[source] = iid
        return iid

    def _GetSceneList(self, d): return {"scenes": [{"sceneName": n} for n in self.scenes]}
    def _CreateScene(self, d): self.scenes[d["sceneName"]] = {}
    def _GetInputList(self, d): return {"inputs": [{"inputName": n} for n in self.inputs]}

    def _CreateInput(self, d):
        self.inputs[d["inputName"]] = (d["inputKind"], dict(d["inputSettings"]))
        return {"sceneItemId": self._add(d["sceneName"], d["inputName"])}

    def _SetInputSettings(self, d): self.inputs[d["inputName"]][1].update(d["inputSettings"])

    def _GetSceneItemId(self, d):
        try:
            return {"sceneItemId": self.scenes[d["sceneName"]][d["sourceName"]]}
        except KeyError:
            raise ObsError(600, "No source was found")

    def _CreateSceneItem(self, d): return {"sceneItemId": self._add(d["sceneName"], d["sourceName"])}

    def _GetSceneItemList(self, d):
        return {"sceneItems": [{"sourceName": s, "sceneItemId": i} for s, i in self.scenes[d["sceneName"]].items()]}

    def _RemoveSceneItem(self, d):
        items = self.scenes[d["sceneName"]]
        for s, i in list(items.items()):
            if i == d["sceneItemId"]:
                del items[s]
    def _GetSourceFilterList(self, d): return {"filters": [{"filterName": n} for n in self.filters.get(d["sourceName"], {})]}

    def _CreateSourceFilter(self, d):
        self.filters.setdefault(d["sourceName"], {})[d["filterName"]] = (d["filterKind"], d.get("filterSettings", {}))

    def _GetInputPropertiesListPropertyItems(self, d):
        return {"propertyItems": [
            {"itemName": "oscar Camera", "itemValue": "UUID-1", "itemEnabled": True},
            {"itemName": "oscar Microphone", "itemValue": "MIC-1", "itemEnabled": True}]}

    def _GetSceneCollectionList(self, d):
        return {"sceneCollections": list(self.collections), "currentSceneCollectionName": self.current_collection}

    def _CreateSceneCollection(self, d):
        self.collections.append(d["sceneCollectionName"])
        self.current_collection = d["sceneCollectionName"]

    def _SetCurrentSceneCollection(self, d): self.current_collection = d["sceneCollectionName"]
    def _GetProfileList(self, d): return {"profiles": list(self.profiles), "currentProfileName": self.current_profile}

    def _CreateProfile(self, d):
        self.profiles.append(d["profileName"])
        self.current_profile = d["profileName"]

    def _SetCurrentProfile(self, d): self.current_profile = d["profileName"]
    def _GetVersion(self, d): return {"obsVersion": "32.2.2"}
    def _GetInputKindList(self, d): return {"inputKinds": self.kinds["input"]}
    def _GetSourceFilterKindList(self, d): return {"sourceFilterKinds": self.kinds["filter"]}
    def _GetTransitionKindList(self, d): return {"transitionKinds": self.kinds["transition"]}
    def _GetSpecialInputs(self, d): return dict(self.special)
    def _GetVideoSettings(self, d): return dict(self.video)


@pytest.fixture
def fake():
    return FakeObs()
