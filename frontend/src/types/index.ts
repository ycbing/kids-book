// frontend/src/types/index.ts

/**
 * ================
 * 基础类型定义
 * ================
 */

/**
 * ID类型
 */
export type ID = number | string;

/**
 * 时间戳类型
 */
export type Timestamp = number;

/**
 * 日期时间类型
 */
export type DateTime = string;

/**
 * 可选类型（所有属性可选）
 */
export type Partial<T> = {
  [P in keyof T]?: T[P];
};

/**
 * 必需类型（所有属性必需）
 */
export type Required<T> = {
  [P in keyof T]-?: T[P];
};

/**
 * 提取特定属性
 */
export type Pick<T, K extends keyof T> = {
  [P in K]: T[P];
};

/**
 * 排除特定属性
 */
export type Omit<T, K extends keyof T> = {
  [P in Exclude<keyof T, K>]: T[P];
};

/**
 * ================
 * 通用类型
 * ================
 */

/**
 * 分页参数
 */
export interface PaginationParams {
  page?: number;
  size?: number;
  limit?: number;
  offset?: number;
}

/**
 * 分页响应
 */
export interface PaginationResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

/**
 * 排序参数
 */
export interface SortParams {
  field: string;
  order: 'asc' | 'desc';
}

/**
 * 查询参数
 */
export interface QueryParams extends PaginationParams {
  sort?: SortParams;
  filter?: Record<string, any>;
  search?: string;
}

/**
 * API响应基础类型
 */
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  code?: string;
  timestamp?: string;
}

/**
 * 列表响应
 */
export interface ListResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

/**
 * 创建请求
 */
export interface CreateRequest {
  [key: string]: any;
}

/**
 * 更新请求
 */
export interface UpdateRequest {
  [key: string]: any;
}

/**
 * 删除响应
 */
export interface DeleteResponse {
  success: boolean;
  message?: string;
}

/**
 * ================
 * 业务类型
 * ================
 */

/**
 * 绘本状态
 */
