import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { loginRequest } from '../api';

const LoginPage = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (username && password) {
      setIsLoading(true);
      try {
        const response = await loginRequest(username, password);
        const tokenData = response.data;
        const token = typeof tokenData === 'object' && tokenData.access_token ? tokenData.access_token : tokenData;
        
        localStorage.setItem('token', token);
        if (typeof tokenData === 'object') {
          if (tokenData.refresh_token) localStorage.setItem('refreshToken', tokenData.refresh_token);
          if (tokenData.id_token) {
            localStorage.setItem('idToken', tokenData.id_token);
            try {
              const payload = JSON.parse(atob(tokenData.id_token.split('.')[1]));
              if (payload.preferred_username || payload.name || payload.sub) {
                localStorage.setItem('username', payload.preferred_username || payload.name || payload.sub);
              }
            } catch (e) {
              localStorage.setItem('username', username);
            }
          } else {
            localStorage.setItem('username', username);
          }
        } else {
          localStorage.setItem('username', username);
        }
        
        if (onLogin) onLogin();
        navigate('/chat');
      } catch (err) {
        setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
      } finally {
        setIsLoading(false);
      }
    }
  };

  return (
    <div className="flex justify-center items-center h-screen bg-background">
      <div className="bg-card p-10 rounded-2xl w-full max-w-md shadow-lg border">
        <h2 className="text-center mb-6 text-2xl font-medium text-foreground">Welcome to Telecom Agent</h2>
        {error && <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg text-sm">{error}</div>}
        <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
          <input 
            type="text" 
            className="bg-background border px-4 py-3 rounded-lg text-foreground text-base outline-none transition-colors focus:border-primary"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <input 
            type="password" 
            className="bg-background border px-4 py-3 rounded-lg text-foreground text-base outline-none transition-colors focus:border-primary"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button 
            type="submit" 
            disabled={isLoading}
            className={`bg-foreground text-background border-none py-3 rounded-lg text-base font-medium cursor-pointer transition-opacity hover:opacity-90 mt-2 ${isLoading ? 'opacity-70 cursor-not-allowed' : ''}`}
          >
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
