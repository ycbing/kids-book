// frontend/src/stores/bookStore.ts
import { create } from 'zustand';
import { Book, BookCreateRequest, bookApi } from '../services/api';
import { websocketService, WebSocketMessage } from '../services/websocket';

interface BookState {
  // 状态
  books: Book[];
  currentBook: Book | null;
  isLoading: boolean;
  isGenerating: boolean;
  generationProgress: {
    stage: string;
    progress: number;
  };
  error: string | null;
  pollingInterval: ReturnType<typeof setInterval> | null;
  websocketUnsubscribe: (() => void) | null;

  // 动作
  fetchBooks: () => Promise<void>;
  fetchBook: (id: number) => Promise<void>;
  createBook: (data: BookCreateRequest) => Promise<Book>;
  deleteBook: (id: number) => Promise<void>;
  updatePage: (bookId: number, pageNumber: number, text: string) => Promise<void>;
  regenerateImage: (bookId: number, pageNumber: number) => Promise<void>;
  setGenerationProgress: (stage: string, progress: number) => void;
  clearError: () => void;
  startPolling: (bookId: number) => void;
  stopPolling: () => void;
  connectWebSocket: (bookId: number) => void;
  disconnectWebSocket: () => void;
  handleWebSocketMessage: (message: WebSocketMessage) => void;
}

export const useBookStore = create<BookState>((set, get) => ({
  books: [],
  currentBook: null,
  isLoading: false,
  isGenerating: false,
  generationProgress: { stage: '', progress: 0 },
  error: null,
  pollingInterval: null,
  websocketUnsubscribe: null,

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
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },

  createBook: async (data: BookCreateRequest) => {
    set({ isGenerating: true, error: null, generationProgress: { stage: '初始化', progress: 0 } });
    try {
      const book = await bookApi.create(data);
      set((state) => ({
        books: [book, ...state.books],
        currentBook: book,
        isGenerating: false
      }));
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

  setGenerationProgress: (stage: string, progress: number) => {
    set({ generationProgress: { stage, progress } });
  },

  clearError: () => set({ error: null }),

  startPolling: (bookId: number) => {
    // 清除旧的轮询
    if (get().pollingInterval) {
      get().stopPolling();
    }

    // 立即获取一次
    get().fetchBook(bookId);

    // 每3秒轮询一次
    const interval = setInterval(async () => {
      const state = get();
      if (state.currentBook?.status === 'completed' || state.currentBook?.status === 'failed') {
        // 生成完成或失败，停止轮询
        get().stopPolling();
      } else {
        // 继续轮询
        await get().fetchBook(bookId);
      }
    }, 3000);

    set({ pollingInterval: interval });
  },

  stopPolling: () => {
    const { pollingInterval } = get();
    if (pollingInterval) {
      clearInterval(pollingInterval);
      set({ pollingInterval: null });
    }
  },

  connectWebSocket: (bookId: number) => {
    // 先断开旧连接
    get().disconnectWebSocket();

    // 连接WebSocket
    websocketService.connect(bookId);

    // 订阅消息
    const unsubscribe = websocketService.subscribe((message) => {
      get().handleWebSocketMessage(message);
    });

    set({ websocketUnsubscribe: unsubscribe });
  },

  disconnectWebSocket: () => {
    const { websocketUnsubscribe } = get();
    if (websocketUnsubscribe) {
      websocketUnsubscribe();
      set({ websocketUnsubscribe: null });
    }
    websocketService.disconnect();
  },

  handleWebSocketMessage: (message: WebSocketMessage) => {
    console.log('Received WebSocket message:', message);

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
        // 生成完成，停止轮询
        get().stopPolling();
        get().fetchBook(message.book_id);
        break;

      case 'generation_failed':
        // 生成失败
        get().stopPolling();
        get().fetchBook(message.book_id);
        set({ error: message.error || '生成失败' });
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
        if (message.status) {
          set({
            generationProgress: {
              stage: message.stage || '初始化',
              progress: 0
            }
          });
        }
        break;
    }
  }
}));
