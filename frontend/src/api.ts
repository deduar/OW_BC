import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  withCredentials: true, // Crucial for HttpOnly cookies
});

// Add response interceptor for session expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear user data and redirect to login if session expired
      window.dispatchEvent(new CustomEvent('auth:expired'));
    }
    return Promise.reject(error);
  }
);

export default api;
