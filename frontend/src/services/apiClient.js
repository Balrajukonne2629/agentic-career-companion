import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(
  (config) => {
    config.metadata = { startTime: new Date() };
    const label = `[API REQUEST] ${(config.method || 'GET').toUpperCase()} ${config.url}`;
    console.group(`%c⬆ Request Started — ${label}`, 'color: #9C27B0; font-weight: bold;');
    console.log('%cEndpoint URL:', 'font-weight:bold', config.url);
    console.log('%cMethod:', 'font-weight:bold', (config.method || 'GET').toUpperCase());
    if (config.data) {
      console.log('%cRequest Payload:', 'font-weight:bold');
      if (typeof config.data === 'object' && config.data !== null) {
        console.table(config.data);
        console.log('(full payload object):', config.data);
      } else {
        console.log(config.data);
      }
    } else {
      console.log('%cRequest Payload: none', 'color: #9E9E9E;');
    }
    console.groupEnd();
    return config;
  },
  (error) => {
    console.group('%c⬆ Request Setup Failed', 'color: #F44336; font-weight: bold;');
    console.error('Request Failed at Start:', error);
    if (error.stack) console.error('Stack Trace:', error.stack);
    console.groupEnd();
    return Promise.reject(error);
  }
);

apiClient.interceptors.response.use(
  (response) => {
    const startTime = response.config.metadata?.startTime;
    const responseTime = startTime ? new Date() - startTime : null;
    const label = `[API RESPONSE] ${(response.config.method || 'GET').toUpperCase()} ${response.config.url}`;

    console.group(`%c⬇ Request Completed — ${label}`, 'color: #4CAF50; font-weight: bold;');
    console.log('%cStatus:', 'font-weight:bold', response.status);
    if (responseTime !== null) {
      console.log(`%cResponse Time: ${responseTime}ms`, responseTime > 5000 ? 'color:#FF9800;font-weight:bold' : 'font-weight:bold');
    }
    console.log('%cResponse Body:', 'font-weight:bold', response.data);
    if (response.data && typeof response.data === 'object') {
      try {
        const flatKeys = Object.keys(response.data);
        if (flatKeys.length > 0) {
          console.table(flatKeys.map((k) => ({ key: k, type: typeof response.data[k], hasValue: response.data[k] !== null && response.data[k] !== undefined })));
        }
      } catch (_) { /* ignore table errors */ }
    }
    console.groupEnd();
    return response;
  },
  (error) => {
    const startTime = error.config?.metadata?.startTime;
    const responseTime = startTime ? new Date() - startTime : null;
    const label = `[API ERROR] ${(error.config?.method || 'GET').toUpperCase()} ${error.config?.url}`;

    console.group(`%c⬇ Request Failed — ${label}`, 'color: #F44336; font-weight: bold;');
    if (error.response) {
      console.error('%cStatus:', 'font-weight:bold', error.response.status);
    }
    if (responseTime !== null) {
      console.log(`%cResponse Time: ${responseTime}ms`, 'font-weight:bold');
    }

    const message =
      error.response?.data?.message ||
      error.response?.data?.error ||
      error.message ||
      'Something went wrong while communicating with the backend.';

    console.error('%cError Message:', 'font-weight:bold', message);
    if (error.response?.data) {
      console.error('%cError Body:', 'font-weight:bold', error.response.data);
      try { console.table(error.response.data); } catch (_) { /* ignore */ }
    }
    if (error.stack) {
      console.error('%cStack Trace:', 'font-weight:bold', error.stack);
    } else if (error.originalError?.stack) {
      console.error('%cStack Trace (original):', 'font-weight:bold', error.originalError.stack);
    }
    console.groupEnd();

    return Promise.reject({
      message,
      status: error.response?.status,
      data: error.response?.data,
      originalError: error,
    });
  },
);

export default apiClient;
