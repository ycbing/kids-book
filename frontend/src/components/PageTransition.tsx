// frontend/src/components/PageTransition.tsx
import React, { useRef, useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';

interface PageTransitionProps {
  children: React.ReactNode;
  type?: 'fade' | 'slide' | 'scale' | 'none';
  duration?: number;
}

/**
 * 页面过渡动画组件
 */
export const PageTransition: React.FC<PageTransitionProps> = ({
  children,
  type = 'fade',
  duration = 300,
}) => {
  const location = useLocation();
  const [displayChildren, setDisplayChildren] = useState(children);
  const [isAnimating, setIsAnimating] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (children !== displayChildren) {
      // 开始退出动画
      if (type !== 'none' && containerRef.current) {
        setIsAnimating(true);
        containerRef.current.classList.add('page-exit');

        setTimeout(() => {
          setDisplayChildren(children);
          setIsAnimating(false);

          // 进入动画
          if (containerRef.current) {
            containerRef.current.classList.remove('page-exit');
            containerRef.current.classList.add('page-enter');

            setTimeout(() => {
              if (containerRef.current) {
                containerRef.current.classList.remove('page-enter');
              }
            }, duration);
          }
        }, duration);
      } else {
        setDisplayChildren(children);
      }
    }
  }, [children, displayChildren, type, duration]);

  const animations = {
    fade: `
      .page-enter {
        animation: fadeIn ${duration}ms ease-in;
      }
      .page-exit {
        animation: fadeOut ${duration}ms ease-in;
      }
      @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
      }
      @keyframes fadeOut {
        from { opacity: 1; }
        to { opacity: 0; }
      }
    `,
    slide: `
      .page-enter {
        animation: slideInRight ${duration}ms ease-in;
      }
      .page-exit {
        animation: slideOutLeft ${duration}ms ease-in;
      }
      @keyframes slideInRight {
        from { transform: translateX(30px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
      }
      @keyframes slideOutLeft {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(-30px); opacity: 0; }
      }
    `,
    scale: `
      .page-enter {
        animation: scaleIn ${duration}ms ease-in;
      }
      .page-exit {
        animation: scaleOut ${duration}ms ease-in;
      }
      @keyframes scaleIn {
        from { transform: scale(0.95); opacity: 0; }
        to { transform: scale(1); opacity: 1; }
      }
      @keyframes scaleOut {
        from { transform: scale(1); opacity: 1; }
        to { transform: scale(0.95); opacity: 0; }
      }
    `,
  };

  return (
    <>
      <style>{animations[type]}</style>
      <div
        ref={containerRef}
        className={`page-transition ${isAnimating ? 'animating' : ''}`}
        style={{
          transition: type === 'none' ? 'none' : `all ${duration}ms ease-in-out`,
        }}
      >
        {displayChildren}
      </div>
    </>
  );
};

/**
 * 页面切换进度条
 */
export const PageProgressBar: React.FC = () => {
  const [progress, setProgress] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const location = useLocation();

  useEffect(() => {
    setIsLoading(true);
    setProgress(0);

    // 模拟加载进度
    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) return prev;
        return prev + Math.random() * 10;
      });
    }, 100);

    // 完成加载
    const timeout = setTimeout(() => {
      clearInterval(timer);
      setProgress(100);
      setTimeout(() => {
        setIsLoading(false);
        setProgress(0);
      }, 300);
    }, 500);

    return () => {
      clearInterval(timer);
      clearTimeout(timeout);
    };
  }, [location.pathname]);

  if (!isLoading && progress === 0) return null;

  return (
    <div className="page-progress-bar">
      <div
        className="page-progress-fill"
        style={{
          width: `${progress}%`,
          transition: 'width 0.3s ease',
        }}
      />
      <style>{`
        .page-progress-bar {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          height: 3px;
          background: #e0e0e0;
          z-index: 9999;
        }

        .page-progress-fill {
          height: 100%;
          background: linear-gradient(90deg, #0066cc, #00bcd4);
          box-shadow: 0 0 10px rgba(0, 102, 204, 0.5);
        }
      `}</style>
    </div>
  );
};

/**
 * 页面加载骨架屏
 */
interface PageSkeletonProps {
  type?: 'list' | 'detail' | 'form';
}

export const PageSkeleton: React.FC<PageSkeletonProps> = ({ type = 'list' }) => {
  return (
    <div className="page-skeleton" style={{ padding: '20px' }}>
      {type === 'list' && (
        <>
          <div
            style={{
              height: '40px',
              width: '200px',
              background: '#e0e0e0',
              borderRadius: '4px',
              marginBottom: '20px',
            }}
          />
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
              gap: '20px',
            }}
          >
            {Array.from({ length: 8 }).map((_, i) => (
              <div
                key={i}
                style={{
                  height: '300px',
                  background: '#f5f5f5',
                  borderRadius: '8px',
                }}
              />
            ))}
          </div>
        </>
      )}

      {type === 'detail' && (
        <>
          <div
            style={{
              height: '40px',
              width: '60%',
              background: '#e0e0e0',
              borderRadius: '4px',
              marginBottom: '20px',
            }}
          />
          <div style={{ display: 'flex', gap: '20px' }}>
            <div
              style={{
                width: '300px',
                height: '400px',
                background: '#f5f5f5',
                borderRadius: '8px',
              }}
            />
            <div style={{ flex: 1 }}>
              <div
                style={{
                  height: '24px',
                  width: '80%',
                  background: '#e0e0e0',
                  borderRadius: '4px',
                  marginBottom: '12px',
                }}
              />
              <div
                style={{
                  height: '16px',
                  width: '100%',
                  background: '#f5f5f5',
                  borderRadius: '4px',
                  marginBottom: '8px',
                }}
              />
              <div
                style={{
                  height: '16px',
                  width: '90%',
                  background: '#f5f5f5',
                  borderRadius: '4px',
                  marginBottom: '8px',
                }}
              />
            </div>
          </div>
        </>
      )}

      {type === 'form' && (
        <>
          <div
            style={{
              height: '40px',
              width: '200px',
              background: '#e0e0e0',
              borderRadius: '4px',
              marginBottom: '30px',
            }}
          />
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} style={{ marginBottom: '20px' }}>
              <div
                style={{
                  height: '16px',
                  width: '100px',
                  background: '#e0e0e0',
                  borderRadius: '4px',
                  marginBottom: '8px',
                }}
              />
              <div
                style={{
                  height: '40px',
                  width: '100%',
                  background: '#f5f5f5',
                  borderRadius: '4px',
                }}
              />
            </div>
          ))}
        </>
      )}
    </div>
  );
};

export default PageTransition;
