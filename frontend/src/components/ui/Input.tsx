// frontend/src/components/ui/Input.tsx
import React, { InputHTMLAttributes, forwardRef, useState } from 'react';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  fullWidth?: boolean;
  variant?: 'outlined' | 'filled' | 'standard';
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      helperText,
      fullWidth = false,
      variant = 'outlined',
      className = '',
      style,
      disabled = false,
      ...props
    },
    ref
  ) => {
    const [focused, setFocused] = useState(false);

    const containerStyle: React.CSSProperties = {
      display: 'flex',
      flexDirection: 'column',
      gap: '4px',
      width: fullWidth ? '100%' : 'auto',
      ...style,
    };

    const labelStyle: React.CSSProperties = {
      fontSize: '14px',
      fontWeight: '500',
      color: error ? '#ff5252' : '#333',
    };

    const inputBaseStyle: React.CSSProperties = {
      padding: '8px 12px',
      fontSize: '14px',
      border: '1px solid',
      borderRadius: '4px',
      outline: 'none',
      transition: 'all 0.2s ease',
      width: '100%',
      boxSizing: 'border-box',
    };

    const getVariantStyle = (): React.CSSProperties => {
      switch (variant) {
        case 'outlined':
          return {
            borderColor: focused ? '#0066cc' : error ? '#ff5252' : '#ccc',
            backgroundColor: '#fff',
            '&:focus': {
              borderColor: '#0066cc',
              boxShadow: '0 0 0 2px rgba(0, 102, 204, 0.1)',
            },
          };
        case 'filled':
          return {
            border: 'none',
            borderBottom: '2px solid',
            borderRadius: '4px 4px 0 0',
            borderColor: focused ? '#0066cc' : error ? '#ff5252' : '#ccc',
            backgroundColor: focused ? 'rgba(0, 102, 204, 0.05)' : '#f5f5f5',
          };
        case 'standard':
          return {
            border: 'none',
            borderBottom: '1px solid',
            borderRadius: 0,
            borderColor: focused ? '#0066cc' : error ? '#ff5252' : '#ccc',
          };
        default:
          return {};
      }
    };

    const helperTextStyle: React.CSSProperties = {
      fontSize: '12px',
      color: error ? '#ff5252' : '#666',
    };

    return (
      <div className={`input-container ${className}`} style={containerStyle}>
        {label && <label style={labelStyle}>{label}</label>}

        <input
          ref={ref}
          className={`input input-${variant}`}
          disabled={disabled}
          onFocus={(e) => {
            setFocused(true);
            props.onFocus?.(e);
          }}
          onBlur={(e) => {
            setFocused(false);
            props.onBlur?.(e);
          }}
          style={{
            ...inputBaseStyle,
            ...getVariantStyle(),
            opacity: disabled ? 0.5 : 1,
            cursor: disabled ? 'not-allowed' : 'text',
          }}
          {...props}
        />

        {error && <span style={helperTextStyle}>{error}</span>}
        {helperText && !error && <span style={helperTextStyle}>{helperText}</span>}
      </div>
    );
  }
);

Input.displayName = 'Input';

/**
 * 文本域组件
 */
