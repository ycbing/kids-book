// frontend/src/stores/bookStore.ts
import { create } from 'zustand';
import { Book, BookCreateRequest, bookApi } from '../services/api';
import { websocketService, WebSocketMessage } from '../services/websocket';
import { useUIStore } from './uiStore';

interface BookState {
  // 数据状态
  books: Book[];
  currentBook: Book | null;

  // UI状态
  isLoading: boolean;
  isGenerating: boolean;
  generationProgress: {
    stage: string;
    progress: number;
  };
  error: string | null;
  wsStatus: 'disconnected' | 'connecting' | 'connected' | 'reconnecting' | 'failed';

  // WebSocket管理
  websocketUnsubscribe: (() => void) | null;
  pollingInterval: ReturnType<typeof setInterval> | null;
  usePollingFallback: boolean;

  // 动作
  fetchBooks: () => Promise<void>;
  fetchBook: (id: number) => Promise<void>;
  createBook: (data: BookCreateRequest) => Promise<Book>;
  deleteBook: (id: number) => Promise<void>;
  updatePage: (bookId: number, pageNumber: number, text: string) => Promise<void>;
  regenerateImage: (bookId: number, pageNumber: number) => Promise<void>;
  setGenerationProgress: (stage: string, progress: number) => void;
  clearError: () => void;

  // WebSocket相关
  connectWebSocket: (bookId: number) => void;
  disconnectWebSocket: () => void;
  handleWebSocketMessage: (message: WebSocketMessage) => void;
  startPollingFallback: (bookId: number) => void;
  stopPollingFallback: () => void;
}

