import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        configure: (proxy, options) => {
          // Hook into the proxy error event to suppress the terminal spam
          proxy.on('error', (err, req, res) => {
            if (err.code === 'ECONNREFUSED') {
              // Gracefully handle the error without crashing or spamming the Vite terminal
              res.writeHead(503, {
                'Content-Type': 'application/json',
              });
              res.end(JSON.stringify({ error: 'ContextShield Backend is offline.' }));
            }
          });
        }
      }
    }
  }
});
