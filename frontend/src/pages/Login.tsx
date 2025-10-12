import React, { useState } from 'react';
import { api } from '../services/api';
import { useNavigate } from 'react-router-dom';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const res = await api.post<any>('/auth/login', { username, password });
      localStorage.setItem('auth_token', res.access_token);
      localStorage.setItem('refresh_token', res.refresh_token);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <form onSubmit={onSubmit} className="bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4 w-full max-w-sm">
        <h1 className="text-xl font-semibold mb-4">Login</h1>
        {error && <div className="text-red-500 text-sm mb-2">{error}</div>}
        <label className="block text-gray-700 text-sm font-bold mb-2">Username</label>
        <input className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 mb-3" value={username} onChange={e => setUsername(e.target.value)} />
        <label className="block text-gray-700 text-sm font-bold mb-2">Password</label>
        <input type="password" className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 mb-3" value={password} onChange={e => setPassword(e.target.value)} />
        <button type="submit" className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">Sign In</button>
      </form>
    </div>
  );
}
