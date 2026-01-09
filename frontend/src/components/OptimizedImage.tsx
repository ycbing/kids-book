// frontend/src/components/OptimizedImage.tsx
import React, { useState, useRef, useEffect } from 'react';
import { imageOptimizer } from '../utils/imageOptimizer';

interface OptimizedImageProps {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  className?: string;
  placeholder?: 'blur' | 'color' | 'none';
  placeholderColor?: string;
  blurDataURL?: string;
  sizes?: string;
  quality?: number;
  loading?: 'lazy' | 'eager';
  fadeIn?: boolean;
  onLoad?: () => void;
  onError?: () => void;
}

/**
 * 优化的图片组件 - 支持懒加载、占位符、淡入效果
 */
export const OptimizedImage: React.FC<OptimizedImageProps> = ({
  src,
  alt,
  width,
  height,
  className = '',
  placeholder = 'blur',
  placeholderColor = '#e0e0e0',
  blurDataURL,
  sizes = '(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw',
  quality = 80,
  loading = 'lazy',
  fadeIn = true,
  onLoad,
  onError,
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInView, setIsInView] = useState(false);
  const [hasError, setHasError] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  // 使用Intersection Observer实现懒加载
  useEffect(() => {
    if (loading === 'eager') {
      setIsInView(true);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsInView(true);
            observer.disconnect();
          }
        });
      },
      {
        rootMargin: '50px', // 提前50px开始加载
      }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => observer.disconnect();
  }, [loading]);

  const handleLoad = () => {
    setIsLoaded(true);
    onLoad?.();
  };

  const handleError = () => {
    setHasError(true);
    onError?.();
  };

  // 生成srcset
  const srcSet = isInView
    ? imageOptimizer.generateSrcSet(src, undefined, quality)
    : undefined;

  // 占位符样式
  const placeholderStyle: React.CSSProperties = {
    backgroundColor: placeholderColor,
    backgroundImage: placeholder === 'blur' && blurDataURL ? `url(${blurDataURL})` : undefined,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    filter: placeholder === 'blur' ? 'blur(10px)' : undefined,
  };

  return (
    <div
      className={`optimized-image-container ${className}`}
      style={{ position: 'relative', overflow: 'hidden' }}
    >
      {/* 占位符 */}
      {(!isLoaded || !isInView) && placeholder !== 'none' && (
        <div
          className="image-placeholder"
          style={{
            ...placeholderStyle,
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            transition: fadeIn ? 'opacity 0.3s ease' : undefined,
            opacity: isLoaded ? 0 : 1,
          }}
        />
      )}

      {/* 实际图片 */}
      <img
        ref={imgRef}
        src={isInView ? src : undefined}
        srcSet={srcSet}
        sizes={sizes}
        alt={alt}
        width={width}
        height={height}
        loading={loading}
        onLoad={handleLoad}
        onError={handleError}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          opacity: isLoaded && fadeIn ? 1 : 0,
          transition: fadeIn ? 'opacity 0.3s ease' : undefined,
          display: hasError ? 'none' : 'block',
        }}
      />

      {/* 错误状态 */}
      {hasError && (
        <div
          className="image-error"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: placeholderColor,
            color: '#666',
            fontSize: '14px',
          }}
        >
          图片加载失败
        </div>
      )}

      <style>{`
        .optimized-image-container {
          display: inline-block;
        }

        .optimized-image-container img {
          display: block;
        }
      `}</style>
    </div>
  );
};

/**
 * 响应式图片组件
 */
interface ResponsiveImageProps extends Omit<OptimizedImageProps, 'sizes' | 'quality'> {
  breakpoints?: {
    width: number;
    size: string;
  }[];
}

export const ResponsiveImage: React.FC<ResponsiveImageProps> = ({
  src,
  alt,
  breakpoints = [
    { width: 320, size: '100vw' },
    { width: 640, size: '50vw' },
    { width: 960, size: '33vw' },
    { width: 1280, size: '25vw' },
  ],
  ...rest
}) => {
  // 生成sizes属性
  const sizes = breakpoints
    .map((bp) => `(max-width: ${bp.width}px) ${bp.size}`)
    .join(', ');

  return <OptimizedImage src={src} alt={alt} sizes={sizes} {...rest} />;
};

/**
 * 图片画廊组件
 */
interface ImageGalleryProps {
  images: Array<{
    src: string;
    alt: string;
    thumb?: string;
  }>;
  className?: string;
  gap?: number;
  columns?: number;
  onImageClick?: (index: number) => void;
}

export const ImageGallery: React.FC<ImageGalleryProps> = ({
  images,
  className = '',
  gap = 16,
  columns = 3,
  onImageClick,
}) => {
  return (
    <div
      className={`image-gallery ${className}`}
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${columns}, 1fr)`,
        gap: `${gap}px`,
      }}
    >
      {images.map((image, index) => (
        <div
          key={index}
          className="gallery-item"
          style={{ position: 'relative', paddingTop: '100%' }} // 1:1 宽高比
          onClick={() => onImageClick?.(index)}
        >
          <OptimizedImage
            src={image.src}
            alt={image.alt}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
            }}
            className="cursor-pointer"
          />
        </div>
      ))}

      <style>{`
        .image-gallery {
          width: 100%;
        }

        .gallery-item {
          cursor: pointer;
          transition: transform 0.2s ease;
        }

        .gallery-item:hover {
          transform: scale(1.02);
        }

        .cursor-pointer {
          cursor: pointer;
        }
      `}</style>
    </div>
  );
};

/**
 * 图片预览组件（带放大功能）
 */
interface ImagePreviewProps {
  src: string;
  alt: string;
  isOpen: boolean;
  onClose: () => void;
}

export const ImagePreview: React.FC<ImagePreviewProps> = ({
  src,
  alt,
  isOpen,
  onClose,
}) => {
  if (!isOpen) return null;

  return (
    <div
      className="image-preview-overlay"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.9)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: '20px',
      }}
      onClick={onClose}
    >
      <img
        src={src}
        alt={alt}
        style={{
          maxWidth: '90vw',
          maxHeight: '90vh',
          objectFit: 'contain',
        }}
        onClick={(e) => e.stopPropagation()}
      />

      <button
        onClick={onClose}
        style={{
          position: 'absolute',
          top: '20px',
          right: '20px',
          background: 'rgba(255, 255, 255, 0.2)',
          border: 'none',
          borderRadius: '50%',
          width: '40px',
          height: '40px',
          fontSize: '24px',
          color: 'white',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        ×
      </button>
    </div>
  );
};

export default OptimizedImage;
