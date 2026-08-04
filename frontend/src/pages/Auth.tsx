import { Navigate } from 'react-router-dom';

/**
 * Auth page — redirects to the login page.
 * The actual authentication UI lives in LoginPage.tsx.
 */
export default function Auth() {
  return <Navigate to="/" replace />;
}
