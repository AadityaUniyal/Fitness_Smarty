import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import LoginPage from './LoginPage';
import { AuthProvider } from '../contexts/AuthContext';
import { BrowserRouter } from 'react-router-dom';

// Mock context and useNavigate
const mockNavigate = vi.fn();
const mockLogin = vi.fn();
const mockRegister = vi.fn();
const mockGoogle = vi.fn();
const mockApple = vi.fn();
let mockAuthState: any = {
  user: null,
  loading: false,
  isAuthenticated: false,
};
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});
vi.mock('../contexts/AuthContext', async () => {
  const actual = await vi.importActual<typeof import('../contexts/AuthContext')>('../contexts/AuthContext');
  return {
    ...actual,
    useAuth: () => ({
      ...mockAuthState,
      login: mockLogin,
      register: mockRegister,
      googleLogin: mockGoogle,
      appleLogin: mockApple,
      logout: vi.fn(),
      updateProfile: vi.fn(),
      refreshUser: vi.fn(),
    }),
  };
});

describe('LoginPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    mockAuthState = { user: null, loading: false, isAuthenticated: false };
  });

  it('renders login form elements by default', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </BrowserRouter>
    );

    expect(screen.getByPlaceholderText(/Email Address/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Access Hub/i })).toBeInTheDocument();
  });

  it('toggles to registration form', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </BrowserRouter>
    );

    const toggleBtn = screen.getByRole('button', { name: /Create Account/i });
    fireEvent.click(toggleBtn);

    expect(screen.getByPlaceholderText(/Full Name/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Register/i })).toBeInTheDocument();
  });

  it('allows guest access', async () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </BrowserRouter>
    );

    const guestBtn = screen.getByText(/Guest Mode/i);
    fireEvent.click(guestBtn);

    await waitFor(() => {
      const guestUser = JSON.parse(localStorage.getItem('smarty_user') || '{}');
      expect(guestUser.email).toBe('guest@smarty.ai');
      expect(mockNavigate).toHaveBeenCalledWith('/onboarding');
    });
  });

  it('submits login credentials to auth service', async () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </BrowserRouter>
    );

    fireEvent.change(screen.getByPlaceholderText(/Email Address/i), { target: { value: 'demo@example.com' } });
    fireEvent.change(screen.getByPlaceholderText(/Password/i), { target: { value: 'secret123' } });
    fireEvent.click(screen.getByRole('button', { name: /Access Hub/i }));

    await waitFor(() => expect(mockLogin).toHaveBeenCalledWith('demo@example.com', 'secret123'));
    expect(mockNavigate).toHaveBeenCalledWith('/onboarding');
  });

  it('shows an error when login fails', async () => {
    mockLogin.mockRejectedValueOnce(new Error('Invalid credentials'));

    render(
      <BrowserRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </BrowserRouter>
    );

    fireEvent.change(screen.getByPlaceholderText(/Email Address/i), { target: { value: 'bad@example.com' } });
    fireEvent.change(screen.getByPlaceholderText(/Password/i), { target: { value: 'wrongpass' } });
    fireEvent.click(screen.getByRole('button', { name: /Access Hub/i }));

    await waitFor(() => expect(screen.getByText(/Invalid credentials/i)).toBeInTheDocument());
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('disables the submit button while auth is loading', async () => {
    mockAuthState = { user: null, loading: true, isAuthenticated: false };

    render(
      <BrowserRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </BrowserRouter>
    );

    expect(screen.getByRole('button', { name: /Syncing.../i })).toBeDisabled();
  });

  it('routes admins to the admin dashboard after auth', async () => {
    mockAuthState = {
      user: { id: '1', email: 'admin@smarty.ai', is_admin: true },
      loading: false,
      isAuthenticated: true,
    };

    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    );

    fireEvent.change(screen.getByPlaceholderText(/Email Address/i), { target: { value: 'admin@smarty.ai' } });
    fireEvent.change(screen.getByPlaceholderText(/Password/i), { target: { value: 'secret123' } });
    fireEvent.click(screen.getByRole('button', { name: /Access Hub/i }));

    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/admin'));
  });

  it('supports register flow and blocks submit until disclaimer is accepted', async () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </BrowserRouter>
    );

    fireEvent.click(screen.getByRole('button', { name: /Create Account/i }));
    fireEvent.change(screen.getByPlaceholderText(/Full Name/i), { target: { value: 'New User' } });
    fireEvent.change(screen.getByPlaceholderText(/Email Address/i), { target: { value: 'new@example.com' } });
    fireEvent.change(screen.getByPlaceholderText(/Password/i), { target: { value: 'StrongPass123' } });

    const registerBtn = screen.getByRole('button', { name: /Register/i });
    expect(registerBtn).toBeDisabled();

    fireEvent.click(screen.getByLabelText(/I understand that Smarty AI provides fitness and nutritional guides/i));
    expect(registerBtn).not.toBeDisabled();

    fireEvent.click(registerBtn);
    await waitFor(() => expect(mockRegister).toHaveBeenCalledWith('new@example.com', 'StrongPass123', 'New User'));
  });
});
