import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import ErrorBoundary from './ErrorBoundary';

const ThrowingChild = () => {
  throw new Error('smoke failure');
};

describe('ErrorBoundary', () => {
  it('renders a fallback when a child throws', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <ThrowingChild />
      </ErrorBoundary>
    );

    expect(screen.getByText(/Neural Link Disrupted/i)).toBeInTheDocument();
    expect(screen.getByText('smoke failure')).toBeInTheDocument();

    consoleError.mockRestore();
  });
});
