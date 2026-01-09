// frontend/src/components/ui/Button.tsx
import React, { ButtonHTMLAttributes, forwardRef } from 'react';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'link';
  size?: 'small' | 'medium' | 'large';
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
  icon?: React.ReactNode;
  children: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'medium',
      loading = false,
      disabled = false,
      fullWidth = false,
      icon,
      children,
      className = '',
      style,
      ...props
    },
    ref
  ) => {
    const baseStyle: React.CSSProperties = {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '8px',
      padding: '8px 16px',
      borderRadius: '6px',
      border: 'none',
      cursor: disabled || loading ? 'not-allowed' : 'pointer',
      fontSize: '14px',
      fontWeight: '500',
      transition: 'all 0.2s ease',
      opacity: disabled || loading ? 0.5 : 1,
      width: fullWidth ? '100%' : 'auto',
      ...style,
    };

    const variantStyles = {
      primary: {
        backgroundColor: '#0066cc',
        color: 'white',
        '&:hover': {
          backgroundColor: '#0052a3',
        },
      },
      secondary: {
        backgroundColor: '#f0f0f0',
        color: '#333',
        '&:hover': {
          backgroundColor: '#e0e0e0',
        },
      },
      danger: {
        backgroundColor: '#ff5252',
        color: 'white',
        '&:hover': {
          backgroundColor: '#ff3333',
        },
      },
      ghost: {
        backgroundColor: 'transparent',
        color: '#0066cc',
        border: '1px solid #0066cc',
        '&:hover': {
          backgroundColor: 'rgba(0, 102, 204, 0.05)',
        },
      },
      link: {
        backgroundColor: 'transparent',
        color: '#0066cc',
        padding: '4px 8px',
        '&:hover': {
          textDecoration: 'underline',
        },
      },
    };

    const sizeStyles = {
      small: {
        padding: '4px 12px',
        fontSize: '12px',
      },
      medium: {
        padding: '8px 16px',
        fontSize: '14px',
      },
      large: {
        padding: '12px 24px',
        fontSize: '16px',
      },
    };

    return (
      <button
        ref={ref}
        className={`button button-${variant} button-${size} ${className}`}
        disabled={disabled || loading}
        style={{
          ...baseStyle,
          ...variantStyles[variant],
          ...sizeStyles[size],
        }}
        {...props}
      >
        {loading && <LoadingSpinner size="small" />}
        {icon && <span className="button-icon">{icon}</span>}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';

const LoadingSpinner: React.FC<{ size?: string }> = ({ size }) => (
  <span
    className="button-spinner"
    style={{
      display: 'inline-block',
      width: size === 'small' ? '12px' : '16px',
      height: size === 'small' ? '12px' : '16px',
      border: '2px solid currentColor',
      borderRadius: '50%',
      borderRightColor: 'transparent',
      animation: 'spin 0.6s linear infinite',
    }}
  />
);

export default Button;
