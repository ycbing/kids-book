import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',  // 使用 IPv4 地址而不是 localhost
        changeOrigin: true,
        rewrite: (path) => path,  // 不需要重写路径
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('proxy error', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('Sending:', req.method, req.url, '->', proxyReq.path);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log('Received:', proxyRes.statusCode, 'from', req.url);
          });
        },
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // React核心库
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          // UI组件库
          'ui-vendor': ['framer-motion', 'lucide-react', 'react-hot-toast'],
          // 数据请求和状态管理
          'utils': ['axios', '@tanstack/react-query'],
          // 其他第三方库
          'vendor': ['idb', 'jszip'],
        },
      },
    },
    // 启用源码映射用于生产环境调试
    sourcemap: true,
    // 代码分割阈值
    chunkSizeWarningLimit: 1000,
  },
})
