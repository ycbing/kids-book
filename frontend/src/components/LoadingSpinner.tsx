// frontend/src/components/LoadingSpinner.tsx
import React from 'react';

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  color?: 'primary' | 'secondary' | 'white';
  className?: string;
  fullscreen?: boolean;
  text?: string;
}

/**
 * 加载指示器组件
 */
export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'medium',
  color = 'primary',
  className = '',
  fullscreen = false,
  text,
}) => {
  const sizeMap = {
    small: '20px',
    medium: '40px',
    large: '60px',
  };

  const colorMap = {
    primary: '#0066cc',
    secondary: '#666666',
    white: '#ffffff',
  };

  const spinnerStyle: React.CSSProperties = {
    width: sizeMap[size],
    height: sizeMap[size],
    borderColor: color === 'white' ? 'rgba(255,255,255,0.3)' : '#e0e0e0',
    borderTopColor: colorMap[color],
  };

  const content = (
    <div className={`loading-spinner ${className}`}>
      <div className="spinner" style={spinnerStyle} />
      {text && <p className="loading-text">{text}</p>}

      <style>{`
        .loading-spinner {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 12px;
        }

        .spinner {
          border: 3px solid;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .loading-text {
          margin: 0;
          font-size: 14px;
          color: ${colorMap[color]};
          text-align: center;
        }

        .fullscreen-spinner {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(255, 255, 255, 0.9);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 9999;
        }
      `}</style>
    </div>
  );

  if (fullscreen) {
    return <div className="fullscreen-spinner">{content}</div>;
  }

  return content;
};

/**
 * 点状加载指示器
 */
interface DotsLoaderProps {
  size?: 'small' | 'medium' | 'large';
  color?: string;
  className?: string;
}

