import "@testing-library/jest-dom";

process.env.NEXT_PUBLIC_API_URL = "http://localhost:8000";
process.env.NEXT_PUBLIC_SUPABASE_URL = "https://example.supabase.co";
process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = "supabase-anon-key";
process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY = "pk_test_123";

Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => undefined,
    removeListener: () => undefined,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
    dispatchEvent: () => false,
  }),
});

Object.defineProperty(navigator, "clipboard", {
  writable: true,
  value: {
    writeText: jest.fn(),
  },
});

Element.prototype.scrollIntoView = jest.fn();

// Prevent accidental real network requests during tests.
// Tests should explicitly mock network calls (MSW or jest mocks).
const networkErrorMessage =
  "Network requests are disabled during tests. Mock fetch/axios or use MSW.";

const throwNetworkError = () =>
  Promise.reject(new Error(networkErrorMessage));

;(global as any).fetch = jest.fn().mockImplementation(() => throwNetworkError());
(window as any).fetch = (global as any).fetch;

// If code uses XMLHttpRequest directly, make it fail fast as well.
class _XHRStub {
  open() {
    /* noop */
  }
  send() {
    throw new Error(networkErrorMessage);
  }
}

(window as any).XMLHttpRequest = _XHRStub;
