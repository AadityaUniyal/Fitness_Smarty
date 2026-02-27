import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');
  return {
    server: {
      port: 3000,
      host: '0.0.0.0',
    },
    plugins: [react()],
    // Removed process.env.API_KEY shim — all env vars now use import.meta.env.VITE_*
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      }
    },
    build: {
      // Code splitting to reduce chunk size
      rollupOptions: {
        output: {
          manualChunks: {
            // Vendor chunk for large stable libraries
            'vendor-react': ['react', 'react-dom'],
            'vendor-gemini': ['@google/genai'],
            'vendor-ui': ['lucide-react'],
          }
        }
      },
      // Raise chunk size warning limit slightly (large ML deps are expected)
      chunkSizeWarningLimit: 600,
    }
  };
});
