import "@testing-library/jest-dom/vitest";

// jsdom has no ResizeObserver, but Recharts' <ResponsiveContainer> needs one
// to measure its parent. A no-op stub is enough for tests -- they only
// assert on rendered content, not real layout.
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}

window.ResizeObserver = window.ResizeObserver ?? ResizeObserverStub;

// jsdom is also missing a few APIs Radix UI's Select/Popper primitives call
// (pointer capture, scrollIntoView) -- no-op stubs are enough since tests
// only assert on rendered content, never real pointer/scroll behavior.
if (!Element.prototype.hasPointerCapture) {
  Element.prototype.hasPointerCapture = () => false;
}
if (!Element.prototype.setPointerCapture) {
  Element.prototype.setPointerCapture = () => {};
}
if (!Element.prototype.releasePointerCapture) {
  Element.prototype.releasePointerCapture = () => {};
}
if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {};
}
