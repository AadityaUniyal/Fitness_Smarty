import { useState, useCallback } from 'react';

export interface APIState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export interface UseAPIReturn<T, Args extends any[]> {
  data: T | null;
  loading: boolean;
  error: string | null;
  execute: (...args: Args) => Promise<T | null>;
  reset: () => void;
}

/**
 * Custom hook for managing API call state
 * Provides loading, error, and data states with automatic error handling
 */
export function useAPI<T, Args extends any[] = []>(
  apiFunction: (...args: Args) => Promise<T>
): UseAPIReturn<T, Args> {
  const [state, setState] = useState<APIState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const execute = useCallback(
    async (...args: Args): Promise<T | null> => {
      setState({ data: null, loading: true, error: null });

      try {
        const result = await apiFunction(...args);
        setState({ data: result, loading: false, error: null });
        return result;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'An error occurred';
        setState({ data: null, loading: false, error: errorMessage });
        return null;
      }
    },
    [apiFunction]
  );

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return {
    ...state,
    execute,
    reset,
  };
}

/**
 * Hook for managing multiple API calls with combined loading state
 */
export function useMultipleAPI() {
  const [loadingStates, setLoadingStates] = useState<Record<string, boolean>>({});
  const [errors, setErrors] = useState<Record<string, string | null>>({});

  const isLoading = Object.values(loadingStates).some(loading => loading);
  const hasErrors = Object.values(errors).some(error => error !== null);

  const executeAPI = useCallback(
    async <T,>(key: string, apiFunction: () => Promise<T>): Promise<T | null> => {
      setLoadingStates(prev => ({ ...prev, [key]: true }));
      setErrors(prev => ({ ...prev, [key]: null }));

      try {
        const result = await apiFunction();
        setLoadingStates(prev => ({ ...prev, [key]: false }));
        return result;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'An error occurred';
        setLoadingStates(prev => ({ ...prev, [key]: false }));
        setErrors(prev => ({ ...prev, [key]: errorMessage }));
        return null;
      }
    },
    []
  );

  const reset = useCallback((key?: string) => {
    if (key) {
      setLoadingStates(prev => ({ ...prev, [key]: false }));
      setErrors(prev => ({ ...prev, [key]: null }));
    } else {
      setLoadingStates({});
      setErrors({});
    }
  }, []);

  return {
    isLoading,
    hasErrors,
    loadingStates,
    errors,
    executeAPI,
    reset,
  };
}