export enum BookStatus {
  DRAFT = 'draft',
  GENERATING = 'generating',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

/**
 * 绘本风格
 */
export enum BookStyle {
  CARTOON = 'cartoon',
  WATERCOLOR = 'watercolor',
  OIL_PAINTING = 'oil_painting',
  SKETCH = 'sketch',
  ANIME = 'anime',
  REALISTIC = 'realistic',
}

/**
 * 目标年龄
 */
export enum TargetAge {
  PRESCHOOL = '3-5',
  EARLY_ELEMENTARY = '6-8',
  LATE_ELEMENTARY = '9-12',
  MIDDLE_SCHOOL = '13-15',
}

/**
 * 绘本类型
 */
export interface Book {
  id: ID;
  title: string;
  description: string;
  theme: string;
  keywords: string[];
  target_age: string;
  style: string;
  status: BookStatus;
  cover_image?: string;
  pages: Page[];
  created_at: DateTime;
  updated_at: DateTime;
  user_id?: ID;
}

/**
 * 绘本创建请求
 */
export interface BookCreateRequest {
  title?: string;
  theme: string;
  keywords: string[];
  target_age: string;
  style: string;
  page_count: number;
  custom_prompt?: string;
}

/**
 * 绘本更新请求
 */
export interface BookUpdateRequest {
  title?: string;
  description?: string;
  theme?: string;
  keywords?: string[];
  target_age?: string;
  style?: string;
}

/**
 * 页面内容
 */
export interface Page {
  page_number: number;
  text_content: string;
  image_prompt: string;
  image_url?: string;
  created_at?: DateTime;
}

/**
 * 页面更新请求
 */
export interface PageUpdateRequest {
  text_content?: string;
  image_prompt?: string;
}

/**
 * 故事生成请求
 */
export interface StoryGenerateRequest {
  theme: string;
  keywords: string[];
  target_age: string;
  page_count: number;
  custom_prompt?: string;
}

/**
 * 故事响应
 */
export interface Story {
  title: string;
  description: string;
  pages: StoryPage[];
}

/**
 * 故事页面
 */
export interface StoryPage {
  page_number: number;
  text: string;
  scene_description: string;
  image_prompt: string;
}

/**
 * 图片生成请求
 */
export interface ImageGenerateRequest {
  prompt: string;
  style: string;
  negative_prompt?: string;
}

/**
 * 图片生成响应
 */
export interface ImageGenerateResponse {
  image_url: string;
  prompt?: string;
}

/**
 * 导出格式
 */
export enum ExportFormat {
  PDF = 'pdf',
  IMAGES = 'images',
  EPUB = 'epub',
}

/**
 * 导出质量
 */
export enum ExportQuality {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
}

/**
 * 导出请求
 */
export interface ExportRequest {
  book_id: ID;
  format: ExportFormat;
  quality: ExportQuality;
}

/**
 * 导出响应
 */
export interface ExportResponse {
  message: string;
  filename: string;
  file_type: string;
  book_id: ID;
  download_url?: string;
}

/**
 * ================
 * WebSocket类型
 * ================
 */

/**
 * WebSocket消息类型
 */
export enum WebSocketMessageType {
  STATUS_UPDATE = 'status_update',
  IMAGE_PROGRESS = 'image_progress',
  PAGE_COMPLETED = 'page_completed',
  GENERATION_COMPLETED = 'generation_completed',
  GENERATION_FAILED = 'generation_failed',
}

/**
 * WebSocket消息
 */
export interface WebSocketMessage {
  type: WebSocketMessageType;
  book_id: ID;
  status?: string;
  stage?: string;
  completed_pages?: number;
  total_pages?: number;
  progress?: number;
  page_number?: number;
  image_url?: string;
  error?: string;
}

/**
 * 连接状态
 */
export enum ConnectionStatus {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  RECONNECTING = 'reconnecting',
  FAILED = 'failed',
}

/**
 * WebSocket回调
 */
export type WebSocketCallback = (message: WebSocketMessage) => void;

/**
 * 状态监听器
 */
export type StatusListener = (status: ConnectionStatus) => void;

/**
 * ================
 * UI类型
 * ================
 */

/**
 * 加载状态
 */
export interface LoadingState {
  [key: string]: boolean;
}

/**
 * 通知类型
 */
export enum NotificationType {
  SUCCESS = 'success',
  ERROR = 'error',
  WARNING = 'warning',
  INFO = 'info',
}

/**
 * 通知
 */
export interface Notification {
  id: string;
  type: NotificationType;
  message: string;
  duration?: number;
  timestamp?: DateTime;
}

/**
 * 模态框状态
 */
export interface ModalState {
  [key: string]: boolean;
}

/**
 * 侧边栏状态
 */
export interface SidebarState {
  isOpen: boolean;
  width?: number;
}

/**
 * 表单状态
 */
export interface FormState<T = any> {
  values: T;
  errors: Record<keyof T, string | undefined>;
  touched: Record<keyof T, boolean>;
  isSubmitting: boolean;
  isValid: boolean;
  isDirty: boolean;
}

/**
 * ================
 * 用户类型
 * ================
 */

/**
 * 用户
 */
export interface User {
  id: ID;
  username: string;
  email: string;
  avatar?: string;
  created_at: DateTime;
  updated_at: DateTime;
}

/**
 * 用户创建请求
 */
export interface UserCreateRequest {
  username: string;
  email: string;
  password: string;
}

/**
 * 用户更新请求
 */
export interface UserUpdateRequest {
  username?: string;
  email?: string;
  avatar?: string;
}

/**
 * 认证响应
 */
export interface AuthResponse {
  access_token: string;
  refresh_token?: string;
  user: User;
  expires_in?: number;
}

/**
 * 登录请求
 */
export interface LoginRequest {
  username: string;
  password: string;
}

/**
 * 注册请求
 */
export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

/**
 * ================
 * 错误类型
 * ================
 */

/**
 * 错误类型枚举
 */
export enum ErrorType {
  NETWORK = 'NETWORK_ERROR',
  API = 'API_ERROR',
  VALIDATION = 'VALIDATION_ERROR',
  AUTH = 'AUTH_ERROR',
  PERMISSION = 'PERMISSION_ERROR',
  NOT_FOUND = 'NOT_FOUND_ERROR',
  SERVER = 'SERVER_ERROR',
  UNKNOWN = 'UNKNOWN_ERROR',
}

/**
 * 应用错误
 */
export class AppError extends Error {
  type: ErrorType;
  code?: string;
  statusCode?: number;
  originalError?: Error;

