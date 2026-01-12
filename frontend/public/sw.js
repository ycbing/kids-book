// frontend/public/sw.js
/**
 * Service Worker for AI Picture Book PWA
 * 提供离线缓存和资源管理功能
 */

const CACHE_NAME = 'ai-picture-book-v1';
const RUNTIME_CACHE = 'ai-picture-book-runtime-v1';

// 静态资源缓存列表 - 在install时预缓存
const STATIC_CACHE_URLS = [
  '/',
  '/index.html',
  '/manifest.json', // 如果有PWA manifest
];

// API缓存配置
const API_CACHE_CONFIG = {
  // 缓存热门绘本列表 (5分钟)
  '/api/books': { maxAge: 5 * 60 * 1000, maxEntries: 10 },
  // 缓存绘本详情 (10分钟)
  '/api/books/': { maxAge: 10 * 60 * 1000, maxEntries: 50 },
  // 缓存用户信息 (30分钟)
  '/api/users/': { maxAge: 30 * 60 * 1000, maxEntries: 5 },
};

// 安装事件 - 预缓存静态资源
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');

  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Pre-caching app shell');
      return cache.addAll(STATIC_CACHE_URLS);
    })
  );

  // 立即激活新的service worker
  self.skipWaiting();
});

// 激活事件 - 清理旧缓存
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...');

  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          // 删除旧版本的缓存
          if (cacheName !== CACHE_NAME && cacheName !== RUNTIME_CACHE) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );

  // 立即控制所有客户端
  return self.clients.claim();
});

// 拦截网络请求
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // API请求处理
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleAPIRequest(request));
    return;
  }

  // 静态资源处理 - Cache First策略
  event.respondWith(
    caches.match(request).then((cachedResponse) => {
      if (cachedResponse) {
        // 缓存命中，同时后台更新
        fetchAndCache(request);
        return cachedResponse;
      }

      // 缓存未命中，发起网络请求
      return fetchAndCache(request);
    })
  );
});

/**
 * 处理API请求 - Network First策略
 */
async function handleAPIRequest(request) {
  const url = new URL(request.url);
  const pathname = url.pathname;

  // 查找匹配的缓存配置
  let cacheConfig = null;
  for (const [path, config] of Object.entries(API_CACHE_CONFIG)) {
    if (pathname.startsWith(path)) {
      cacheConfig = config;
      break;
    }
  }

  // GET请求可以缓存
  if (request.method === 'GET' && cacheConfig) {
    try {
      // 先尝试网络请求
      const response = await fetch(request);

      // 网络请求成功，缓存响应
      if (response.ok) {
        const cache = await caches.open(RUNTIME_CACHE);
        await cache.put(request, response.clone());
      }

      return response;
    } catch (error) {
      // 网络失败，尝试从缓存读取
      const cachedResponse = await caches.match(request);
      if (cachedResponse) {
        console.log('[SW] API cache hit for:', request.url);
        return cachedResponse;
      }

      // 缓存也没有，返回离线错误
      return new Response(
        JSON.stringify({
          success: false,
          error: {
            code: 'NETWORK_ERROR',
            message: '网络连接失败，请检查您的网络设置'
          }
        }),
        {
          status: 503,
          headers: { 'Content-Type': 'application/json' }
        }
      );
    }
  }

  // 非GET请求或无需缓存的请求直接转发
  return fetch(request);
}

/**
 * 发起网络请求并缓存响应
 */
async function fetchAndCache(request) {
  try {
    const response = await fetch(request);

    // 只缓存成功的响应
    if (response.ok && response.status === 200) {
      const cache = await caches.open(RUNTIME_CACHE);
      await cache.put(request, response.clone());
    }

    return response;
  } catch (error) {
    console.error('[SW] Fetch failed:', error);
    throw error;
  }
}

/**
 * 定期清理过期缓存
 */
async function cleanupExpiredCache() {
  try {
    const cache = await caches.open(RUNTIME_CACHE);
    const requests = await cache.keys();

    // 检查每个缓存的年龄
    const now = Date.now();
    for (const request of requests) {
      const response = await cache.match(request);
      if (response) {
        const cacheTime = response.headers.get('sw-cache-time');
        if (cacheTime && (now - parseInt(cacheTime)) > 30 * 60 * 1000) {
          // 超过30分钟的缓存删除
          await cache.delete(request);
        }
      }
    }
  } catch (error) {
    console.error('[SW] Cache cleanup failed:', error);
  }
}

// 每小时清理一次过期缓存
setInterval(cleanupExpiredCache, 60 * 60 * 1000);

// 监听消息事件（用于手动更新缓存）
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'CLEAR_CACHE') {
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => caches.delete(cacheName))
      );
    });
  }
});

console.log('[SW] Service Worker loaded');
