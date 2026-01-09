// frontend/src/components/ImageUpload.tsx
import React, { useState, useRef } from 'react';
import { imageOptimizer, compressImage, getImageInfo } from '../utils/imageOptimizer';
import { useUIStore } from '../stores/uiStore';
import { DotsLoader } from './LoadingSpinner';

interface ImageUploadProps {
  onUpload?: (file: File, compressed?: Blob) => Promise<void>;
  accept?: string;
  maxSize?: number; // 字节
  maxWidth?: number;
  maxHeight?: number;
  quality?: number;
  className?: string;
  showPreview?: boolean;
  compress?: boolean;
}

/**
 * 图片上传组件 - 支持压缩、预览、验证
 */
export const ImageUpload: React.FC<ImageUploadProps> = ({
  onUpload,
  accept = 'image/jpeg,image/png,image/gif,image/webp',
  maxSize = 5 * 1024 * 1024, // 5MB
  maxWidth = 1920,
  maxHeight = 1080,
  quality = 0.8,
  className = '',
  showPreview = true,
  compress = true,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [imageInfo, setImageInfo] = useState<any>(null);
  const [isCompressing, setIsCompressing] = useState(false);
  const [compressionRatio, setCompressionRatio] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // 验证文件类型
    if (!file.type.startsWith('image/')) {
      useUIStore.getState().addNotification({
        type: 'error',
        message: '请选择图片文件',
      });
      return;
    }

    // 验证文件大小
    if (file.size > maxSize) {
      useUIStore.getState().addNotification({
        type: 'error',
        message: `文件过大（最大${imageOptimizer.formatFileSize(maxSize)}）`,
      });
      return;
    }

    setSelectedFile(file);

    // 生成预览
    if (showPreview) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreviewUrl(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }

    // 获取图片信息
    try {
      const info = await getImageInfo(file);
      setImageInfo(info);
    } catch (error) {
      console.error('获取图片信息失败:', error);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsCompressing(true);

    try {
      let fileToUpload = selectedFile;
      let compressed: Blob | undefined;

      // 压缩图片
      if (compress) {
        const startTime = Date.now();
        compressed = await compressImage(selectedFile, {
          maxWidth,
          maxHeight,
          quality,
        });
        const compressionTime = Date.now() - startTime;

        const ratio = ((1 - compressed.size / selectedFile.size) * 100).toFixed(1);
        setCompressionRatio(parseFloat(ratio));

        // 使用压缩后的文件
        fileToUpload = new File([compressed], selectedFile.name, {
          type: compressed.type,
        });

        useUIStore.getState().addNotification({
          type: 'success',
          message: `图片压缩完成！减少${ratio}%，耗时${compressionTime}ms`,
        });
      }

      // 调用上传回调
      if (onUpload) {
        await onUpload(selectedFile, compressed);
      }
    } catch (error) {
      useUIStore.getState().addNotification({
        type: 'error',
        message: `图片处理失败: ${(error as Error).message}`,
      });
    } finally {
      setIsCompressing(false);
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setImageInfo(null);
    setCompressionRatio(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className={`image-upload ${className}`}>
      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        onChange={handleFileSelect}
        style={{ display: 'none' }}
      />

      {!selectedFile ? (
        <div
          className="upload-dropzone"
          onClick={() => fileInputRef.current?.click()}
          style={{
            border: '2px dashed #ccc',
            borderRadius: '8px',
            padding: '40px',
            textAlign: 'center',
            cursor: 'pointer',
            transition: 'border-color 0.2s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = '#0066cc';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = '#ccc';
          }}
        >
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>📷</div>
          <p style={{ margin: 0, color: '#666' }}>点击或拖拽上传图片</p>
          <p style={{ margin: '8px 0 0 0', fontSize: '12px', color: '#999' }}>
            最大{imageOptimizer.formatFileSize(maxSize)}，支持JPG、PNG、GIF、WebP
          </p>
        </div>
      ) : (
        <div className="upload-preview" style={{ padding: '20px' }}>
          {/* 预览 */}
          {showPreview && previewUrl && (
            <div
              style={{
                position: 'relative',
                marginBottom: '16px',
                borderRadius: '8px',
                overflow: 'hidden',
              }}
            >
              <img
                src={previewUrl}
                alt="Preview"
                style={{ width: '100%', maxHeight: '300px', objectFit: 'contain' }}
              />
            </div>
          )}

          {/* 图片信息 */}
          {imageInfo && (
            <div
              style={{
                padding: '12px',
                backgroundColor: '#f5f5f5',
                borderRadius: '4px',
                marginBottom: '16px',
                fontSize: '14px',
              }}
            >
              <div><strong>文件名:</strong> {selectedFile.name}</div>
              <div><strong>尺寸:</strong> {imageInfo.width} × {imageInfo.height}</div>
              <div><strong>大小:</strong> {imageOptimizer.formatFileSize(imageInfo.size)}</div>
              <div><strong>类型:</strong> {imageInfo.type}</div>
              <div><strong>宽高比:</strong> {imageInfo.aspectRatio.toFixed(2)}</div>
            </div>
          )}

          {/* 压缩信息 */}
          {compress && compressionRatio > 0 && (
            <div
              style={{
                padding: '12px',
                backgroundColor: '#e8f5e9',
                borderRadius: '4px',
                marginBottom: '16px',
                fontSize: '14px',
                color: '#2e7d32',
              }}
            >
              <strong>压缩效果:</strong> 减少{compressionRatio}%
            </div>
          )}

          {/* 操作按钮 */}
          <div style={{ display: 'flex', gap: '12px' }}>
            {!isCompressing ? (
              <>
                <button
                  onClick={handleUpload}
                  disabled={isCompressing}
                  style={{
                    flex: 1,
                    padding: '12px 24px',
                    backgroundColor: '#0066cc',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '16px',
                  }}
                >
                  {compress ? '压缩并上传' : '上传'}
                </button>
                <button
                  onClick={handleClear}
                  style={{
                    padding: '12px 24px',
                    backgroundColor: '#e0e0e0',
                    color: '#333',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '16px',
                  }}
                >
                  清除
                </button>
              </>
            ) : (
              <div
                style={{
                  flex: 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '12px',
                  padding: '12px',
                }}
              >
                <DotsLoader size="small" />
                <span>处理中...</span>
              </div>
            )}
          </div>
        </div>
      )}

      <style>{`
        .image-upload {
          width: 100%;
        }

        .upload-dropzone:hover {
          background-color: #f9f9f9;
        }
      `}</style>
    </div>
  );
};

/**
 * 多图片上传组件
 */
interface MultiImageUploadProps extends Omit<ImageUploadProps, 'onUpload'> {
  onUpload?: (files: File[]) => Promise<void>;
  maxFiles?: number;
}

export const MultiImageUpload: React.FC<MultiImageUploadProps> = ({
  onUpload,
  maxFiles = 10,
  ...rest
}) => {
  const [files, setFiles] = useState<File[]>([]);

  const handleFileSelect = async (file: File, compressed?: Blob) => {
    if (files.length >= maxFiles) {
      useUIStore.getState().addNotification({
        type: 'warning',
        message: `最多只能上传${maxFiles}张图片`,
      });
      return;
    }

    setFiles([...files, file]);
  };

  const handleRemoveFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleUploadAll = async () => {
    if (onUpload) {
      await onUpload(files);
      setFiles([]);
    }
  };

  return (
    <div className="multi-image-upload">
      {files.map((file, index) => (
        <div key={index} style={{ marginBottom: '16px' }}>
          <ImageUpload
            onUpload={handleFileSelect}
            {...rest}
            showPreview={true}
          />
          <button
            onClick={() => handleRemoveFile(index)}
            style={{
              marginTop: '8px',
              padding: '8px 16px',
              backgroundColor: '#ff5252',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            删除
          </button>
        </div>
      ))}

      {files.length < maxFiles && (
        <ImageUpload onUpload={handleFileSelect} {...rest} />
      )}

      {files.length > 0 && (
        <button
          onClick={handleUploadAll}
          style={{
            marginTop: '16px',
            padding: '12px 24px',
            backgroundColor: '#0066cc',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '16px',
            width: '100%',
          }}
        >
          上传全部 ({files.length})
        </button>
      )}
    </div>
  );
};

export default ImageUpload;
