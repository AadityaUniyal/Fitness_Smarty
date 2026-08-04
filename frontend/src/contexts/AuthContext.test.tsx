import { act, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, beforeEach, vi } from 'vitest';
import React from 'react';
import { AuthProvider, useAuth } from './AuthContext';
import { AuthAPI } from '../services/apiService';

vi.mock('../services/apiService', () => ({
  AuthAPI: {
    login: vi.fn(),
    register: vi.fn(),
    getCurrentUser: vi.fn(),
    refreshToken: vi.fn(),
    logout: vi.fn(),
    updateProfile: vi.fn(),
    googleLogin: vi.fn(),
    appleLogin: vi.fn(),
  },
}));

const Consumer = () => {
  const { user, login, register, logout, refreshUser, isAuthenticated } = useAuth();
  return (
    <div>
      <div data-testid="auth-state">{isAuthenticated ? 'yes' : 'no'}</div>
      <div data-testid="user-email">{user?.email || ''}</div>
      <button onClick={() => login('test@example.com', 'secret')}>login</button>
      <button onClick={() => register('new@example.com', 'secret', 'New User')}>register</button>
      <button onClick={() => refreshUser()}>refresh</button>
      <button onClick={() => logout()}>logout</button>
    </div>
  );
};

describe('AuthProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('stores login tokens and user data', async () => {
    vi.mocked(AuthAPI.login).mockResolvedValueOnce({ access_token: 'access-1', refresh_token: 'refresh-1', token_type: 'bearer' });
    vi.mocked(AuthAPI.getCurrentUser).mockResolvedValueOnce({ id: '7', email: 'test@example.com' });

    render(<AuthProvider><Consumer /></AuthProvider>);
    await act(async () => {
      screen.getByText('login').click();
    });

    await waitFor(() => expect(localStorage.getItem('smarty_access_token')).toBe('access-1'));
    await waitFor(() => expect(screen.getByTestId('auth-state')).toHaveTextContent('yes'));
    expect(screen.getByTestId('user-email')).toHaveTextContent('test@example.com');
  });

  it('stores registration tokens and user data', async () => {
    vi.mocked(AuthAPI.register).mockResolvedValueOnce({ access_token: 'access-2', refresh_token: 'refresh-2', token_type: 'bearer' });
    vi.mocked(AuthAPI.getCurrentUser).mockResolvedValueOnce({ id: '8', email: 'new@example.com' });

    render(<AuthProvider><Consumer /></AuthProvider>);
    await act(async () => {
      screen.getByText('register').click();
    });

    await waitFor(() => expect(localStorage.getItem('smarty_refresh_token')).toBe('refresh-2'));
    expect(screen.getByTestId('user-email')).toHaveTextContent('new@example.com');
  });

  it('logs out and clears stored auth data', async () => {
    vi.mocked(AuthAPI.login).mockResolvedValueOnce({ access_token: 'access-3', refresh_token: 'refresh-3', token_type: 'bearer' });
    vi.mocked(AuthAPI.getCurrentUser).mockResolvedValueOnce({ id: '10', email: 'logout@example.com' });
    vi.mocked(AuthAPI.logout).mockResolvedValueOnce({ message: 'ok' });

    render(<AuthProvider><Consumer /></AuthProvider>);
    await act(async () => {
      screen.getByText('login').click();
    });

    await waitFor(() => expect(localStorage.getItem('smarty_access_token')).toBe('access-3'));
    await act(async () => {
      screen.getByText('logout').click();
    });

    await waitFor(() => expect(AuthAPI.logout).toHaveBeenCalledWith('access-3'));
    expect(localStorage.getItem('smarty_access_token')).toBeNull();
    expect(localStorage.getItem('smarty_refresh_token')).toBeNull();
  });
});
