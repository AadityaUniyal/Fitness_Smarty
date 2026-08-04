import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import DailyChecklist from './DailyChecklist';

const mockTasks = [
  { id: 1, title: 'Drink Water', category: 'hydration', is_completed: false, priority: 1 },
  { id: 2, title: 'Morning Run', category: 'exercise', is_completed: true, priority: 2 },
];

describe('DailyChecklist Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('fetches and renders tasks correctly', async () => {
    const mockFetch = vi.fn().mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockTasks),
      } as Response)
    );
    vi.stubGlobal('fetch', mockFetch);

    render(<DailyChecklist userId={123} />);

    expect(screen.getByText(/Daily Checklist/i)).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('Drink Water')).toBeInTheDocument();
      expect(screen.getByText('Morning Run')).toBeInTheDocument();
    });
  });

  it('optimistically toggles a task and rolls back on failure', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const mockFetch = vi.fn()
      .mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockTasks),
        } as Response)
      )
      .mockImplementationOnce(() =>
        Promise.reject(new Error('Network error'))
      );
    vi.stubGlobal('fetch', mockFetch);

    render(<DailyChecklist userId={123} />);

    await waitFor(() => {
      expect(screen.getByText('Drink Water')).toBeInTheDocument();
    });

    const taskElement = screen.getByText('Drink Water');
    fireEvent.click(taskElement);

    // Verify optimistic state change (checked/line-through class)
    await waitFor(() => {
      expect(taskElement.className).toContain('line-through');
    });

    // Verify rollback state (unchecked/no line-through class)
    await waitFor(() => {
      expect(taskElement.className).not.toContain('line-through');
    });
    warnSpy.mockRestore();
  });

  it('allows adding a new task', async () => {
    const mockFetch = vi.fn()
      .mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockTasks),
        } as Response)
      )
      .mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({}),
        } as Response)
      )
      .mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve([...mockTasks, { id: 3, title: 'Meditate', category: 'mindful', is_completed: false }]),
        } as Response)
      );
    vi.stubGlobal('fetch', mockFetch);

    render(<DailyChecklist userId={123} />);

    await waitFor(() => {
      expect(screen.getByText('Drink Water')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText(/Add a custom task.../i);
    fireEvent.change(input, { target: { value: 'Meditate' } });

    // The add button has a Plus icon, find the button containing it or the sibling button next to input
    const buttons = screen.getAllByRole('button');
    const addButton = buttons.find(b => b.querySelector('svg'));
    expect(addButton).toBeDefined();

    if (addButton) {
      fireEvent.click(addButton);
    }

    await waitFor(() => {
      expect(screen.getByText('Meditate')).toBeInTheDocument();
    });
  });

  it('allows deleting a task', async () => {
    const mockFetch = vi.fn()
      .mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockTasks),
        } as Response)
      )
      .mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
        } as Response)
      );
    vi.stubGlobal('fetch', mockFetch);

    render(<DailyChecklist userId={123} />);

    await waitFor(() => {
      expect(screen.getByText('Drink Water')).toBeInTheDocument();
    });

    const deleteBtns = screen.getAllByRole('button');
    // The delete button is the button containing the X icon
    const deleteBtn = deleteBtns.find(btn => btn.querySelector('.lucide-x'));
    expect(deleteBtn).toBeDefined();

    if (deleteBtn) {
      fireEvent.click(deleteBtn);
      await waitFor(() => {
        expect(screen.queryByText('Drink Water')).toBeNull();
      });
    }
  });

  it('renders compact view correctly', async () => {
    const mockFetch = vi.fn().mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockTasks),
      } as Response)
    );
    vi.stubGlobal('fetch', mockFetch);

    render(<DailyChecklist userId={123} compact />);

    await waitFor(() => {
      expect(screen.getByText("Today's Progress")).toBeInTheDocument();
      expect(screen.getByText("Next:")).toBeInTheDocument();
      expect(screen.getByText("Drink Water")).toBeInTheDocument();
    });
  });
});
