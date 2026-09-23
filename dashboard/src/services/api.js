import axios from 'axios';

// Base API URL configuration
// Using Vite proxy path `/api` by default, with fallback to direct http://127.0.0.1:8000
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';
const DIRECT_API_URL = 'http://127.0.0.1:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2-minute timeout for deep static ML/CVE search
});

/**
 * Check API Health Status
 */
export const checkApiHealth = async () => {
  try {
    // Try primary client (Vite proxy)
    const response = await client.get('/health', { timeout: 3000 });
    if (response.data && response.data.status === 'healthy') {
      return { online: true, message: 'API Healthy' };
    }
    return { online: true, message: 'API Running' };
  } catch (err) {
    // Fallback attempt directly to http://127.0.0.1:8000 if proxy failed
    try {
      const directResponse = await axios.get(`${DIRECT_API_URL}/health`, { timeout: 3000 });
      if (directResponse.status === 200) {
        return { online: true, message: 'API Healthy (Direct)' };
      }
    } catch (directErr) {
      // Both failed
    }
    return { online: false, message: 'API Offline' };
  }
};

/**
 * Analyze uploaded APK file
 * @param {File} apkFile - The uploaded APK file
 * @returns {Promise<Object>} The parsed MOSAIC-ML response JSON
 */
export const analyzeApk = async (apkFile) => {
  if (!apkFile) {
    throw new Error('Please select an APK file to analyze.');
  }

  if (!apkFile.name.toLowerCase().endsWith('.apk')) {
    throw new Error('Invalid file type. Only .apk files are supported by MOSAIC-ML.');
  }

  const formData = new FormData();
  formData.append('file', apkFile);

  try {
    let response;
    try {
      // Primary call via proxy `/api/analyze-apk`
      response = await client.post('/analyze-apk', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
    } catch (proxyError) {
      // If proxy returns network error, fallback to direct call http://127.0.0.1:8000/analyze-apk
      if (!proxyError.response) {
        response = await axios.post(`${DIRECT_API_URL}/analyze-apk`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 120000,
        });
      } else {
        throw proxyError;
      }
    }

    if (!response || !response.data) {
      throw new Error('Empty response received from the analysis engine.');
    }

    return response.data;
  } catch (error) {
    console.error('MOSAIC-ML Analysis API Error:', error);

    if (error.response) {
      const status = error.response.status;
      const detail = error.response.data?.detail || error.response.data?.message;
      if (status === 500) {
        throw new Error(`Backend processing error: ${detail || 'The server encountered an exception while parsing the APK.'}`);
      }
      if (status === 422) {
        throw new Error('Unprocessable file format or invalid request payload.');
      }
      throw new Error(detail || `API error (HTTP ${status}). Please verify the backend service.`);
    } else if (error.code === 'ECONNABORTED') {
      throw new Error('Analysis timed out. Large APK parsing or CVE queries took longer than expected.');
    } else if (error.request) {
      throw new Error('Unable to reach the MOSAIC-ML backend API at http://127.0.0.1:8000. Please make sure the FastAPI server is running.');
    }

    throw new Error(error.message || 'An unexpected error occurred during analysis.');
  }
};
