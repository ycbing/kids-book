// frontend/src/router/index.tsx
import React, { lazy, Suspense } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { ErrorBoundary } from "../components/ErrorBoundary";

/**
 * 路由配置
 */
export interface RouteConfig {
  path: string;
  element: React.LazyExoticComponent<React.ComponentType<any>>;
  title?: string;
  requireAuth?: boolean;
  exact?: boolean;
}

/**
 * 公共路由配置
 */
const routes: RouteConfig[] = [
  {
    path: "/",
    element: lazy(() => import("../pages/Home")),
    title: "首页 - AI绘本工坊",
  },
  {
    path: "/create",
    element: lazy(() => import("../pages/Create")),
    title: "创作绘本 - AI绘本工坊",
    requireAuth: false,
  },
  {
    path: "/book/:id",
    element: lazy(() => import("../pages/BookDetail")),
    title: "绘本详情 - AI绘本工坊",
  },
  {
    path: "/profile",
    element: lazy(() => import("../pages/Profile")),
    title: "个人中心 - AI绘本工坊",
    requireAuth: true,
  },
  {
    path: "/settings",
    element: lazy(() => import("../pages/Settings")),
    title: "设置 - AI绘本工坊",
    requireAuth: true,
  },
  {
    path: "/not-found",
    element: lazy(() => import("../pages/NotFound")),
    title: "页面未找到 - AI绘本工坊",
  },
];

/**
 * 加载中组件
 */
const PageLoading: React.FC = () => {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <LoadingSpinner text="加载中..." size="large" />
    </div>
  );
};

/**
 * 路由懒加载包装器
 */
const LazyRouteWrapper: React.FC<{
  children: React.ReactNode;
  title?: string;
}> = ({ children, title }) => {
  // 设置页面标题
  React.useEffect(() => {
    if (title) {
      document.title = title;
    }
  }, [title]);

  return (
    <Suspense fallback={<PageLoading />}>
      <ErrorBoundary>{children}</ErrorBoundary>
    </Suspense>
  );
};

/**
 * 路由守卫组件
 */
interface RouteGuardProps {
  requireAuth?: boolean;
  children: React.ReactNode;
}

const RouteGuard: React.FC<RouteGuardProps> = ({ requireAuth, children }) => {
  // 检查认证状态
  const isAuthenticated = () => {
    const token = localStorage.getItem("auth_token");
    return !!token;
  };

  if (requireAuth && !isAuthenticated()) {
    // 未认证，重定向到首页
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

/**
 * 渲染路由配置
 */
export const renderRoutes = (routeList: RouteConfig[] = routes) => {
  return routeList.map((route) => (
    <Route
      key={route.path}
      path={route.path}
      element={
        <LazyRouteWrapper title={route.title}>
          <RouteGuard requireAuth={route.requireAuth}>
            <route.element />
          </RouteGuard>
        </LazyRouteWrapper>
      }
    />
  ));
};

/**
 * App路由组件
 */
export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {renderRoutes(routes)}
      {/* 默认重定向到404 */}
      <Route path="*" element={<Navigate to="/not-found" replace />} />
    </Routes>
  );
};

export default routes;
