// frontend/src/utils/test-utils.test.ts
/**
 * 工具函数测试
 */

import { describe, it, expect } from 'vitest';
import {
  isBook,
  isPage,
  isUser,
  validatePassword,
  isValidEmail,
  formatDate,
  formatFileSize,
} from './utils';

describe('类型守卫函数', () => {
  describe('isBook', () => {
    it('应该正确识别Book对象', () => {
      const book = {
        id: 1,
        title: '测试绘本',
        description: '测试描述',
        theme: '测试主题',
        keywords: ['测试'],
        target_age: '3-5',
        style: '水彩风格',
        status: 'draft',
        pages: [],
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
        user_id: 1,
      };

      expect(isBook(book)).toBe(true);
    });

    it('应该拒绝无效的Book对象', () => {
      const invalidBook = {
        id: 'not a number',
        title: '测试',
      };

      expect(isBook(invalidBook)).toBe(false);
    });

    it('应该拒绝null', () => {
      expect(isBook(null)).toBe(false);
    });

    it('应该拒绝undefined', () => {
      expect(isBook(undefined)).toBe(false);
    });
  });

  describe('isPage', () => {
    it('应该正确识别Page对象', () => {
      const page = {
        page_number: 1,
        text_content: '测试文本',
        image_prompt: '测试提示词',
      };

      expect(isPage(page)).toBe(true);
    });

    it('应该拒绝无效的Page对象', () => {
      const invalidPage = {
        page_number: 'not a number',
        text_content: '测试',
      };

      expect(isPage(invalidPage)).toBe(false);
    });
  });

  describe('isUser', () => {
    it('应该正确识别User对象', () => {
      const user = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      };

      expect(isUser(user)).toBe(true);
    });

    it('应该拒绝无效的User对象', () => {
      const invalidUser = {
        id: 1,
        username: 'test',
      };

      expect(isUser(invalidUser)).toBe(false);
    });
  });
});

describe('验证函数', () => {
  describe('validatePassword', () => {
    it('应该验证强密码', () => {
      const result = validatePassword('StrongPass123!');

      expect(result.isValid).toBe(true);
      expect(result.strength).toBe('strong');
      expect(result.errors).toHaveLength(0);
    });

    it('应该识别弱密码（太短）', () => {
      const result = validatePassword('Short1!');

      expect(result.isValid).toBe(false);
      expect(result.strength).toBe('weak');
      expect(result.errors.length).toBeGreaterThan(0);
    });

    it('应该识别中等密码', () => {
      const result = validatePassword('MediumPass123');

      expect(result.isValid).toBe(false);
      expect(result.strength).toBe('medium');
    });

    it('应该要求包含大写字母', () => {
      const result = validatePassword('lowercase123!');

      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('密码需要包含大写字母');
    });

    it('应该要求包含数字', () => {
      const result = validatePassword('NoNumbers!');

      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('密码需要包含数字');
    });
  });

  describe('isValidEmail', () => {
    it('应该接受有效的邮箱地址', () => {
      expect(isValidEmail('test@example.com')).toBe(true);
      expect(isValidEmail('user.name+tag@domain.co.uk')).toBe(true);
    });

    it('应该拒绝无效的邮箱地址', () => {
      expect(isValidEmail('invalid')).toBe(false);
      expect(isValidEmail('invalid@')).toBe(false);
      expect(isValidEmail('@example.com')).toBe(false);
      expect(isValidEmail('test@')).toBe(false);
    });
  });
});

describe('格式化函数', () => {
  describe('formatDate', () => {
    it('应该格式化日期为中文格式', () => {
      const date = new Date('2024-01-15T10:30:00Z');
      const formatted = formatDate(date);

      expect(formatted).toContain('2024');
      expect(formatted).toContain('01');
      expect(formatted).toContain('15');
    });

    it('应该处理ISO字符串', () => {
      const formatted = formatDate('2024-01-15T10:30:00Z');

      expect(formatted).toBeDefined();
      expect(typeof formatted).toBe('string');
    });

    it('应该处理无效日期', () => {
      const formatted = formatDate('invalid-date');

      expect(formatted).toBe('无效日期');
    });
  });

  describe('formatFileSize', () => {
    it('应该格式化字节', () => {
      expect(formatFileSize(500)).toBe('500 B');
    });

    it('应该格式化KB', () => {
      expect(formatFileSize(1536)).toBe('1.5 KB');
    });

    it('应该格式化MB', () => {
      expect(formatFileSize(1048576 * 5)).toBe('5 MB');
    });

    it('应该格式化GB', () => {
      expect(formatFileSize(1073741824 * 2)).toBe('2 GB');
    });

    it('应该处理0字节', () => {
      expect(formatFileSize(0)).toBe('0 B');
    });
  });
});

describe('数组工具函数', () => {
  describe('chunk', () => {
    it('应该正确分块数组', () => {
      const array = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
      const chunks = chunk(array, 3);

      expect(chunks).toHaveLength(4);
      expect(chunks[0]).toEqual([1, 2, 3]);
      expect(chunks[1]).toEqual([4, 5, 6]);
      expect(chunks[2]).toEqual([7, 8, 9]);
      expect(chunks[3]).toEqual([10]);
    });

    it('应该处理空数组', () => {
      const chunks = chunk([], 3);
      expect(chunks).toEqual([]);
    });

    it('当块大小大于数组长度时应该返回单个块', () => {
      const chunks = chunk([1, 2, 3], 10);
      expect(chunks).toHaveLength(1);
      expect(chunks[0]).toEqual([1, 2, 3]);
    });
  });

  describe('groupBy', () => {
    it('应该按属性分组', () => {
      const items = [
        { category: 'A', name: 'Item1' },
        { category: 'B', name: 'Item2' },
        { category: 'A', name: 'Item3' },
      ];

      const grouped = groupBy(items, 'category');

      expect(grouped['A']).toHaveLength(2);
      expect(grouped['B']).toHaveLength(1);
    });
  });
});
