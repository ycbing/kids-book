// frontend/src/stores/bookStore.ts
import { create } from 'zustand';
import { Book, BookCreateRequest, bookApi } from '../services/api';

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

  // 动作
  fetchBooks: () => Promise<void>;
  fetchBook: (id: number) => Promise<void>;
  createBook: (data: BookCreateRequest) => Promise<Book>;
  deleteBook: (id: number) => Promise<void>;
  updatePage: (bookId: number, pageNumber: number, text: string) => Promise<void>;
  regenerateImage: (bookId: number, pageNumber: number) => Promise<void>;
  setGenerationProgress: (stage: string, progress: number) => void;
  clearError: () => void;
}

export const useBookStore = create<BookState>((set) => ({
  books: [],
  currentBook: null,
  isLoading: false,
  isGenerating: false,
  generationProgress: { stage: '', progress: 0 },
  error: null,

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

  clearError: () => set({ error: null })
}));
