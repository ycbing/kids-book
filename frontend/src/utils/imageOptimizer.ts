// frontend/src/utils/imageOptimizer.ts

/**
 * 图片优化配置
 */
export interface ImageOptimizationOptions {
  maxWidth?: number;
  maxHeight?: number;
  quality?: number; // 0-1
  format?: 'image/jpeg' | 'image/png' | 'image/webp';
  enableCache?: boolean;
}

/**
 * 图片信息
 */
export interface ImageInfo {
  width: number;
  height: number;
  size: number; // 字节
  type: string;
  aspectRatio: number;
}

/**
 * 图片优化工具类
 */
export class ImageOptimizer {
  private cache: Map<string, string> = new Map();
  private maxSize = 10 * 1024 * 1024; // 10MB缓存限制

  /**
   * 压缩图片
   */
  async compressImage(
    file: File,
    options: ImageOptimizationOptions = {}
  ): Promise<Blob> {
    const {
      maxWidth = 1920,
      maxHeight = 1080,
      quality = 0.8,
      format = 'image/jpeg',
    } = options;

    return new Promise((resolve, reject) => {
      const img = new Image();
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');

      if (!ctx) {
        reject(new Error('无法获取canvas context'));
        return;
      }

      img.onload = () => {
        // 计算新尺寸（保持宽高比）
        let { width, height } = this.calculateSize(
          img.width,
          img.height,
          maxWidth,
          maxHeight
        );

        canvas.width = width;
        canvas.height = height;

        // 绘制图片
        ctx.drawImage(img, 0, 0, width, height);

        // 转换为Blob
        canvas.toBlob(
          (blob) => {
            if (blob) {
              resolve(blob);
            } else {
              reject(new Error('图片压缩失败'));
            }
          },
          format,
          quality
        );
      };

      img.onerror = () => reject(new Error('图片加载失败'));

      // 加载图片
      const reader = new FileReader();
      reader.onload = (e) => {
        img.src = e.target?.result as string;
      };
      reader.readAsDataURL(file);
    });
  }

  /**
   * 计算缩放后的尺寸
   */
  private calculateSize(
    width: number,
    height: number,
    maxWidth: number,
    maxHeight: number
  ): { width: number; height: number } {
    let newWidth = width;
    let newHeight = height;

    // 缩放以适应最大宽度
    if (newWidth > maxWidth) {
      const ratio = maxWidth / newWidth;
      newWidth = maxWidth;
      newHeight = newHeight * ratio;
    }

    // 缩放以适应最大高度
    if (newHeight > maxHeight) {
      const ratio = maxHeight / newHeight;
      newHeight = maxHeight;
      newWidth = newWidth * ratio;
    }

    return { width: Math.round(newWidth), height: Math.round(newHeight) };
  }

  /**
   * 获取图片信息
   */
  async getImageInfo(file: File | Blob): Promise<ImageInfo> {
    return new Promise((resolve, reject) => {
      const img = new Image();

      img.onload = () => {
        resolve({
          width: img.width,
          height: img.height,
          size: file.size,
          type: file.type,
          aspectRatio: img.width / img.height,
        });
      };

      img.onerror = () => reject(new Error('无法获取图片信息'));

      const reader = new FileReader();
      reader.onload = (e) => {
        img.src = e.target?.result as string;
      };
      reader.readAsDataURL(file);
    });
  }

  /**
   * 生成响应式图片URL
   */
  generateResponsiveUrl(
    baseUrl: string,
    width: number,
    quality: number = 80
  ): string {
    // 假设后端支持图片处理参数
    const url = new URL(baseUrl, window.location.origin);
    url.searchParams.set('w', width.toString());
    url.searchParams.set('q', quality.toString());
    return url.toString();
  }

  /**
   * 生成srcset属性
   */
  generateSrcSet(
    baseUrl: string,
    sizes: number[] = [320, 640, 960, 1280, 1920],
    quality: number = 80
  ): string {
    return sizes
      .map((size) => {
        const url = this.generateResponsiveUrl(baseUrl, size, quality);
        return `${url} ${size}w`;
      })
      .join(', ');
  }

  /**
   * 计算最佳图片尺寸
   */
  calculateOptimalSize(containerWidth: number, devicePixelRatio: number = 1): number {
    const baseSize = containerWidth * devicePixelRatio;
    // 向上取整到最近的100
    return Math.ceil(baseSize / 100) * 100;
  }

  /**
   * 格式化文件大小
   */
  formatFileSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  /**
   * 缓存优化后的图片
   */
  cacheImage(key: string, dataUrl: string): void {
    // 检查缓存大小
    if (this.cache.size >= 100) {
      // 清除最旧的缓存
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }

    this.cache.set(key, dataUrl);
  }

  /**
   * 获取缓存的图片
   */
  getCachedImage(key: string): string | undefined {
    return this.cache.get(key);
  }

  /**
   * 清除缓存
   */
  clearCache(): void {
    this.cache.clear();
  }

  /**
   * 预加载图片
   */
  preloadImage(url: string): Promise<void> {
    return new Promise((resolve, reject) => {
      // 检查缓存
      const cached = this.getCachedImage(url);
      if (cached) {
        resolve();
        return;
      }

      const img = new Image();

      img.onload = () => {
        // 缓存图片
        this.cacheImage(url, url);
        resolve();
      };

      img.onerror = () => reject(new Error(`预加载失败: ${url}`));

      img.src = url;
    });
  }

  /**
   * 批量预加载图片
   */
  async preloadImages(urls: string[]): Promise<void> {
    const promises = urls.map((url) => this.preloadImage(url));
    await Promise.allSettled(promises);
  }

  /**
   * 检测WebP支持
   */
  checkWebPSupport(): Promise<boolean> {
    return new Promise((resolve) => {
      const webP = new Image();
      webP.onload = webP.onerror = () => {
        resolve(webP.height === 2);
      };
      webP.src =
        'data:image/webp;base64,UklGRjoAAABXRUJQVlA4IC4AAACyAgCdASoCAAIALmk0mk0iIiIiIgBoSygABc6WWgAA/veff/0PP8bA//LwYAAA';
    });
  }

  /**
   * 获取最佳图片格式
   */
  async getBestFormat(supportsWebP?: boolean): Promise<'image/webp' | 'image/jpeg'> {
    if (supportsWebP === undefined) {
      supportsWebP = await this.checkWebPSupport();
    }
    return supportsWebP ? 'image/webp' : 'image/jpeg';
  }
}

// 创建全局实例
export const imageOptimizer = new ImageOptimizer();

/**
 * 便捷函数：压缩图片
 */
export async function compressImage(
  file: File,
  options?: ImageOptimizationOptions
): Promise<Blob> {
  return imageOptimizer.compressImage(file, options);
}

/**
 * 便捷函数：获取图片信息
 */
export async function getImageInfo(file: File | Blob): Promise<ImageInfo> {
  return imageOptimizer.getImageInfo(file);
}

/**
 * 便捷函数：生成srcset
 */
export function generateSrcSet(
  baseUrl: string,
  sizes?: number[],
  quality?: number
): string {
  return imageOptimizer.generateSrcSet(baseUrl, sizes, quality);
}

/**
 * 便捷函数：预加载图片
 */
export async function preloadImage(url: string): Promise<void> {
  return imageOptimizer.preloadImage(url);
}

/**
 * 便捷函数：批量预加载
 */
export async function preloadImages(urls: string[]): Promise<void> {
  return imageOptimizer.preloadImages(urls);
}
