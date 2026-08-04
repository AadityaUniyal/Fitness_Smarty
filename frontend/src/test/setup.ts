import '@testing-library/jest-dom/vitest';
import React from 'react';
import { vi } from 'vitest';

class MockIntersectionObserver {
  observe() {}
  disconnect() {}
  unobserve() {}
}

class MockResizeObserver {
  observe() {}
  disconnect() {}
  unobserve() {}
}

if (!(globalThis as any).IntersectionObserver) {
  (globalThis as any).IntersectionObserver = MockIntersectionObserver as any;
}

if (!(globalThis as any).ResizeObserver) {
  (globalThis as any).ResizeObserver = MockResizeObserver as any;
}

vi.mock('recharts', async () => {
  const actual = await vi.importActual<any>('recharts');
  const ResponsiveContainer = ({ children }: { children?: React.ReactNode }) =>
    React.createElement('div', { 'data-testid': 'responsive-container' }, children);

  return {
    ...actual,
    ResponsiveContainer,
  };
});
