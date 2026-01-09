// frontend/src/stores/uiStore.ts
import { create } from 'zustand';

interface LoadingState {
  [key: string]: boolean;
}

interface UIState {
  // 加载状态
  loading: LoadingState;
  globalLoading: boolean;

  // 通知状态
  notifications: Array<{
    id: string;
    type: 'success' | 'error' | 'warning' | 'info';
    message: string;
    duration?: number;
  }>;

  // 模态框状态
  modals: {
    [key: string]: boolean;
  };

  // 侧边栏状态
  sidebarOpen: boolean;

  // 动作
  setGlobalLoading: (loading: boolean) => void;
  setLoading: (key: string, loading: boolean) => void;
  isLoading: (key: string) => boolean;

  // 通知操作
  addNotification: (notification: {
    type: 'success' | 'error' | 'warning' | 'info';
    message: string;
    duration?: number;
  }) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;

  // 模态框操作
  openModal: (key: string) => void;
  closeModal: (key: string) => void;
  isModalOpen: (key: string) => boolean;

  // 侧边栏操作
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;

  // 批量操作
  clearLoading: () => void;
  clearModals: () => void;
}

export const useUIStore = create<UIState>((set, get) => ({
  // 初始状态
  loading: {},
  globalLoading: false,
  notifications: [],
  modals: {},
  sidebarOpen: true,

  // ========== 全局加载状态 ==========

  setGlobalLoading: (loading: boolean) => {
    set({ globalLoading: loading });
  },

  // ========== 局部加载状态 ==========

  setLoading: (key: string, loading: boolean) => {
    set((state) => ({
      loading: {
        ...state.loading,
        [key]: loading,
      },
    }));

    // 如果有任何加载中，则全局加载为true
    const hasLoading = Object.values(get().loading).some((v) => v);
    set({ globalLoading: hasLoading });
  },

  isLoading: (key: string) => {
    return get().loading[key] || false;
  },

  // ========== 通知操作 ==========

  addNotification: (notification) => {
    const id = `notification-${Date.now()}-${Math.random()}`;
    const newNotification = { ...notification, id };

    set((state) => ({
      notifications: [...state.notifications, newNotification],
    }));

    // 自动移除通知
    const duration = notification.duration || 3000;
    if (duration > 0) {
      setTimeout(() => {
        get().removeNotification(id);
      }, duration);
    }
  },

  removeNotification: (id: string) => {
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    }));
  },

  clearNotifications: () => {
    set({ notifications: [] });
  },

  // ========== 模态框操作 ==========

  openModal: (key: string) => {
    set((state) => ({
      modals: {
        ...state.modals,
        [key]: true,
      },
    }));
  },

  closeModal: (key: string) => {
    set((state) => ({
      modals: {
        ...state.modals,
        [key]: false,
      },
    }));
  },

  isModalOpen: (key: string) => {
    return get().modals[key] || false;
  },

  // ========== 侧边栏操作 ==========

  toggleSidebar: () => {
    set((state) => ({
      sidebarOpen: !state.sidebarOpen,
    }));
  },

  setSidebarOpen: (open: boolean) => {
    set({ sidebarOpen: open });
  },

  // ========== 批量操作 ==========

  clearLoading: () => {
    set({ loading: {}, globalLoading: false });
  },

  clearModals: () => {
    set({ modals: {} });
  },
}));

// 便捷工具函数
export const uiActions = {
  // 显示成功通知
  success: (message: string, duration?: number) => {
    useUIStore.getState().addNotification({ type: 'success', message, duration });
  },

  // 显示错误通知
  error: (message: string, duration?: number) => {
    useUIStore.getState().addNotification({ type: 'error', message, duration });
  },

  // 显示警告通知
  warning: (message: string, duration?: number) => {
    useUIStore.getState().addNotification({ type: 'warning', message, duration });
  },

  // 显示信息通知
  info: (message: string, duration?: number) => {
    useUIStore.getState().addNotification({ type: 'info', message, duration });
  },

  // 异步操作包装器
  asyncOperation: async <T>(
    key: string,
    operation: () => Promise<T>,
    options?: {
      onSuccess?: (result: T) => void;
      onError?: (error: Error) => void;
      successMessage?: string;
      errorMessage?: string;
    }
  ): Promise<T> => {
    const { setLoading, addNotification } = useUIStore.getState();

    try {
      setLoading(key, true);
      const result = await operation();

      if (options?.successMessage) {
        addNotification({ type: 'success', message: options.successMessage });
      }

      options?.onSuccess?.(result);
      return result;
    } catch (error) {
      const message = options?.errorMessage || (error as Error).message;
      addNotification({ type: 'error', message, duration: 5000 });

      options?.onError?.(error as Error);
      throw error;
    } finally {
      setLoading(key, false);
    }
  },
};
