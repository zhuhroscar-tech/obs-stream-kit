(function (root) {
  "use strict";
  var MODES = ["starting", "brb", "ending", "privacy", "bg"];

  function formatClock(ms) {
    var total = Math.max(0, Math.ceil(ms / 1000));
    var m = Math.floor(total / 60);
    var s = total % 60;
    return m + ":" + String(s).padStart(2, "0");
  }

  function remainingMs(startedAt, durationMs, now) {
    return Math.max(0, startedAt + durationMs - now);
  }

  function rotateIndex(count, now, periodMs) {
    if (count <= 0) return -1;
    return Math.floor(now / periodMs) % count;
  }

  function normalizeMode(value) {
    return MODES.indexOf(value) >= 0 ? value : "starting";
  }

  var api = { formatClock: formatClock, remainingMs: remainingMs, rotateIndex: rotateIndex, normalizeMode: normalizeMode };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.KitLib = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