export const DotsLoader: React.FC<DotsLoaderProps> = ({
  size = 'medium',
  color = '#0066cc',
  className = '',
}) => {
  const sizeMap = {
    small: '8px',
    medium: '12px',
    large: '16px',
  };

  const dotStyle: React.CSSProperties = {
    width: sizeMap[size],
    height: sizeMap[size],
    backgroundColor: color,
  };

  return (
    <div className={`dots-loader ${className}`}>
      <div className="dot" style={dotStyle} />
      <div className="dot" style={dotStyle} />
      <div className="dot" style={dotStyle} />

      <style>{`
        .dots-loader {
          display: inline-flex;
          align-items: center;
          gap: 8px;
        }

        .dot {
          border-radius: 50%;
          animation: bounce 1.4s infinite ease-in-out both;
        }

        .dot:nth-child(1) {
          animation-delay: -0.32s;
        }

        .dot:nth-child(2) {
          animation-delay: -0.16s;
        }

        @keyframes bounce {
          0%, 80%, 100% {
            transform: scale(0);
            opacity: 0.5;
          }
          40% {
            transform: scale(1);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
};

/**
 * 进度条加载器
 */
interface ProgressBarProps {
  progress: number; // 0-100
  color?: string;
  height?: number;
  showPercentage?: boolean;
  className?: string;
  animated?: boolean;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  color = '#0066cc',
  height = 8,
  showPercentage = false,
  className = '',
  animated = true,
}) => {
  const clampedProgress = Math.min(100, Math.max(0, progress));

  return (
    <div className={`progress-bar-container ${className}`}>
      <div className="progress-bar-wrapper" style={{ height: `${height}px` }}>
        <div
          className={`progress-bar-fill ${animated ? 'animated' : ''}`}
          style={{
            width: `${clampedProgress}%`,
            backgroundColor: color,
          }}
        />
      </div>
      {showPercentage && (
        <span className="progress-percentage">{Math.round(clampedProgress)}%</span>
      )}

      <style>{`
        .progress-bar-container {
          display: flex;
          flex-direction: column;
          gap: 8px;
          width: 100%;
        }

        .progress-bar-wrapper {
          width: 100%;
          background: #e0e0e0;
          border-radius: ${height / 2}px;
          overflow: hidden;
        }

        .progress-bar-fill {
          height: 100%;
          transition: width 0.3s ease;
          border-radius: ${height / 2}px;
        }

        .progress-bar-fill.animated {
          animation: shimmer 2s infinite;
        }

        @keyframes shimmer {
          0% {
            opacity: 1;
          }
          50% {
            opacity: 0.7;
          }
          100% {
            opacity: 1;
          }
        }

        .progress-percentage {
          font-size: 12px;
          color: #666;
          text-align: right;
        }
      `}</style>
    </div>
  );
};

/**
 * 带阶段的进度条
 */
interface StageProgressBarProps {
  stage: string;
  progress: number;
  stages: string[];
  className?: string;
}

export const StageProgressBar: React.FC<StageProgressBarProps> = ({
  stage,
  progress,
  stages,
  className = '',
}) => {
  const currentIndex = stages.indexOf(stage);
  const totalStages = stages.length;
  const stageProgress = ((currentIndex + progress / 100) / totalStages) * 100;

  return (
    <div className={`stage-progress-container ${className}`}>
      <div className="stages">
        {stages.map((s, index) => {
          const isCompleted = index < currentIndex;
          const isCurrent = index === currentIndex;
          const isPending = index > currentIndex;

          return (
            <div
              key={s}
              className={`stage ${isCompleted ? 'completed' : ''} ${
                isCurrent ? 'current' : ''
              } ${isPending ? 'pending' : ''}`}
            >
              <div className="stage-dot" />
              <span className="stage-label">{s}</span>
            </div>
          );
        })}
      </div>

      <ProgressBar progress={stageProgress} showPercentage />

      <style>{`
        .stage-progress-container {
          display: flex;
          flex-direction: column;
          gap: 16px;
          width: 100%;
          padding: 20px;
          background: #f9f9f9;
          border-radius: 8px;
        }

        .stages {
          display: flex;
          justify-content: space-between;
          align-items: center;
          position: relative;
        }

        .stages::before {
          content: '';
          position: absolute;
          top: 12px;
          left: 20px;
          right: 20px;
          height: 2px;
          background: #e0e0e0;
          z-index: 0;
        }

        .stage {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          z-index: 1;
        }

        .stage-dot {
          width: 24px;
          height: 24px;
          border-radius: 50%;
          background: #e0e0e0;
          border: 2px solid #fff;
          transition: all 0.3s ease;
        }

        .stage.completed .stage-dot {
          background: #4caf50;
        }

        .stage.current .stage-dot {
          background: #0066cc;
          animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
          0%, 100% {
            transform: scale(1);
            opacity: 1;
          }
          50% {
            transform: scale(1.1);
            opacity: 0.8;
          }
        }

        .stage.pending .stage-dot {
          background: #e0e0e0;
        }

        .stage-label {
          font-size: 12px;
          color: #666;
          text-align: center;
          max-width: 80px;
        }

        .stage.completed .stage-label {
          color: #4caf50;
          font-weight: 500;
        }

        .stage.current .stage-label {
          color: #0066cc;
          font-weight: 500;
        }
      `}</style>
    </div>
  );
};

/**
 * 脉冲加载器
 */
interface PulseLoaderProps {
  size?: 'small' | 'medium' | 'large';
  color?: string;
  className?: string;
}

export const PulseLoader: React.FC<PulseLoaderProps> = ({
  size = 'medium',
  color = '#0066cc',
  className = '',
}) => {
  const sizeMap = {
    small: '32px',
    medium: '48px',
    large: '64px',
  };

  return (
    <div className={`pulse-loader ${className}`}>
      <div
        className="pulse-circle"
        style={{
          width: sizeMap[size],
          height: sizeMap[size],
          backgroundColor: color,
        }}
      />

      <style>{`
        .pulse-loader {
          display: inline-block;
        }

        .pulse-circle {
          border-radius: 50%;
          animation: pulse-scale 1.5s ease-in-out infinite;
        }

        @keyframes pulse-scale {
          0%, 100% {
            transform: scale(0.8);
            opacity: 0.5;
          }
          50% {
            transform: scale(1);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
};

export default LoadingSpinner;
