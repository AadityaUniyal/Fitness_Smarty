import { useMemo } from 'react';
import { useAuth } from '../contexts/AuthContext';

export function useCurrentUserId(providedId?: string | number, defaultId = '1') {
  const { user } = useAuth();
  return useMemo(() => String(providedId || user?.id || defaultId), [providedId, user?.id, defaultId]);
}
