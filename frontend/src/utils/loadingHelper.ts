// frontend/src/utils/loadingHelper.ts
import { useUIStore } from '../stores/uiStore';

/**
 * 创建带有加载状态的异步操作包装器
 * 自动管理本地和全局的加载状态
 */
export function createLoadingAction<T extends (...args: any[]) => Promise<any>>(
  key: string,
  action: T,
  options?: {
    localLoadingSetter?: (loading: boolean) => void;
    errorMessage?: string;
    successMessage?: string;
    clearError?: () => void;
  }
): T {
  return (async (...args: Parameters<T>) => {
    const { setLoading, addNotification } = useUIStore.getState();

    // 清除之前的错误
    options?.clearError?.();

    // 设置加载状态
    options?.localLoadingSetter?.(true);
    setLoading(key, true);

    try {
      const result = await action(...args);

      // 显示成功消息（可选）
      if (options?.successMessage) {
        addNotification({
          type: 'success',
          message: options.successMessage,
        });
      }

      return result;
    } catch (error) {
      // 显示错误消息
      const message = options?.errorMessage || (error as Error).message;
      addNotification({
        type: 'error',
        message,
        duration: 5000,
      });

      throw error;
    } finally {
      // 清除加载状态
      options?.localLoadingSetter?.(false);
      setLoading(key, false);
    }
  }) as T;
}

/**
 * 批量操作加载状态管理
 */
export async function withBatchLoading<T>(
  keys: string[],
  action: () => Promise<T>,
  options?: {
    localLoadingSetter?: (loading: boolean) => void;
    onSuccess?: (result: T) => void;
    onError?: (error: Error) => void;
  }
): Promise<T> {
  const { setLoading } = useUIStore.getState();

  // 设置所有加载状态
  keys.forEach((key) => setLoading(key, true));
  options?.localLoadingSetter?.(true);

  try {
    const result = await action();
    options?.onSuccess?.(result);
    return result;
  } catch (error) {
    options?.onError?.(error as Error);
    throw error;
  } finally {
    // 清除所有加载状态
    keys.forEach((key) => setLoading(key, false));
    options?.localLoadingSetter?.(false);
  }
}

/**
 * 竞态加载处理
 * 确保同时只有一个相同的操作在进行
 */
export class RaceConditionLoader {
  private pendingRequests = new Map<string, Promise<any>>();

  async load<T>(
    key: string,
    loader: () => Promise<T>,
    options?: {
      deduplicate?: boolean; // 是否去重
    }
  ): Promise<T> {
    // 如果启用去重且有正在进行的请求，返回它
    if (options?.deduplicate && this.pendingRequests.has(key)) {
      return this.pendingRequests.get(key) as Promise<T>;
    }

    // 创建新请求
    const promise = loader();

    // 保存请求
    this.pendingRequests.set(key, promise);

    // 完成后清除
    promise.finally(() => {
      this.pendingRequests.delete(key);
    });

    return promise;
  }

  /**
   * 取消特定key的所有待处理请求
   */
  cancel(key: string) {
    this.pendingRequests.delete(key);
  }

  /**
   * 取消所有待处理请求
   */
  cancelAll() {
    this.pendingRequests.clear();
  }
}

// 创建全局实例
export const raceLoader = new RaceConditionLoader();

/**
 * 优先级加载管理
 */
export class PriorityLoader {
  private queue: Array<{
    key: string;
    priority: number;
    loader: () => Promise<any>;
    resolve: (value: any) => void;
    reject: (error: any) => void;
  }> = [];
  private running = false;
  private maxConcurrent = 3;
  private currentCount = 0;

  async load<T>(
    key: string,
    loader: () => Promise<T>,
    priority: number = 0
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push({
        key,
        priority,
        loader,
        resolve,
        reject,
      });

      // 按优先级排序
      this.queue.sort((a, b) => b.priority - a.priority);

      this.process();
    });
  }

  private async process() {
    if (this.running || this.currentCount >= this.maxConcurrent) {
      return;
    }

    this.running = true;

    while (this.queue.length > 0 && this.currentCount < this.maxConcurrent) {
      const task = this.queue.shift();
      if (task) {
        this.currentCount++;

        task
          .loader()
          .then(task.resolve)
          .catch(task.reject)
          .finally(() => {
            this.currentCount--;
            this.process();
          });
      }
    }

    this.running = false;
  }
}

// 创建全局实例
export const priorityLoader = new PriorityLoader();
