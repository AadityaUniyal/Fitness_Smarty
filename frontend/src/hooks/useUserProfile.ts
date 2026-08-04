import { useEffect, useState } from 'react';
import { AuthAPI } from '../services/apiService';
import { useAuth } from '../contexts/AuthContext';

export function useUserProfile() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<any>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    const load = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem('smarty_access_token');
        if (token) {
          const remote = await AuthAPI.getCurrentUser(token);
          if (!active) return;
          setProfile(remote);
        } else {
          setProfile(user || {});
        }
      } catch {
        setProfile(user || {});
      } finally {
        if (active) setLoading(false);
      }
    };
    load();
    return () => { active = false; };
  }, [user?.id]);

  return { profile, loading, user };
}
