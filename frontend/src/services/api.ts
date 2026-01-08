// frontend/src/services/api.ts
import axios from 'axios';

// 开发环境使用代理，生产环境使用完整URL
const API_BASE_URL = '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2分钟超时（AI生成需要时间）
});

// 类型定义
export interface BookCreateRequest {
  title?: string;
  theme: string;
  keywords: string[];
  target_age: string;
  style: string;
  page_count: number;
  custom_prompt?: string;
}

export interface PageContent {
  page_number: number;
  text_content: string;
  image_prompt: string;
  image_url?: string;
}

export interface Book {
  id: number;
  title: string;
  description: string;
  theme: string;
  target_age: string;
  style: string;
  status: 'draft' | 'generating' | 'completed' | 'failed';
  cover_image?: string;
  pages: PageContent[];
  created_at: string;
}

export interface StoryGenerateRequest {
  theme: string;
  keywords: string[];
  target_age: string;
  page_count: number;
  custom_prompt?: string;
}

export interface Story {
  title: string;
  description: string;
  pages: {
    page_number: number;
    text: string;
    scene_description: string;
    image_prompt: string;
  }[];
}

// API方法
export const bookApi = {
  // 创建绘本
  create: async (data: BookCreateRequest): Promise<Book> => {
    const response = await api.post('/books', data);
    return response.data;
  },

  // 获取绘本详情
  get: async (id: number): Promise<Book> => {
    const response = await api.get(`/books/${id}`);
    return response.data;
  },

  // 获取绘本列表
  list: async (skip = 0, limit = 20): Promise<Book[]> => {
    const response = await api.get('/books', { params: { skip, limit } });
    return response.data;
  },

  // 删除绘本
  delete: async (id: number): Promise<void> => {
    await api.delete(`/books/${id}`);
  },

  // 更新页面
  updatePage: async (bookId: number, pageNumber: number, textContent: string): Promise<void> => {
    await api.put(`/books/${bookId}/pages/${pageNumber}`, null, {
      params: { text_content: textContent }
    });
  },

  // 重新生成页面图片
  regenerateImage: async (bookId: number, pageNumber: number, style?: string): Promise<{ image_url: string }> => {
    const response = await api.post(`/books/${bookId}/regenerate-image/${pageNumber}`, null, {
      params: { style }
    });
    return response.data;
  },

  // 导出绘本
  export: async (bookId: number, format: string, quality: string): Promise<{
    message: string;
    filename: string;
    file_type: string;
    book_id: number;
  }> => {
    const response = await api.post(`/books/${bookId}/export`, {
      book_id: bookId,
      format,
      quality
    });
    return response.data;
  },

  // 获取下载URL
  getDownloadUrl: (bookId: number, filename: string): string => {
    return `/api/v1/download/${bookId}/${filename}`;
  }
};

export const aiApi = {
  // 生成故事
  generateStory: async (data: StoryGenerateRequest): Promise<Story> => {
    const response = await api.post('/generate/story', data);
    return response.data;
  },

  // 生成图片
  generateImage: async (prompt: string, style: string): Promise<{ image_url: string }> => {
    const response = await api.post('/generate/image', { prompt, style });
    return response.data;
  }
};

export default api;
