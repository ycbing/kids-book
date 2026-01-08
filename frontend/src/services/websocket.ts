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

class WebSocketService {
  private ws: WebSocket | null = null;
  private callbacks: Set<WebSocketCallback> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000;
  private bookId: number | null = null;

  connect(bookId: number) {
    // 如果已经连接到同一个book，不重新连接
    if (this.ws && this.bookId === bookId && this.ws.readyState === WebSocket.OPEN) {
      return;
    }

    // 关闭旧连接
    this.disconnect();

    this.bookId = bookId;
    const wsUrl = `ws://localhost:8000/api/v1/ws/book-${bookId}`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected for book:', bookId);
        this.reconnectAttempts = 0;
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
        console.error('WebSocket error:', error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        // 尝试重连
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
          setTimeout(() => {
            if (this.bookId) {
              this.connect(this.bookId);
            }
          }, this.reconnectDelay);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.bookId = null;
    this.reconnectAttempts = 0;
  }

  subscribe(callback: WebSocketCallback) {
    this.callbacks.add(callback);
    return () => {
      this.callbacks.delete(callback);
    };
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// 创建单例
export const websocketService = new WebSocketService();
