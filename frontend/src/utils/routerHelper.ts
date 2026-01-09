// frontend/src/utils/routerHelper.ts
import { useNavigate, useLocation, useParams, NavigateFunction } from 'react-router-dom';

/**
 * 路由工具类
 */
export class RouterHelper {
  private navigate: NavigateFunction;

  constructor(navigate: NavigateFunction) {
    this.navigate = navigate;
  }

  /**
   * 导航到指定路径
   */
  go(path: string, options?: { replace?: boolean }) {
    this.navigate(path, { replace: options?.replace });
  }

  /**
   * 返回上一页
   */
  back() {
    this.navigate(-1);
  }

  /**
   * 前进到下一页
   */
  forward() {
    this.navigate(1);
  }

  /**
   * 刷新当前页
   */
  refresh() {
    this.navigate(0);
  }

  /**
   * 跳转到首页
   */
  goHome() {
    this.navigate('/');
  }

  /**
   * 跳转到404页面
   */
  goNotFound() {
    this.navigate('/not-found', { replace: true });
  }

  /**
   * 跳转到登录页（带重定向）
   */
  goLogin(redirectTo?: string) {
    const params = redirectTo ? `?redirect=${encodeURIComponent(redirectTo)}` : '';
    this.navigate(`/login${params}`);
  }

  /**
   * 带查询参数跳转
   */
  goWithQuery(path: string, params: Record<string, string | number>) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      searchParams.set(key, String(value));
    });
    this.navigate(`${path}?${searchParams.toString()}`);
  }

  /**
   * 跳转到绘本详情
   */
  goBookDetail(bookId: number | string) {
    this.navigate(`/book/${bookId}`);
  }

  /**
   * 跳转到创作页面
   */
  goCreate() {
    this.navigate('/create');
  }

  /**
   * 跳转到个人中心
   */
  goProfile() {
    this.navigate('/profile');
  }

  /**
   * 跳转到设置页面
   */
  goSettings() {
    this.navigate('/settings');
  }
}

/**
 * 使用路由工具的Hook
 */
export const useRouter = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const params = useParams();

  const router = new RouterHelper(navigate);

  return {
    router,
    navigate,
    location,
    params,
    pathname: location.pathname,
    search: location.search,
    hash: location.hash,
    state: location.state as any,
  };
};

/**
 * 页面标题管理Hook
 */
export const usePageTitle = (title: string | undefined) => {
  React.useEffect(() => {
    if (title) {
      document.title = title;
    }
  }, [title]);
};

/**
 * 获取查询参数Hook
 */
export const useQueryParams = <T extends Record<string, string>>() => {
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);

  const params = {} as T;

  searchParams.forEach((value, key) => {
    (params as any)[key] = value;
  });

  return params;
};

/**
 * 返回上一页Hook
 */
export const useGoBack = (fallbackPath = '/') => {
  const navigate = useNavigate();

  return () => {
    if (window.history.length > 1) {
      navigate(-1);
    } else {
      navigate(fallbackPath);
    }
  };
};

/**
 * 路由切换确认Hook
 */
export const useRouteLeavingGuard = (
  when: boolean,
  message = '确定要离开吗？未保存的更改将会丢失。'
) => {
  const navigate = useNavigate();
  const location = useLocation();

  React.useEffect(() => {
    const unblock = (window as any).navigation?.blocks?.add((block: any) => {
      if (when) {
        const confirm = window.confirm(message);
        if (confirm) {
          // 允许导航
          block.transition?.();
        } else {
          // 阻止导航
          block.transition?.cancel();
        }
      }
    });

    // 浏览器原生的beforeunload事件
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (when) {
        e.preventDefault();
        e.returnValue = message;
        return message;
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      if (unblock) {
        unblock();
      }
    };
  }, [when, message, navigate, location]);
};

/**
 * 路由历史记录管理
 */
export class RouteHistory {
  private history: string[] = [];
  private maxHistory = 50;

  add(path: string) {
    this.history.push(path);
    if (this.history.length > this.maxHistory) {
      this.history.shift();
    }
  }

  getPrevious(): string | null {
    if (this.history.length < 2) return null;
    return this.history[this.history.length - 2];
  }

  canGoBack(): boolean {
    return this.history.length >= 2;
  }

  clear() {
    this.history = [];
  }
}

// 全局路由历史实例
export const routeHistory = new RouteHistory();

/**
 * 自动路由历史记录Hook
 */
export const useRouteHistory = () => {
  const location = useLocation();

  React.useEffect(() => {
    routeHistory.add(location.pathname);
  }, [location.pathname]);

  return {
    canGoBack: routeHistory.canGoBack(),
    getPrevious: () => routeHistory.getPrevious(),
  };
};

/**
 * 延迟导航Hook
 */
export const useDelayedNavigate = (delay: number = 300) => {
  const navigate = useNavigate();
  const timeoutRef = useRef<NodeJS.Timeout>();

  const delayedNavigate = (path: string, options?: { replace?: boolean }) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      navigate(path, { replace: options?.replace });
    }, delay);
  };

  React.useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return delayedNavigate;
};

/**
 * 页面可见性Hook
 */
export const usePageVisibility = () => {
  const [isVisible, setIsVisible] = useState(!document.hidden);

  React.useEffect(() => {
    const handleVisibilityChange = () => {
      setIsVisible(!document.hidden);
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  return isVisible;
};

// 导出React
import React from 'react';
