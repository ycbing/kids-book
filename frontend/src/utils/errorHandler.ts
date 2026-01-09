// frontend/src/utils/errorHandler.ts
import { AxiosError } from 'axios';
import { uiActions } from '../stores/uiStore';

/**
 * 错误类型定义
 */
export enum ErrorType {
  NETWORK = 'NETWORK_ERROR',
  API = 'API_ERROR',
  VALIDATION = 'VALIDATION_ERROR',
  AUTH = 'AUTH_ERROR',
  PERMISSION = 'PERMISSION_ERROR',
  NOT_FOUND = 'NOT_FOUND_ERROR',
  SERVER = 'SERVER_ERROR',
  UNKNOWN = 'UNKNOWN_ERROR',
}

/**
 * 应用错误类
 */
export class AppError extends Error {
  type: ErrorType;
  code?: string;
  statusCode?: number;
  originalError?: Error;

  constructor(
    message: string,
    type: ErrorType = ErrorType.UNKNOWN,
    code?: string,
    statusCode?: number,
    originalError?: Error
  ) {
    super(message);
    this.name = 'AppError';
    this.type = type;
    this.code = code;
    this.statusCode = statusCode;
    this.originalError = originalError;

    // 保持正确的堆栈跟踪
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, AppError);
    }
  }
}

/**
 * 错误处理配置
 */
interface ErrorHandlerConfig {
  showNotification?: boolean;
  logToConsole?: boolean;
  reportToServer?: boolean;
  onError?: (error: AppError) => void;
}

const defaultConfig: ErrorHandlerConfig = {
  showNotification: true,
  logToConsole: true,
  reportToServer: false,
};

/**
 * 全局错误处理器
 */
class ErrorHandler {
  private config: ErrorHandlerConfig;

  constructor(config: ErrorHandlerConfig = {}) {
    this.config = { ...defaultConfig, ...config };
  }

  /**
   * 更新配置
   */
  updateConfig(config: Partial<ErrorHandlerConfig>) {
    this.config = { ...this.config, ...config };
  }

  /**
   * 处理错误
   */
  handle(error: Error | AxiosError | unknown, context?: string): AppError {
    let appError: AppError;

    // 转换为AppError
    if (error instanceof AppError) {
      appError = error;
    } else if (this.isAxiosError(error)) {
      appError = this.handleAxiosError(error);
    } else if (error instanceof Error) {
      appError = new AppError(
        error.message,
        ErrorType.UNKNOWN,
        undefined,
        undefined,
        error
      );
    } else {
      appError = new AppError(
        String(error),
        ErrorType.UNKNOWN
      );
    }

    // 添加上下文信息
    if (context) {
      appError.message = `[${context}] ${appError.message}`;
    }

    // 日志记录
    if (this.config.logToConsole) {
      this.logError(appError);
    }

    // 显示通知
    if (this.config.showNotification) {
      this.showErrorNotification(appError);
    }

    // 上报错误
    if (this.config.reportToServer) {
      this.reportError(appError);
    }

    // 调用自定义回调
    if (this.config.onError) {
      this.config.onError(appError);
    }

    return appError;
  }

  /**
   * 处理Axios错误
   */
  private handleAxiosError(error: AxiosError): AppError {
    const response = error.response;

    if (!response) {
      // 网络错误或请求超时
      if (error.code === 'ECONNABORTED') {
        return new AppError(
          '请求超时，请稍后重试',
          ErrorType.NETWORK,
          error.code,
          undefined,
          error
        );
      }
      return new AppError(
        '网络连接失败，请检查网络设置',
        ErrorType.NETWORK,
        error.code,
        undefined,
        error
      );
    }

    const { status, data } = response;
    const errorMessage = this.extractErrorMessage(data);

    // 根据状态码分类错误
    switch (status) {
      case 400:
        return new AppError(
          errorMessage || '请求参数错误',
          ErrorType.VALIDATION,
          'VALIDATION_ERROR',
          status,
          error
        );

      case 401:
        return new AppError(
          '未授权，请重新登录',
          ErrorType.AUTH,
          'UNAUTHORIZED',
          status,
          error
        );

      case 403:
        return new AppError(
          errorMessage || '没有权限执行此操作',
          ErrorType.PERMISSION,
          'FORBIDDEN',
          status,
          error
        );

      case 404:
        return new AppError(
          errorMessage || '请求的资源不存在',
          ErrorType.NOT_FOUND,
          'NOT_FOUND',
          status,
          error
        );

      case 422:
        return new AppError(
          errorMessage || '数据验证失败',
          ErrorType.VALIDATION,
          'UNPROCESSABLE_ENTITY',
          status,
          error
        );

      case 429:
        return new AppError(
          '请求过于频繁，请稍后再试',
          ErrorType.API,
          'RATE_LIMIT_EXCEEDED',
          status,
          error
        );

      case 500:
        return new AppError(
          '服务器内部错误，请稍后重试',
          ErrorType.SERVER,
          'INTERNAL_SERVER_ERROR',
          status,
          error
        );

      case 502:
      case 503:
      case 504:
        return new AppError(
          '服务暂时不可用，请稍后重试',
          ErrorType.SERVER,
          'SERVICE_UNAVAILABLE',
          status,
          error
        );

      default:
        return new AppError(
          errorMessage || `请求失败 (${status})`,
          ErrorType.API,
          `HTTP_${status}`,
          status,
          error
        );
    }
  }