export const useBookStore = create<BookState>((set, get) => ({
  // 初始状态
  books: [],
  currentBook: null,
  isLoading: false,
  isGenerating: false,
  generationProgress: { stage: '', progress: 0 },
  error: null,
  wsStatus: 'disconnected',
  websocketUnsubscribe: null,
  pollingInterval: null,
  usePollingFallback: false,

  // ========== 数据操作 ==========

  fetchBooks: async () => {
    set({ isLoading: true, error: null });
    try {
      const books = await bookApi.list();
      set({ books, isLoading: false });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },

  fetchBook: async (id: number) => {
    set({ isLoading: true, error: null });
    try {
      const book = await bookApi.get(id);
      set({ currentBook: book, isLoading: false });

      // 如果正在生成，连接WebSocket
      if (book.status === 'generating' && !get().usePollingFallback) {
        get().connectWebSocket(id);
      }
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },

  createBook: async (data: BookCreateRequest) => {
    set({
      isGenerating: true,
      error: null,
      generationProgress: { stage: '初始化', progress: 0 },
      usePollingFallback: false
    };

    try {
      const book = await bookApi.create(data);
      set((state) => ({
        books: [book, ...state.books],
        currentBook: book
      }));

      // 连接WebSocket以获取实时进度
      get().connectWebSocket(book.id);

      return book;
    } catch (error: any) {
      set({ error: error.message, isGenerating: false });
      throw error;
    }
  },

  deleteBook: async (id: number) => {
    try {
      await bookApi.delete(id);
      set((state) => ({
        books: state.books.filter((b) => b.id !== id),
        currentBook: state.currentBook?.id === id ? null : state.currentBook
      }));
    } catch (error: any) {
      set({ error: error.message });
    }
  },

  updatePage: async (bookId: number, pageNumber: number, text: string) => {
    try {
      await bookApi.updatePage(bookId, pageNumber, text);
      set((state) => {
        if (state.currentBook?.id === bookId) {
          const updatedPages = state.currentBook.pages.map((p) =>
            p.page_number === pageNumber ? { ...p, text_content: text } : p
          );
          return { currentBook: { ...state.currentBook, pages: updatedPages } };
        }
        return state;
      });
    } catch (error: any) {
      set({ error: error.message });
    }
  },

  regenerateImage: async (bookId: number, pageNumber: number) => {
    set({ isLoading: true });
    try {
      const result = await bookApi.regenerateImage(bookId, pageNumber);
      set((state) => {
        if (state.currentBook?.id === bookId) {
          const updatedPages = state.currentBook.pages.map((p) =>
            p.page_number === pageNumber ? { ...p, image_url: result.image_url } : p
          );
          return { currentBook: { ...state.currentBook, pages: updatedPages }, isLoading: false };
        }
        return { isLoading: false };
      });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },

  // ========== 状态管理 ==========

  setGenerationProgress: (stage: string, progress: number) => {
    set({ generationProgress: { stage, progress } });
  },

  clearError: () => set({ error: null }),

  // ========== WebSocket管理 ==========

  connectWebSocket: (bookId: number) => {
    // 先断开旧连接和轮询
    get().disconnectWebSocket();
    get().stopPollingFallback();

    // 设置WebSocket连接失败回调
    websocketService.setConnectionLostCallback((failedBookId) => {
      if (failedBookId === bookId) {
        console.log('⚠️  WebSocket连接失败，切换到轮询模式');
        set({ usePollingFallback: true });
        get().startPollingFallback(bookId);
      }
    });

    // 监听连接状态
    websocketService.onStatusChange((status) => {
      set({ wsStatus: status });
    });

    // 连接WebSocket
    websocketService.connect(bookId);

    // 订阅消息
    const unsubscribe = websocketService.subscribe((message) => {
      get().handleWebSocketMessage(message);
    });

    set({ websocketUnsubscribe: unsubscribe });
  },

  disconnectWebSocket: () => {
    const { websocketUnsubscribe, pollingInterval } = get();

    // 取消WebSocket订阅
    if (websocketUnsubscribe) {
      websocketUnsubscribe();
      set({ websocketUnsubscribe: null });
    }

    // 断开WebSocket
    websocketService.disconnect();

    // 停止轮询
    if (pollingInterval) {
      clearInterval(pollingInterval);
      set({ pollingInterval: null });
    }

    set({
      wsStatus: 'disconnected',
      usePollingFallback: false
    });
  },

  handleWebSocketMessage: (message: WebSocketMessage) => {
    console.log('📨 Received WebSocket message:', message.type);

    switch (message.type) {
      case 'page_completed':
        // 单个页面完成，更新对应页面
        if (message.page_number && message.image_url) {
          set((state) => {
            if (state.currentBook?.id === message.book_id) {
              const updatedPages = state.currentBook.pages.map((p) =>
                p.page_number === message.page_number
                  ? { ...p, image_url: message.image_url }
                  : p
              );
              return {
                currentBook: { ...state.currentBook, pages: updatedPages }
              };
            }
            return state;
          });
        }
        break;

      case 'generation_completed':
        // 生成完成，重新获取完整数据
        get().fetchBook(message.book_id);
        set({ isGenerating: false });
        break;

      case 'generation_failed':
        // 生成失败
        get().fetchBook(message.book_id);
        set({
          isGenerating: false,
          error: message.error || '生成失败'
        });
        break;

      case 'image_progress':
        // 更新进度
        if (message.progress !== undefined) {
          set({
            generationProgress: {
              stage: message.stage || '生成中',
              progress: message.progress
            }
          });
        }
        break;

      case 'status_update':
        // 状态更新
        set({
          generationProgress: {
            stage: message.stage || '初始化',
            progress: 0
          }
        });
        break;
    }
  },

  // ========== 轮询降级方案 ==========

  startPollingFallback: (bookId: number) => {
    // 清除旧的轮询
    const { pollingInterval } = get();
    if (pollingInterval) {
      clearInterval(pollingInterval);
    }

    console.log('🔄 Starting polling fallback for book:', bookId);

    // 立即获取一次
    get().fetchBook(bookId);

    // 每3秒轮询一次
    const interval = setInterval(async () => {
      const state = get();

      // 检查是否应该停止轮询
      if (!state.usePollingFallback ||
          !state.currentBook ||
          state.currentBook.id !== bookId) {
        get().stopPollingFallback();
        return;
      }

      // 如果生成完成或失败，停止轮询
      if (state.currentBook.status === 'completed' ||
          state.currentBook.status === 'failed') {
        get().stopPollingFallback();
        return;
      }

      // 继续轮询
      await get().fetchBook(bookId);
    }, 3000);

    set({ pollingInterval: interval });
  },

  stopPollingFallback: () => {
    const { pollingInterval } = get();
    if (pollingInterval) {
      clearInterval(pollingInterval);
      set({ pollingInterval: null });
    }
  },
}));
