// frontend/src/components/ui/Card.tsx
import React, { HTMLAttributes, forwardRef } from 'react';

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
  extra?: React.ReactNode;
  footer?: React.ReactNode;
  hoverable?: boolean;
  bordered?: boolean;
  shadow?: 'none' | 'small' | 'medium' | 'large';
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger';
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      children,
      title,
      subtitle,
      extra,
      footer,
      hoverable = false,
      bordered = true,
      shadow = 'small',
      variant = 'default',
      className = '',
      style,
      ...props
    },
    ref
  ) => {
    const containerStyle: React.CSSProperties = {
      backgroundColor: '#fff',
      borderRadius: '8px',
      border: bordered ? '1px solid #e0e0e0' : 'none',
      boxShadow: {
        none: 'none',
        small: '0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24)',
        medium: '0 3px 6px rgba(0, 0, 0, 0.16), 0 3px 6px rgba(0, 0, 0, 0.23)',
        large: '0 10px 20px rgba(0, 0, 0, 0.19), 0 6px 6px rgba(0, 0, 0, 0.23)',
      }[shadow],
      transition: hoverable ? 'all 0.3s ease' : 'none',
      cursor: hoverable ? 'pointer' : 'default',
      overflow: 'hidden',
      ...style,
    };

    const getVariantStyle = (): React.CSSProperties => {
      const variantStyles = {
        default: {},
        primary: {
          borderTop: '3px solid #0066cc',
        },
        success: {
          borderTop: '3px solid #4caf50',
        },
        warning: {
          borderTop: '3px solid #ff9800',
        },
        danger: {
          borderTop: '3px solid #ff5252',
        },
      };
      return variantStyles[variant];
    };

    return (
      <div
        ref={ref}
        className={`card card-${variant} ${hoverable ? 'card-hoverable' : ''} ${className}`}
        style={{ ...containerStyle, ...getVariantStyle() }}
        {...props}
      >
        {(title || subtitle || extra) && (
          <div
            className="card-header"
            style={{
              padding: '16px',
              borderBottom: '1px solid #e0e0e0',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div>
              {title && (
                <h3
                  style={{
                    margin: 0,
                    fontSize: '16px',
                    fontWeight: '600',
                    color: '#333',
                  }}
                >
                  {title}
                </h3>
              )}
              {subtitle && (
                <p
                  style={{
                    margin: '4px 0 0 0',
                    fontSize: '14px',
                    color: '#666',
                  }}
                >
                  {subtitle}
                </p>
              )}
            </div>
            {extra && <div>{extra}</div>}
          </div>
        )}

        <div
          className="card-body"
          style={{
            padding: title || subtitle || extra ? '16px' : '0',
          }}
        >
          {children}
        </div>

        {footer && (
          <div
            className="card-footer"
            style={{
              padding: '16px',
              borderTop: '1px solid #e0e0e0',
            }}
          >
            {footer}
          </div>
        )}
      </div>
    );
  }
);

Card.displayName = 'Card';

/**
 * 卡片网格
 */
export interface CardGridProps extends HTMLAttributes<HTMLDivElement> {
  cols?: number;
  gap?: number;
  responsive?: boolean;
}

export const CardGrid = forwardRef<HTMLDivElement, CardGridProps>(
  ({ cols = 3, gap = 16, responsive = true, children, className = '', style, ...props }, ref) => {
    const gridStyle: React.CSSProperties = {
      display: 'grid',
      gridTemplateColumns: responsive
        ? `repeat(auto-fit, minmax(${cols === 1 ? '100%' : cols === 2 ? 'calc(50% - 8px)' : cols === 3 ? 'calc(33.333% - 11px)' : cols === 4 ? 'calc(25% - 12px)' : '200px'}, 1fr))`
        : `repeat(${cols}, 1fr)`,
      gap: `${gap}px`,
      ...style,
    };

    return (
      <div
        ref={ref}
        className={`card-grid ${className}`}
        style={gridStyle}
        {...props}
      >
        {children}
      </div>
    );
  }
);

CardGrid.displayName = 'CardGrid';

export default Card;
