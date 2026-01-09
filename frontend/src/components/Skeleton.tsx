// frontend/src/components/Skeleton.tsx
import React from 'react';

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  variant?: 'text' | 'rectangular' | 'circular';
  className?: string;
  animation?: 'pulse' | 'wave' | 'none';
}

/**
 * 基础骨架屏组件
 */
export const Skeleton: React.FC<SkeletonProps> = ({
  width = '100%',
  height = '1em',
  variant = 'text',
  className = '',
  animation = 'pulse',
}) => {
  const style: React.CSSProperties = {
    width: typeof width === 'number' ? `${width}px` : width,
    height: typeof height === 'number' ? `${height}px` : height,
  };

  const variantClass = `skeleton-${variant}`;
  const animationClass = animation !== 'none' ? `animate-${animation}` : '';

  return (
    <div
      className={`skeleton ${variantClass} ${animationClass} ${className}`}
      style={style}
    >
      <style>{`
        .skeleton {
          background: #e0e0e0;
          display: inline-block;
        }

        .skeleton-text {
          border-radius: 4px;
          height: 1em;
        }

        .skeleton-rectangular {
          border-radius: 4px;
        }

        .skeleton-circular {
          border-radius: 50%;
        }

        .animate-pulse {
          animation: skeleton-pulse 1.5s ease-in-out infinite;
        }

        @keyframes skeleton-pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.5;
          }
        }

        .animate-wave {
          position: relative;
          overflow: hidden;
        }

        .animate-wave::after {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: linear-gradient(
            90deg,
            transparent,
            rgba(255, 255, 255, 0.5),
            transparent
          );
          animation: skeleton-wave 1.5s infinite;
        }

        @keyframes skeleton-wave {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(100%);
          }
        }
      `}</style>
    </div>
  );
};

/**
 * 文本骨架屏
 */
interface TextSkeletonProps {
  lines?: number;
  className?: string;
}

export const TextSkeleton: React.FC<TextSkeletonProps> = ({
  lines = 3,
  className = '',
}) => {
  return (
    <div className={`text-skeleton ${className}`}>
      {Array.from({ length: lines }).map((_, index) => (
        <Skeleton
          key={index}
          height="1em"
          width={index === lines - 1 ? '60%' : '100%'}
          variant="text"
        />
      ))}

      <style>{`
        .text-skeleton {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
      `}</style>
    </div>
  );
};

/**
 * 卡片骨架屏
 */
interface CardSkeletonProps {
  showAvatar?: boolean;
  showTitle?: boolean;
  showDescription?: boolean;
  lines?: number;
  className?: string;
}

export const CardSkeleton: React.FC<CardSkeletonProps> = ({
  showAvatar = true,
  showTitle = true,
  showDescription = true,
  lines = 3,
  className = '',
}) => {
  return (
    <div className={`card-skeleton ${className}`}>
      {showAvatar && <Skeleton width={40} height={40} variant="circular" />}
      <div className="card-content">
        {showTitle && <Skeleton height={24} width="60%" />}
        {showDescription && <TextSkeleton lines={lines} />}
      </div>

      <style>{`
        .card-skeleton {
          display: flex;
          gap: 16px;
          padding: 16px;
          background: #fff;
          border: 1px solid #e0e0e0;
          border-radius: 8px;
        }

        .card-content {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
      `}</style>
    </div>
  );
};

/**
 * 列表骨架屏
 */
interface ListSkeletonProps {
  count?: number;
  className?: string;
}

export const ListSkeleton: React.FC<ListSkeletonProps> = ({
  count = 5,
  className = '',
}) => {
  return (
    <div className={`list-skeleton ${className}`}>
      {Array.from({ length: count }).map((_, index) => (
        <CardSkeleton key={index} showAvatar={false} />
      ))}

      <style>{`
        .list-skeleton {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
      `}</style>
    </div>
  );
};

/**
 * 绘本卡片骨架屏
 */
interface BookCardSkeletonProps {
  className?: string;
}

export const BookCardSkeleton: React.FC<BookCardSkeletonProps> = ({
  className = '',
}) => {
  return (
    <div className={`book-card-skeleton ${className}`}>
      <Skeleton width="100%" height={200} variant="rectangular" />
      <div className="book-info">
        <Skeleton height={24} width="80%" />
        <Skeleton height={16} width="60%" />
        <Skeleton height={16} width="40%" />
      </div>

      <style>{`
        .book-card-skeleton {
          background: #fff;
          border: 1px solid #e0e0e0;
          border-radius: 8px;
          overflow: hidden;
        }

        .book-info {
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
      `}</style>
    </div>
  );
};

/**
 * 绘本网格骨架屏
 */
interface BookGridSkeletonProps {
  cols?: number;
  rows?: number;
  className?: string;
}

export const BookGridSkeleton: React.FC<BookGridSkeletonProps> = ({
  cols = 4,
  rows = 2,
  className = '',
}) => {
  const total = cols * rows;

  return (
    <div
      className={`book-grid-skeleton ${className}`}
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${cols}, 1fr)`,
        gap: '16px',
      }}
    >
      {Array.from({ length: total }).map((_, index) => (
        <BookCardSkeleton key={index} />
      ))}
    </div>
  );
};

/**
 * 页面骨架屏
 */
interface PageSkeletonProps {
  className?: string;
}

export const PageSkeleton: React.FC<PageSkeletonProps> = ({ className = '' }) => {
  return (
    <div className={`page-skeleton ${className}`}>
      {/* 标题骨架 */}
      <Skeleton height={32} width="30%" className="page-header-skeleton" />

      {/* 绘本网格骨架 */}
      <div className="page-content-skeleton">
        <BookGridSkeleton cols={4} rows={2} />
      </div>

      <style>{`
        .page-skeleton {
          display: flex;
          flex-direction: column;
          gap: 24px;
          padding: 24px;
        }

        .page-header-skeleton {
          margin-bottom: 16px;
        }

        .page-content-skeleton {
          width: 100%;
        }
      `}</style>
    </div>
  );
};

/**
 * 表格骨架屏
 */
interface TableSkeletonProps {
  rows?: number;
  cols?: number;
  className?: string;
}

export const TableSkeleton: React.FC<TableSkeletonProps> = ({
  rows = 5,
  cols = 4,
  className = '',
}) => {
  return (
    <div className={`table-skeleton ${className}`}>
      <div className="table-header">
        {Array.from({ length: cols }).map((_, index) => (
          <Skeleton key={`header-${index}`} height={32} width="100%" />
        ))}
      </div>
      <div className="table-body">
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div key={`row-${rowIndex}`} className="table-row">
            {Array.from({ length: cols }).map((_, colIndex) => (
              <Skeleton key={`cell-${rowIndex}-${colIndex}`} height={40} />
            ))}
          </div>
        ))}
      </div>

      <style>{`
        .table-skeleton {
          width: 100%;
          border: 1px solid #e0e0e0;
          border-radius: 8px;
          overflow: hidden;
        }

        .table-header {
          display: grid;
          grid-template-columns: repeat(${cols}, 1fr);
          gap: 1px;
          background: #f5f5f5;
          padding: 12px;
        }

        .table-body {
          display: flex;
          flex-direction: column;
        }

        .table-row {
          display: grid;
          grid-template-columns: repeat(${cols}, 1fr);
          gap: 1px;
          padding: 12px;
          border-top: 1px solid #e0e0e0;
        }
      `}</style>
    </div>
  );
};

export default Skeleton;
