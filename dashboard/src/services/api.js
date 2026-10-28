import axios from 'axios';

// `??` not `||`: an EMPTY VITE_API_URL is meaningful - it means "same origin",
// which is how the single-container build talks to its own API. `||` would
// treat the empty string as unset and bake in localhost, breaking the
// deployed container.
const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000';

const client = axios.create({ baseURL: API_BASE_URL, timeout: 180000 });

export const checkApiHealth = async () => {
  const { data } = await client.get('/health');
  return { online: data?.status === 'healthy' || data?.status === 'degraded', ...data };
};

export const analyzeApk = async (file) => {
  const form = new FormData();
  form.append('file', file);
  const { data } = await client.post('/analyze-apk', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const fetchHistory = async (limit = 10) => {
  const { data } = await client.get('/scans', { params: { limit } });
  return data;
};

export { API_BASE_URL };