  constructor(
    message: string,
    type: ErrorType = ErrorType.UNKNOWN,
    code?: string,
    statusCode?: number,
    originalError?: Error
  ) {
    super(message);
    this.name = 'AppError';
    this.type = type;
    this.code = code;
    this.statusCode = statusCode;
    this.originalError = originalError;

    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, AppError);
    }
  }
}

/**
 * ================
 * 文件类型
 * ================
 */

/**
 * 文件上传响应
 */
export interface FileUploadResponse {
  filename: string;
  path: string;
  size: number;
  url?: string;
}

/**
 * 文件信息
 */
export interface FileInfo {
  filename: string;
  size: number;
  size_mb: number;
  created_at: Timestamp;
  modified_at: Timestamp;
  extension: string;
  mime_type: string;
}

/**
 * ================
 * 组件Props类型
 * ================
 */

/**
 * 通用组件Props
 */
export interface BaseComponentProps {
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}

/**
 * 带加载状态的组件Props
 */
export interface WithLoadingProps extends BaseComponentProps {
  isLoading?: boolean;
  loadingText?: string;
}

/**
 * 带错误的组件Props
 */
export interface WithErrorProps extends BaseComponentProps {
  error?: string | null;
  onRetry?: () => void;
}

/**
 * 带分页的组件Props
 */
export interface WithPaginationProps extends BaseComponentProps {
  total: number;
  page: number;
  size: number;
  onPageChange: (page: number) => void;
  onSizeChange?: (size: number) => void;
}

/**
 * ================
 * 工具类型
 * ================
 */

/**
 * Promise类型
 */
export type PromiseValue<T> = T extends Promise<infer V> ? V : never;

/**
 * 数组元素类型
 */
export type ArrayElement<T> = T extends (infer U)[] ? U : never;

/**
 * 函数参数类型
 */
export type FunctionArgs<T> = T extends (...args: infer A) => any ? A : never;

/**
 * 函数返回类型
 */
export type FunctionReturn<T> = T extends (...args: any[]) => infer R ? R : never;

/**
 * 深度必需
 */
export type DeepRequired<T> = {
  [P in keyof T]-?: DeepRequired<T[P]>;
};

/**
 * 深度可选
 */
export type DeepPartial<T> = {
  [P in keyof T]?: DeepPartial<T[P]>;
};

/**
 * 深度只读
 */
export type DeepReadonly<T> = {
  readonly [P in keyof T]: DeepReadonly<T[P]>;
};

/**
 * 提取函数类型
 */
export type ExtractFunction<T> = T extends (...args: any[]) => any ? T : never;

/**
 * 提取Promise类型
 */
export type ExtractPromise<T> = T extends Promise<any> ? T : never;

/**
 * 联合类型转交叉类型
 */
export type UnionToIntersection<U> = (U extends any ? (k: U) => void : never) extends (
  k: infer I
) => void
  ? I
  : never;

/**
 * 元组转联合
 */
export type TupleToUnion<T extends any[]> = T[number];

/**
 * 联合类型转元组
 */
export type UnionToTuple<T, L = LastOf<UnionToIntersection<T extends any ? () => T : never>> = any> =
  [T] extends [never]
    ? []
    : [...UnionToTuple<Exclude<T, L>>, L];

/**
 * 最后一个元素
 */
type LastOf<T> = UnionToIntersection<T extends any ? () => T : never> extends () => infer R
  ? R
  : never;

/**
 * ================
 * 常量类型
 * ================
 */

/**
 * 应用配置
 */
export interface AppConfig {
  API_BASE_URL: string;
  API_TIMEOUT: number;
  WebSocket_URL: string;
  UPLOAD_MAX_SIZE: number;
  UPLOAD_ALLOWED_TYPES: string[];
}

/**
 * 环境变量
 */
export interface EnvConfig {
  NODE_ENV: 'development' | 'production' | 'test';
  VITE_API_BASE_URL?: string;
  VITE_WS_URL?: string;
}

/**
 * ================
 * 导出所有类型
 * ================
 */

export type {
  // React相关
  ReactNode,
  ReactElement,
  ComponentType,
  FC,
  MouseEvent,
  ChangeEvent,
  FormEvent,
  EventHandler,
} from 'react';

export type {
  // React Router相关
  NavigateFunction,
  Location,
  Params,
  Path,
} from 'react-router-dom';
