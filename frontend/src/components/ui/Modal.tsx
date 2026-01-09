// frontend/src/components/ui/Modal.tsx
import React, { HTMLAttributes, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { Button } from './Button';

export interface ModalProps extends HTMLAttributes<HTMLDivElement> {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  footer?: React.ReactNode;
  size?: 'small' | 'medium' | 'large' | 'full';
  closeOnOverlayClick?: boolean;
  closeOnEsc?: boolean;
  showCloseButton?: boolean;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = 'medium',
  closeOnOverlayClick = true,
  closeOnEsc = true,
  showCloseButton = true,
  className = '',
  style,
}) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      // 禁止背景滚动
      document.body.style.overflow = 'hidden';

      // 聚焦到模态框
      if (modalRef.current) {
        modalRef.current.focus();
      }
    } else {
      // 恢复背景滚动
      document.body.style.overflow = '';
    }

    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen || !closeOnEsc) return;

    const handleEsc = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEsc);
    return () => document.removeEventListener('keydown', handleEsc);
  }, [isOpen, closeOnEsc, onClose]);

  if (!isOpen) return null;

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === overlayRef.current && closeOnOverlayClick) {
      onClose();
    }
  };

  const sizeStyles = {
    small: {
      maxWidth: '400px',
      width: '90%',
    },
    medium: {
      maxWidth: '600px',
      width: '90%',
    },
    large: {
      maxWidth: '800px',
      width: '90%',
    },
    full: {
      maxWidth: '100%',
      width: '100%',
      height: '100%',
      borderRadius: 0,
    },
  };

  return createPortal(
    <div
      className={`modal-overlay ${className}`}
      ref={overlayRef}
      onClick={handleOverlayClick}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '20px',
        ...style,
      }}
    >
      <div
        ref={modalRef}
        className="modal-content"
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
        style={{
          backgroundColor: '#fff',
          borderRadius: size === 'full' ? 0 : '8px',
          boxShadow: '0 4px 24px rgba(0, 0, 0, 0.2)',
          maxHeight: size === 'full' ? '100vh' : '90vh',
          overflow: 'auto',
          ...sizeStyles[size],
        }}
      >
        {/* 头部 */}
        {(title || showCloseButton) && (
          <div
            className="modal-header"
            style={{
              padding: '16px 24px',
              borderBottom: '1px solid #e0e0e0',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            {title && (
              <h2
                style={{
                  margin: 0,
                  fontSize: '20px',
                  fontWeight: '600',
                  color: '#333',
                }}
              >
                {title}
              </h2>
            )}
            {showCloseButton && (
              <button
                onClick={onClose}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '24px',
                  cursor: 'pointer',
                  color: '#999',
                  padding: '4px',
                  lineHeight: 1,
                }}
                aria-label="关闭"
              >
                ×
              </button>
            )}
          </div>
        )}

        {/* 内容 */}
        <div
          className="modal-body"
          style={{
            padding: '24px',
          }}
        >
          {children}
        </div>

        {/* 底部 */}
        {footer && (
          <div
            className="modal-footer"
            style={{
              padding: '16px 24px',
              borderTop: '1px solid #e0e0e0',
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '12px',
            }}
          >
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * 确认对话框
 */
export interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title?: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'primary' | 'danger';
}

export const ConfirmModal: React.FC<ConfirmModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title = '确认',
  message,
  confirmText = '确认',
  cancelText = '取消',
  variant = 'primary',
}) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} size="small">
      <p style={{ margin: 0, color: '#666' }}>{message}</p>

      <Modal.Footer>
        <Button variant="ghost" onClick={onClose}>
          {cancelText}
        </Button>
        <Button variant={variant} onClick={onConfirm}>
          {confirmText}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

ConfirmModal.displayName = 'ConfirmModal';

/**
 * 警告对话框
 */
export interface AlertDialogProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  message: string;
  type?: 'warning' | 'error' | 'info';
}

export const AlertDialog: React.FC<AlertDialogProps> = ({
  isOpen,
  onClose,
  title = '提示',
  message,
  type = 'info',
}) => {
  const icons = {
    warning: '⚠️',
    error: '❌',
    info: 'ℹ️',
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} size="small">
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          marginBottom: '16px',
        }}
      >
        <span style={{ fontSize: '32px' }}>{icons[type]}</span>
        <p style={{ margin: 0, color: '#666' }}>{message}</p>
      </div>

      <Modal.Footer>
        <Button onClick={onClose}>确定</Button>
      </Modal.Footer>
    </Modal>
  );
};

AlertDialog.displayName = 'AlertDialog';

// 命名空间
Modal.Footer = ({ children }: { children: React.ReactNode }) => (
  <div style={{ marginTop: '24px', display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
    {children}
  </div>
);

Modal.Footer.displayName = 'Modal.Footer';

export default Modal;
