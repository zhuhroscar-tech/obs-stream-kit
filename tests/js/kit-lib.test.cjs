const test = require("node:test");
const assert = require("node:assert/strict");
const lib = require("../../overlays/lib/kit-lib.js");

test("formatClock rounds partial seconds up and never goes negative", () => {
  assert.equal(lib.formatClock(299001), "5:00");
  assert.equal(lib.formatClock(59000), "0:59");
  assert.equal(lib.formatClock(0), "0:00");
  assert.equal(lib.formatClock(-5), "0:00");
});

test("remainingMs counts down to zero", () => {
  assert.equal(lib.remainingMs(1000, 5000, 3000), 3000);
  assert.equal(lib.remainingMs(1000, 5000, 9000), 0);
});

test("rotateIndex cycles through items by period", () => {
  assert.equal(lib.rotateIndex(3, 0, 8000), 0);
  assert.equal(lib.rotateIndex(3, 8000, 8000), 1);
  assert.equal(lib.rotateIndex(3, 24000, 8000), 0);
  assert.equal(lib.rotateIndex(0, 5000, 8000), -1);
});

test("normalizeMode accepts known modes and defaults to starting", () => {
  for (const m of ["starting", "brb", "ending", "privacy", "bg"]) assert.equal(lib.normalizeMode(m), m);
  assert.equal(lib.normalizeMode("evil"), "starting");
  assert.equal(lib.normalizeMode(undefined), "starting");
});
