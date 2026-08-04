import { useMemo } from 'react';
import { useAuth } from '../contexts/AuthContext';

export function useCurrentUserId(defaultId = '1') {
  const { user } = useAuth();
  return useMemo(() => String(user?.id || defaultId), [user?.id, defaultId]);
}
