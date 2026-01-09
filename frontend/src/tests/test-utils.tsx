// frontend/src/tests/test-utils.tsx
/**
 * 测试工具函数
 * 提供常用的测试辅助函数
 */

import { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// ================================
// 自定义渲染函数
// ================================

/**
 * 创建测试用的QueryClient
 */
export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
    logger: {
      log: console.log,
      warn: console.warn,
      error: () => {}, // 静默错误
    },
  });
}

/**
 * 带有所有provider的自定义渲染函数
 */
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  route?: string;
  queryClient?: QueryClient;
}

export function renderWithProviders(
  ui: ReactElement,
  {
    route = '/',
    queryClient = createTestQueryClient(),
    ...renderOptions
  }: CustomRenderOptions = {}
) {
  // 设置当前路由
  window.history.pushState({}, 'Test page', route);

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>{children}</BrowserRouter>
      </QueryClientProvider>
    );
  }

  return {
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
    queryClient,
  };
}

// 重新导出所有testing-library工具
export * from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';

// ================================
// Mock数据生成器
// ================================

/**
 * 生成随机ID
 */
export function generateId(): number {
  return Math.floor(Math.random() * 10000);
}

/**
 * 生成随机字符串
 */
export function generateRandomString(length: number = 10): string {
  return Math.random().toString(36).substring(2, length + 2);
}

/**
 * 生成Mock绘本数据
 */
export function createMockBook(overrides = {}) {
  return {
    id: generateId(),
    title: '测试绘本',
    description: '这是一个测试绘本',
    theme: '勇敢的小兔子',
    keywords: ['勇气', '友谊'],
    target_age: '3-5',
    style: '水彩风格',
    status: 'draft',
    cover_image: null,
    pages: [],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    user_id: 1,
    ...overrides,
  };
}

/**
 * 生成Mock页面数据
 */
export function createMockPage(overrides = {}) {
  return {
    page_number: 1,
    text_content: '测试文本内容',
    image_prompt: '测试图片提示词',
    image_url: 'https://example.com/test.jpg',
    created_at: new Date().toISOString(),
    ...overrides,
  };
}

/**
 * 生成Mock用户数据
 */
export function createMockUser(overrides = {}) {
  return {
    id: generateId(),
    username: 'testuser',
    email: 'test@example.com',
    avatar: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  };
}

/**
 * 生成Mock API响应
 */
export function createMockResponse<T>(data: T, success = true) {
  return {
    success,
    data,
    timestamp: new Date().toISOString(),
  };
}

// ================================
// Mock函数
// ================================

/**
 * 创建异步Mock函数
 */
export function createAsyncMock<T>(returnValue: T, delay = 100) {
  return vi.fn().mockImplementation(
    () =>
      new Promise<T>((resolve) => {
        setTimeout(() => resolve(returnValue), delay);
      })
  );
}

/**
 * 创建延迟Mock函数（测试加载状态）
 */
export function createDelayedMock<T>(
  returnValue: T,
  delay: number = 1000
): () => Promise<T> {
  return () =>
    new Promise((resolve) => {
      setTimeout(() => resolve(returnValue), delay);
    });
}

// ================================
* 存储Mock工具
// ================================

/**
 * Mock Zustand store
 */
export function createMockStore<T>(initialState: T) {
  let state = initialState;

  return {
    getState: () => state,
    setState: (partial: Partial<T>) => {
      state = { ...state, ...partial };
    },
    subscribe: (listener: () => void) => {
      return () => {}; // 返回unsubscribe函数
    },
    destroy: () => {},
  };
}

// ================================
// DOM查询辅助函数
// ================================

/**
 * 等待元素出现
 */
export async function waitForElement(
  callback: () => HTMLElement | null,
  timeout = 1000
): Promise<HTMLElement> {
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    const element = callback();
    if (element) {
      return element;
    }
    await new Promise(resolve => setTimeout(resolve, 50));
  }

  throw new Error(`Element not found within ${timeout}ms`);
}

/**
 * 等待文本出现
 */
export async function waitForText(
  text: string,
  timeout = 1000
): Promise<HTMLElement> {
  return waitForElement(
    () => document.body.textContent?.includes(text) ? document.body : null,
    timeout
  );
}

// ================================
// 事件触发辅助函数
// ================================

/**
 * 触发文件选择事件
 */
export function triggerFileSelect(
  input: HTMLInputElement,
  files: File[] | FileList
) {
  const dataTransfer = new DataTransfer();

  if (files instanceof FileList) {
    Array.from(files).forEach(file => dataTransfer.items.add(file));
  } else {
    files.forEach(file => dataTransfer.items.add(file));
  }

  input.files = dataTransfer.files;

  // 触发change事件
  const event = new Event('change', { bubbles: true });
  input.dispatchEvent(event);
}

/**
 * 触发拖放事件
 */
export function triggerDragDrop(
  element: HTMLElement,
  data: Record<string, any>
) {
  element.dispatchEvent(
    new DragEvent('drop', {
      bubbles: true,
      cancelable: true,
      dataTransfer: new DataTransfer(),
    })
  );
}

// ================================
* 时间Mock工具
// ================================

/**
 * Mock当前时间
 */
export function mockCurrentTime(date: Date | string) {
  vi.setSystemTime(new Date(date));
}

/**
 * 重置时间Mock
 */
export function resetTimeMock() {
  vi.useRealTimers();
}

// ================================
// 网络Mock工具
// ================================

/**
 * Mock fetch API
 */
export function mockFetch(response: any, ok = true, status = 200) {
  global.fetch = vi.fn().mockResolvedValue({
    ok,
    status,
    json: async () => response,
    text: async () => JSON.stringify(response),
  } as Response);
}

/**
 * 重置fetch Mock
 */
export function resetFetchMock() {
  vi.restoreAllMocks();
}

// ================================
// 测试断言辅助函数
// ================================

/**
 * 断言元素存在
 */
export function assertElementExists(
  container: HTMLElement,
  selector: string
): HTMLElement {
  const element = container.querySelector(selector);
  expect(element).toBeTruthy();
  return element as HTMLElement;
}

/**
 * 断言元素不存在
 */
export function assertElementNotExists(
  container: HTMLElement,
  selector: string
) {
  const element = container.querySelector(selector);
  expect(element).toBeNull();
}

/**
 * 断言文本存在
 */
export function assertTextExists(
  container: HTMLElement,
  text: string
): HTMLElement | null {
  const element = Array.from(container.querySelectorAll('*')).find(el =>
    el.textContent?.includes(text)
  );

  expect(element).toBeTruthy();
  return element || null;
}
