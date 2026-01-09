// frontend/src/stores/bookStore.test.ts
/**
 * bookStore测试
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useBookStore } from './bookStore';
import * as api from '../services/api';

// Mock API
vi.mock('../services/api', () => ({
  bookApi: {
    list: vi.fn(),
    create: vi.fn(),
    get: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    generate: vi.fn(),
  },
}));

const mockBookApi = api.bookApi as any;

describe('useBookStore', () => {
  beforeEach(() => {
    // 重置store状态
    useBookStore.setState({
      books: [],
      currentBook: null,
      isGenerating: false,
      error: null,
      loading: false,
    });

    // 清除所有mock
    vi.clearAllMocks();
  });

  describe('初始状态', () => {
    it('应该有正确的初始状态', () => {
      const { result } = renderHook(() => useBookStore());

      expect(result.current.books).toEqual([]);
      expect(result.current.currentBook).toBeNull();
      expect(result.current.isGenerating).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.loading).toBe(false);
    });
  });

  describe('fetchBooks', () => {
    it('应该成功获取绘本列表', async () => {
      const mockBooks = [
        { id: 1, title: '绘本1', theme: '主题1' },
        { id: 2, title: '绘本2', theme: '主题2' },
      ];

      mockBookApi.list.mockResolvedValue(mockBooks);

      const { result } = renderHook(() => useBookStore());

      await act(async () => {
        await result.current.fetchBooks();
      });

      expect(result.current.books).toEqual(mockBooks);
      expect(result.current.error).toBeNull();
      expect(mockBookApi.list).toHaveBeenCalledTimes(1);
    });

    it('应该处理API错误', async () => {
      mockBookApi.list.mockRejectedValue(new Error('网络错误'));

      const { result } = renderHook(() => useBookStore());

      await act(async () => {
        await result.current.fetchBooks();
      });

      expect(result.current.books).toEqual([]);
      expect(result.current.error).toBe('网络错误');
    });
  });

  describe('createBook', () => {
    it('应该成功创建绘本', async () => {
      const newBook = {
        theme: '测试主题',
        keywords: ['测试'],
        target_age: '3-5',
        style: '水彩风格',
        page_count: 8,
      };

      const createdBook = {
        id: 1,
        ...newBook,
        status: 'draft',
      };

      mockBookApi.create.mockResolvedValue(createdBook);

      const { result } = renderHook(() => useBookStore());

      await act(async () => {
        const book = await result.current.createBook(newBook);
        expect(book).toEqual(createdBook);
      });

      expect(result.current.currentBook).toEqual(createdBook);
      expect(mockBookApi.create).toHaveBeenCalledWith(newBook);
    });
  });

  describe('setCurrentBook', () => {
    it('应该设置当前绘本', () => {
      const { result } = renderHook(() => useBookStore());

      const mockBook = { id: 1, title: '测试绘本' };

      act(() => {
        result.current.setCurrentBook(mockBook as any);
      });

      expect(result.current.currentBook).toEqual(mockBook);
    });

    it('应该能够清除当前绘本', () => {
      const { result } = renderHook(() => useBookStore());

      const mockBook = { id: 1, title: '测试绘本' };

      act(() => {
        result.current.setCurrentBook(mockBook as any);
      });

      expect(result.current.currentBook).toEqual(mockBook);

      act(() => {
        result.current.clearCurrentBook();
      });

      expect(result.current.currentBook).toBeNull();
    });
  });

  describe('setError', () => {
    it('应该设置错误信息', () => {
      const { result } = renderHook(() => useBookStore());

      act(() => {
        result.current.setError('发生错误');
      });

      expect(result.current.error).toBe('发生错误');
    });

    it('应该能够清除错误信息', () => {
      const { result } = renderHook(() => useBookStore());

      act(() => {
        result.current.setError('发生错误');
      });

      expect(result.current.error).toBe('发生错误');

      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
    });
  });

  describe('updateBookInList', () => {
    it('应该更新列表中的绘本', () => {
      const { result } = renderHook(() => useBookStore());

      const initialBooks = [
        { id: 1, title: '绘本1' },
        { id: 2, title: '绘本2' },
      ];

      act(() => {
        result.current.setBooks(initialBooks as any);
      });

      expect(result.current.books).toEqual(initialBooks);

      const updatedBook = { id: 1, title: '更新的绘本1' };

      act(() => {
        result.current.updateBookInList(updatedBook as any);
      });

      expect(result.current.books[0]).toEqual(updatedBook);
      expect(result.current.books[1]).toEqual(initialBooks[1]);
    });

    it('如果绘本不存在应该添加到列表', () => {
      const { result } = renderHook(() => useBookStore());

      const initialBooks = [{ id: 1, title: '绘本1' }];

      act(() => {
        result.current.setBooks(initialBooks as any);
      });

      const newBook = { id: 2, title: '新绘本' };

      act(() => {
        result.current.updateBookInList(newBook as any);
      });

      expect(result.current.books.length).toBe(2);
      expect(result.current.books).toContainEqual(newBook);
    });
  });

  describe('removeBookFromList', () => {
    it('应该从列表中移除绘本', () => {
      const { result } = renderHook(() => useBookStore());

      const initialBooks = [
        { id: 1, title: '绘本1' },
        { id: 2, title: '绘本2' },
        { id: 3, title: '绘本3' },
      ];

      act(() => {
        result.current.setBooks(initialBooks as any);
      });

      act(() => {
        result.current.removeBookFromList(2);
      });

      expect(result.current.books.length).toBe(2);
      expect(result.current.books.find((b: any) => b.id === 2)).toBeUndefined();
      expect(result.current.books.map((b: any) => b.id)).toEqual([1, 3]);
    });
  });

  describe('loading状态', () => {
    it('应该正确设置loading状态', () => {
      const { result } = renderHook(() => useBookStore());

      expect(result.current.loading).toBe(false);

      act(() => {
        result.current.setLoading(true);
      });

      expect(result.current.loading).toBe(true);

      act(() => {
        result.current.setLoading(false);
      });

      expect(result.current.loading).toBe(false);
    });
  });

  describe('isGenerating状态', () => {
    it('应该正确设置生成状态', () => {
      const { result } = renderHook(() => useBookStore());

      expect(result.current.isGenerating).toBe(false);

      act(() => {
        result.current.setGenerating(true);
      });

      expect(result.current.isGenerating).toBe(true);

      act(() => {
        result.current.setGenerating(false);
      });

      expect(result.current.isGenerating).toBe(false);
    });
  });
});
