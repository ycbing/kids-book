// frontend/src/components/ErrorBoundary.tsx
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AppError } from '../utils/errorHandler';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * React错误边界组件
 * 捕获子组件树中的JavaScript错误，记录错误日志，并显示备用UI
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    // 更新state使下一次渲染能够显示降级后的UI
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // 可以将错误日志上报给服务器
    console.error('❌ Error Boundary caught an error:', error);
    console.error('Component Stack:', errorInfo.componentStack);

    // 保存错误信息到state
    this.setState({
      errorInfo,
    });

    // 调用自定义错误回调
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // TODO: 上报错误到服务器
    // this.reportErrorToServer(error, errorInfo);
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // 使用自定义fallback或默认错误页面
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <ErrorFallback
          error={this.state.error}
          errorInfo={this.state.errorInfo}
          onReset={this.handleReset}
          onReload={this.handleReload}
        />
      );
    }

    return this.props.children;
  }
}

/**
 * 默认错误页面组件
 */
interface ErrorFallbackProps {
  error: Error | null;
  errorInfo: ErrorInfo | null;
  onReset: () => void;
  onReload: () => void;
}

const ErrorFallback: React.FC<ErrorFallbackProps> = ({
  error,
  errorInfo,
  onReset,
  onReload,
}) => {
  const isDevelopment = process.env.NODE_ENV === 'development';

  return (
    <div className="error-boundary-fallback">
      <div className="error-container">
        <div className="error-icon">⚠️</div>
        <h1 className="error-title">出错了</h1>
        <p className="error-message">
          抱歉，应用程序遇到了一个错误。您可以尝试重置或刷新页面。
        </p>

        {/* 开发环境显示详细错误信息 */}
        {isDevelopment && error && (
          <details className="error-details">
            <summary>错误详情</summary>
            <div className="error-details-content">
              <div className="error-section">
                <h4>错误信息:</h4>
                <pre>{error.toString()}</pre>
              </div>

              {errorInfo && (
                <div className="error-section">
                  <h4>组件堆栈:</h4>
                  <pre>{errorInfo.componentStack}</pre>
                </div>
              )}

              {error.stack && (
                <div className="error-section">
                  <h4>错误堆栈:</h4>
                  <pre>{error.stack}</pre>
                </div>
              )}
            </div>
          </details>
        )}

        <div className="error-actions">
          <button className="btn btn-primary" onClick={onReset}>
            重置
          </button>
          <button className="btn btn-secondary" onClick={onReload}>
            刷新页面
          </button>
        </div>
      </div>

      <style>{`
        .error-boundary-fallback {
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 100vh;
          padding: 20px;
          background-color: #f5f5f5;
        }

        .error-container {
          max-width: 600px;
          background: white;
          border-radius: 8px;
          padding: 40px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          text-align: center;
        }

        .error-icon {
          font-size: 64px;
          margin-bottom: 20px;
        }

        .error-title {
          font-size: 24px;
          color: #333;
          margin-bottom: 16px;
        }

        .error-message {
          color: #666;
          line-height: 1.6;
          margin-bottom: 24px;
        }

        .error-details {
          margin: 24px 0;
          text-align: left;
        }

        .error-details summary {
          cursor: pointer;
          font-weight: bold;
          color: #0066cc;
          padding: 8px;
          background: #f0f0f0;
          border-radius: 4px;
          user-select: none;
        }

        .error-details-content {
          margin-top: 12px;
          padding: 16px;
          background: #f9f9f9;
          border-radius: 4px;
          overflow: auto;
        }

        .error-section {
          margin-bottom: 16px;
        }

        .error-section:last-child {
          margin-bottom: 0;
        }

        .error-section h4 {
          margin: 0 0 8px 0;
          font-size: 14px;
          color: #333;
        }

        .error-section pre {
          margin: 0;
          padding: 12px;
          background: #fff;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 12px;
          line-height: 1.4;
          overflow-x: auto;
        }

        .error-actions {
          display: flex;
          gap: 12px;
          justify-content: center;
          margin-top: 24px;
        }

        .btn {
          padding: 12px 24px;
          border: none;
          border-radius: 4px;
          font-size: 16px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-primary {
          background: #0066cc;
          color: white;
        }

        .btn-primary:hover {
          background: #0052a3;
        }

        .btn-secondary {
          background: #e0e0e0;
          color: #333;
        }

        .btn-secondary:hover {
          background: #d0d0d0;
        }
      `}</style>
    </div>
  );
};

/**
 * 高阶组件：为组件添加错误边界
 */
export function withErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  fallback?: ReactNode,
  onError?: (error: Error, errorInfo: ErrorInfo) => void
) {
  const WithErrorBoundary = (props: P) => {
    return (
      <ErrorBoundary fallback={fallback} onError={onError}>
        <WrappedComponent {...props} />
      </ErrorBoundary>
    );
  };

  WithErrorBoundary.displayName = `withErrorBoundary(${
    WrappedComponent.displayName || WrappedComponent.name || 'Component'
  })`;

  return WithErrorBoundary;
}

/**
 * Hook: 在函数组件中捕获错误
 */
export function useErrorHandler() {
  const [error, setError] = React.useState<Error | null>(null);

  const handleError = React.useCallback((error: Error) => {
    setError(error);
    // 抛出错误让ErrorBoundary捕获
    throw error;
  }, []);

  const resetError = React.useCallback(() => {
    setError(null);
  }, []);

  return {
    error,
    handleError,
    resetError,
  };
}

export default ErrorBoundary;
