// frontend/src/services/websocket.ts

export interface WebSocketMessage {
  type: 'status_update' | 'image_progress' | 'page_completed' | 'generation_completed' | 'generation_failed';
  book_id: number;
  status?: string;
  stage?: string;
  completed_pages?: number;
  total_pages?: number;
  progress?: number;
  page_number?: number;
  image_url?: string;
  error?: string;
}

export type WebSocketCallback = (message: WebSocketMessage) => void;
export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'reconnecting' | 'failed';

class WebSocketService {
  private ws: WebSocket | null = null;
  private callbacks: Set<WebSocketCallback> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private baseReconnectDelay = 1000;
  private maxReconnectDelay = 30000;
  private bookId: number | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private statusListeners: Set<(status: ConnectionStatus) => void> = new Set();
  private currentStatus: ConnectionStatus = 'disconnected';

  // 降级到轮询模式的回调
  private onConnectionLost: ((bookId: number) => void) | null = null;

  connect(bookId: number) {
    // 如果已经连接到同一个book，不重新连接
    if (this.ws && this.bookId === bookId && this.ws.readyState === WebSocket.OPEN) {
      return;
    }

    // 关闭旧连接
    this.disconnect();

    this.bookId = bookId;
    this.updateStatus('connecting');

    const wsUrl = `ws://localhost:8000/api/v1/ws/${bookId}`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('✅ WebSocket connected for book:', bookId);
        this.reconnectAttempts = 0;
        this.updateStatus('connected');
        this.startHeartbeat();
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          // 只处理属于当前book的消息
          if (message.book_id === bookId) {
            this.callbacks.forEach(callback => callback(message));
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        this.updateStatus('failed');
      };

      this.ws.onclose = (event) => {
        console.log('🔌 WebSocket disconnected:', event.code, event.reason);
        this.stopHeartbeat();
        this.updateStatus('disconnected');

        // 尝试重连
        this.attemptReconnect(bookId);
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.updateStatus('failed');
      // 降级到轮询模式
      this.fallbackToPolling(bookId);
    }
  }

  private attemptReconnect(bookId: number) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.min(
        this.baseReconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
        this.maxReconnectDelay
      );

      console.log(
        `🔄 Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`
      );
      console.log(`   Next attempt in ${delay}ms`);

      this.updateStatus('reconnecting');

      this.reconnectTimer = setTimeout(() => {
        if (this.bookId === bookId) {
          this.connect(bookId);
        }
      }, delay);
    } else {
      console.error('❌ Max reconnection attempts reached. Falling back to polling.');
      this.updateStatus('failed');
      // 降级到轮询模式
      this.fallbackToPolling(bookId);
    }
  }

  private fallbackToPolling(bookId: number) {
    console.log('⚠️  Falling back to polling mode for book:', bookId);
    if (this.onConnectionLost) {
      this.onConnectionLost(bookId);
    }
  }

  private startHeartbeat() {
    // 每30秒发送一次心跳
    this.heartbeatTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping', book_id: this.bookId }));
      } else {
        this.stopHeartbeat();
      }
    }, 30000);
  }

  private stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private updateStatus(status: ConnectionStatus) {
    if (this.currentStatus !== status) {
      this.currentStatus = status;
      this.statusListeners.forEach(listener => listener(status));
      console.log(`📡 WebSocket status: ${status}`);
    }
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    this.stopHeartbeat();

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.bookId = null;
    this.reconnectAttempts = 0;
    this.updateStatus('disconnected');
  }

  subscribe(callback: WebSocketCallback) {
    this.callbacks.add(callback);
    return () => {
      this.callbacks.delete(callback);
    };
  }

  onStatusChange(callback: (status: ConnectionStatus) => void) {
    this.statusListeners.add(callback);
    return () => {
      this.statusListeners.delete(callback);
    };
  }

  setConnectionLostCallback(callback: (bookId: number) => void) {
    this.onConnectionLost = callback;
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  getStatus(): ConnectionStatus {
    return this.currentStatus;
  }
}

// 创建单例
export const websocketService = new WebSocketService();