export interface TextareaProps extends InputHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
  fullWidth?: boolean;
  rows?: number;
  maxLength?: number;
  showCount?: boolean;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      label,
      error,
      helperText,
      fullWidth = false,
      rows = 4,
      maxLength,
      showCount = false,
      className = '',
      style,
      disabled = false,
      value,
      ...props
    },
    ref
  ) => {
    const length = value?.toString().length || 0;

    const containerStyle: React.CSSProperties = {
      display: 'flex',
      flexDirection: 'column',
      gap: '4px',
      width: fullWidth ? '100%' : 'auto',
      ...style,
    };

    const textareaStyle: React.CSSProperties = {
      padding: '8px 12px',
      fontSize: '14px',
      border: '1px solid',
      borderRadius: '4px',
      borderColor: error ? '#ff5252' : '#ccc',
      outline: 'none',
      resize: 'vertical',
      fontFamily: 'inherit',
      opacity: disabled ? 0.5 : 1,
      cursor: disabled ? 'not-allowed' : 'text',
    };

    const helperTextStyle: React.CSSProperties = {
      fontSize: '12px',
      color: error ? '#ff5252' : '#666',
      display: 'flex',
      justifyContent: 'space-between',
    };

    return (
      <div className={`textarea-container ${className}`} style={containerStyle}>
        {label && (
          <label style={{ fontSize: '14px', fontWeight: '500', color: '#333' }}>
            {label}
          </label>
        )}

        <textarea
          ref={ref}
          rows={rows}
          maxLength={maxLength}
          disabled={disabled}
          value={value}
          style={textareaStyle}
          {...props}
        />

        {(error || helperText || showCount) && (
          <div style={helperTextStyle}>
            <span>{error || helperText}</span>
            {showCount && maxLength && (
              <span>
                {length} / {maxLength}
              </span>
            )}
          </div>
        )}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';

/**
 * 选择框组件
 */
export interface SelectProps extends InputHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  helperText?: string;
  fullWidth?: boolean;
  options: Array<{ value: string | number; label: string; disabled?: boolean }>;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  (
    {
      label,
      error,
      helperText,
      fullWidth = false,
      options,
      className = '',
      style,
      disabled = false,
      ...props
    },
    ref
  ) => {
    const containerStyle: React.CSSProperties = {
      display: 'flex',
      flexDirection: 'column',
      gap: '4px',
      width: fullWidth ? '100%' : 'auto',
      ...style,
    };

    const selectStyle: React.CSSProperties = {
      padding: '8px 12px',
      fontSize: '14px',
      border: '1px solid',
      borderRadius: '4px',
      borderColor: error ? '#ff5252' : '#ccc',
      outline: 'none',
      backgroundColor: '#fff',
      cursor: disabled ? 'not-allowed' : 'pointer',
      opacity: disabled ? 0.5 : 1,
    };

    const helperTextStyle: React.CSSProperties = {
      fontSize: '12px',
      color: error ? '#ff5252' : '#666',
    };

    return (
      <div className={`select-container ${className}`} style={containerStyle}>
        {label && (
          <label style={{ fontSize: '14px', fontWeight: '500', color: '#333' }}>
            {label}
          </label>
        )}

        <select
          ref={ref}
          disabled={disabled}
          style={selectStyle}
          {...props}
        >
          {options.map((option) => (
            <option
              key={option.value}
              value={option.value}
              disabled={option.disabled}
            >
              {option.label}
            </option>
          ))}
        </select>

        {error && <span style={helperTextStyle}>{error}</span>}
        {helperText && !error && <span style={helperTextStyle}>{helperText}</span>}
      </div>
    );
  }
);

Select.displayName = 'Select';

/**
 * 复选框组件
 */
export interface CheckboxProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  indeterminate?: boolean;
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ label, error, indeterminate = false, className = '', style, ...props }, ref) => {
    const checkboxRef = React.useRef<HTMLInputElement>(null);

    React.useEffect(() => {
      if (checkboxRef.current) {
        checkboxRef.current.indeterminate = indeterminate;
      }
    }, [indeterminate]);

    const containerStyle: React.CSSProperties = {
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      cursor: props.disabled ? 'not-allowed' : 'pointer',
      ...style,
    };

    const checkboxStyle: React.CSSProperties = {
      width: '18px',
      height: '18px',
      cursor: props.disabled ? 'not-allowed' : 'pointer',
    };

    const labelStyle: React.CSSProperties = {
      fontSize: '14px',
      color: error ? '#ff5252' : '#333',
      cursor: props.disabled ? 'not-allowed' : 'pointer',
    };

    return (
      <label className={`checkbox-container ${className}`} style={containerStyle}>
        <input
          ref={(element) => {
            if (element) {
              checkboxRef.current = element;
              if (typeof ref === 'function') {
                ref(element);
              } else if (ref) {
                ref.current = element;
              }
            }
          }}
          type="checkbox"
          className="checkbox"
          style={checkboxStyle}
          {...props}
        />
        {label && <span style={labelStyle}>{label}</span>}
      </label>
    );
  }
);

Checkbox.displayName = 'Checkbox';

export default Input;
