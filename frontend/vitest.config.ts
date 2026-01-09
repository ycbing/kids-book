// frontend/vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    // 测试环境
    environment: 'jsdom',

    // 全局配置
    globals: true,

    // 设置
    setupFiles: ['./src/tests/setup.ts'],

    // 覆盖率配置
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'src/tests/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/dist/**',
        '**/build/**',
        'src/main.tsx',
        'src/vite-env.d.ts',
      ],
      // 覆盖率阈值
      thresholds: {
        lines: 70,
        functions: 70,
        branches: 70,
        statements: 70,
      },
    },

    // 包含文件
    include: ['src/**/*.{test,spec}.{ts,tsx}'],

    // 排除文件
    exclude: ['node_modules', 'dist', 'build', '.git'],

    // 测试超时时间（毫秒）
    testTimeout: 10000,

    // 钩超时时间（毫秒）
    hookTimeout: 10000,

    // 隔套
    pool: 'threads',
    poolOptions: {
      threads: {
        singleThread: false,
        minThreads: 1,
        maxThreads: 4,
      },
    },

    // 报告器
    reporters: ['default', 'html'],

    // 监听模式配置
    watch: true,

    // 显示堆栈跟踪
    onConsoleLog: (log, type) => {
      if (log.toString().includes('Warning:') || type === 'warning') {
        return false;
      }
    },
  },

  // 路径解析
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@stores': path.resolve(__dirname, './src/stores'),
      '@services': path.resolve(__dirname, './src/services'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@types': path.resolve(__dirname, './src/types'),
    },
  },
});