  /**
   * 从响应数据中提取错误消息
   */
  private extractErrorMessage(data: any): string {
    if (typeof data === 'string') {
      return data;
    }

    if (typeof data === 'object' && data !== null) {
      // 尝试常见的错误字段
      return (
        data.detail ||
        data.message ||
        data.error ||
        data.error_message ||
        ''
      );
    }

    return '';
  }

  /**
   * 判断是否为Axios错误
   */
  private isAxiosError(error: unknown): error is AxiosError {
    return (
      typeof error === 'object' &&
      error !== null &&
      'isAxiosError' in error &&
      (error as AxiosError).isAxiosError === true
    );
  }

  /**
   * 记录错误到控制台
   */
  private logError(error: AppError) {
    const style = 'color: #ff0000; font-weight: bold;';
    console.group('%c❌ Error', style);
    console.error('Type:', error.type);
    console.error('Message:', error.message);
    if (error.code) console.error('Code:', error.code);
    if (error.statusCode) console.error('Status:', error.statusCode);
    if (error.originalError) console.error('Original:', error.originalError);
    console.groupEnd();
  }

  /**
   * 显示错误通知
   */
  private showErrorNotification(error: AppError) {
    const message = this.getUserFriendlyMessage(error);
    const duration = this.getNotificationDuration(error);

    switch (error.type) {
      case ErrorType.VALIDATION:
      case ErrorType.PERMISSION:
        uiActions.warning(message, duration);
        break;

      case ErrorType.AUTH:
        uiActions.warning(message, duration);
        // 跳转到登录页
        // TODO: 实现登录跳转
        break;

      case ErrorType.NOT_FOUND:
        uiActions.info(message, duration);
        break;

      case ErrorType.NETWORK:
      case ErrorType.SERVER:
      case ErrorType.API:
        uiActions.error(message, duration);
        break;

      default:
        uiActions.error(message, duration);
    }
  }

  /**
   * 获取用户友好的错误消息
   */
  private getUserFriendlyMessage(error: AppError): string {
    // 错误消息已经够友好了，直接返回
    return error.message;
  }

  /**
   * 获取通知显示时长
   */
  private getNotificationDuration(error: AppError): number {
    // 严重错误显示更长时间
    switch (error.type) {
      case ErrorType.NETWORK:
      case ErrorType.SERVER:
        return 5000;
      default:
        return 3000;
    }
  }

  /**
   * 上报错误到服务器
   */
  private async reportError(error: AppError) {
    try {
      // TODO: 实现错误上报到服务器的逻辑
      // await axios.post('/api/v1/errors', {
      //   type: error.type,
      //   message: error.message,
      //   code: error.code,
      //   statusCode: error.statusCode,
      //   stack: error.stack,
      //   userAgent: navigator.userAgent,
      //   url: window.location.href,
      //   timestamp: new Date().toISOString(),
      // });
    } catch (reportError) {
      console.error('Failed to report error:', reportError);
    }
  }

  /**
   * 异步操作包装器
   */
  async wrapAsync<T>(
    asyncFn: () => Promise<T>,
    context?: string
  ): Promise<T> {
    try {
      return await asyncFn();
    } catch (error) {
      throw this.handle(error, context);
    }
  }

  /**
   * 同步操作包装器
   */
  wrapSync<T>(
    syncFn: () => T,
    context?: string
  ): T {
    try {
      return syncFn();
    } catch (error) {
      throw this.handle(error, context);
    }
  }
}

// 创建全局实例
export const errorHandler = new ErrorHandler();

// 便捷函数
export const handleError = (error: Error | unknown, context?: string) => {
  return errorHandler.handle(error, context);
};

export const wrapAsync = <T>(
  asyncFn: () => Promise<T>,
  context?: string
) => {
  return errorHandler.wrapAsync(asyncFn, context);
};

export const wrapSync = <T>(
  syncFn: () => T,
  context?: string
) => {
  return errorHandler.wrapSync(syncFn, context);
};
