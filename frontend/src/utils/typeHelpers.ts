// frontend/src/utils/typeHelpers.ts

import {
  Book,
  Page,
  User,
  BookStatus,
  BookStyle,
  TargetAge,
  NotificationType,
  ErrorType,
  WebSocketMessageType,
  ConnectionStatus,
  ExportFormat,
  ExportQuality,
} from '../types';

/**
 * ================
 * 类型守卫
 * ================
 */

/**
 * 检查是否为Book
 */
export function isBook(obj: any): obj is Book {
  return (
    obj &&
    typeof obj === 'object' &&
    typeof obj.id === 'number' &&
    typeof obj.title === 'string' &&
    typeof obj.status === 'string' &&
    Array.isArray(obj.pages)
  );
}

/**
 * 检查是否为Page
 */
export function isPage(obj: any): obj is Page {
  return (
    obj &&
    typeof obj === 'object' &&
    typeof obj.page_number === 'number' &&
    typeof obj.text_content === 'string' &&
    typeof obj.image_prompt === 'string'
  );
}

/**
 * 检查是否为User
 */
export function isUser(obj: any): obj is User {
  return (
    obj &&
    typeof obj === 'object' &&
    typeof obj.id === 'number' &&
    typeof obj.username === 'string' &&
    typeof obj.email === 'string'
  );
}

/**
 * 检查是否为有效的BookStatus
 */
export function isBookStatus(status: string): status is BookStatus {
  return Object.values(BookStatus).includes(status as BookStatus);
}

/**
 * 检查是否为有效的BookStyle
 */
export function isBookStyle(style: string): style is BookStyle {
  return Object.values(BookStyle).includes(style as BookStyle);
}

/**
 * 检查是否为有效的TargetAge
 */
export function isTargetAge(age: string): age is TargetAge {
  return Object.values(TargetAge).includes(age as TargetAge);
}

/**
 * 检查是否为有效的NotificationType
 */
export function isNotificationType(type: string): type is NotificationType {
  return Object.values(NotificationType).includes(type as NotificationType);
}

/**
 * 检查是否为有效的ErrorType
 */
export function isErrorType(type: string): type is ErrorType {
  return Object.values(ErrorType).includes(type as ErrorType);
}

/**
 * 检查是否为有效的WebSocketMessageType
 */
export function isWebSocketMessageType(
  type: string
): type is WebSocketMessageType {
  return Object.values(WebSocketMessageType).includes(type as WebSocketMessageType);
}

/**
 * 检查是否为有效的ConnectionStatus
 */
export function isConnectionStatus(status: string): status is ConnectionStatus {
  return Object.values(ConnectionStatus).includes(status as ConnectionStatus);
}

/**
 * 检查是否为有效的ExportFormat
 */
export function isExportFormat(format: string): format is ExportFormat {
  return Object.values(ExportFormat).includes(format as ExportFormat);
}

/**
 * 检查是否为有效的ExportQuality
 */
export function isExportQuality(quality: string): quality is ExportQuality {
  return Object.values(ExportQuality).includes(quality as ExportQuality);
}

/**
 * 检查是否为空值
 */
export function isEmpty(value: any): value is null | undefined | '' {
  return (
    value === null ||
    value === undefined ||
    value === '' ||
    (Array.isArray(value) && value.length === 0) ||
    (typeof value === 'object' && Object.keys(value).length === 0)
  );
}

/**
 * 检查是否为Promise
 */
export function isPromise(value: any): value is Promise<any> {
  return value && typeof value.then === 'function';
}

/**
 * 检查是否为Date
 */
export function isDate(value: any): value is Date {
  return value instanceof Date;
}

/**
 * 检查是否为Array
 */
export function isArray<T = any>(value: any): value is T[] {
  return Array.isArray(value);
}

/**
 * 检查是否为Object
 */
export function isObject(value: any): value is Record<string, any> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

/**
 * 检查是否为函数
 */
export function isFunction(value: any): value is Function {
  return typeof value === 'function';
}

/**
 * 检查是否为字符串
 */
export function isString(value: any): value is string {
  return typeof value === 'string';
}

/**
 * 检查是否为数字
 */
export function isNumber(value: any): value is number {
  return typeof value === 'number' && !isNaN(value);
}

/**
 * 检查是否为布尔值
 */
export function isBoolean(value: any): value is boolean {
  return typeof value === 'boolean';
}

/**
 * 检查是否为null或undefined
 */
export function isNil(value: any): value is null | undefined {
  return value === null || value === undefined;
}

/**
 * ================
 * 类型断言函数
 * ================
 */

/**
 * 断言非空
 */
export function assertNonNull<T>(value: T | null | undefined): T {
  if (value === null || value === undefined) {
    throw new Error('Value is null or undefined');
  }
  return value;
}

/**
 * 断言为字符串
 */
export function assertString(value: any): string {
  if (typeof value !== 'string') {
    throw new Error(`Expected string, got ${typeof value}`);
  }
  return value;
}

/**
 * 断言为数字
 */
export function assertNumber(value: any): number {
  if (typeof value !== 'number' || isNaN(value)) {
    throw new Error(`Expected number, got ${typeof value}`);
  }
  return value;
}

/**
 * 断言为数组
 */
export function assertArray<T>(value: any): T[] {
  if (!Array.isArray(value)) {
    throw new Error(`Expected array, got ${typeof value}`);
  }
  return value as T[];
}

/**
 * 断言为对象
 */
export function assertObject(value: any): Record<string, any> {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    throw new Error(`Expected object, got ${typeof value}`);
  }
  return value;
}

/**
 * ================
 * 类型转换函数
 * ================
 */

/**
 * 转换为Book
 */
export function toBook(obj: any): Book | null {
  if (isBook(obj)) {
    return obj;
  }
  return null;
}

/**
 * 转换为Book数组
 */
export function toBookArray(obj: any): Book[] {
  if (Array.isArray(obj)) {
    return obj.filter(isBook);
  }
  return [];
}

/**
 * 安全访问对象属性
 */
export function safeGet<T, K extends keyof T>(
  obj: T | null | undefined,
  key: K
): T[K] | undefined {
  return obj?.[key];
}

/**
 * 深度获取对象属性
 */
export function deepGet<T>(obj: any, path: string, defaultValue?: T): T {
  const keys = path.split('.');
  let result = obj;

  for (const key of keys) {
    if (result === null || result === undefined) {
      return defaultValue as T;
    }
    result = result[key];
  }

  return result !== undefined ? (result as T) : (defaultValue as T);
}

/**
 * ================
 * 类型验证工具
 * ================
 */

/**
 * 验证Book对象
 */
export function validateBook(obj: any): obj is Book {
  if (!isBook(obj)) {
    return false;
  }

  // 验证status
  if (!isBookStatus(obj.status)) {
    return false;
  }

  // 验证pages
  if (!Array.isArray(obj.pages)) {
    return false;
  }

  for (const page of obj.pages) {
    if (!isPage(page)) {
      return false;
    }
  }

  return true;
}

/**
 * 验证Email格式
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * 验证URL格式
 */
export function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * 验证ISBN格式
 */
export function isValidISBN(isbn: string): boolean {
  // 移除所有非数字字符
  const cleaned = isbn.replace(/[^0-9X]/gi, '');

  // ISBN-10或ISBN-13
  if (cleaned.length === 10) {
    return isValidISBN10(cleaned);
  } else if (cleaned.length === 13) {
    return isValidISBN13(cleaned);
  }

  return false;
}

/**
 * 验证ISBN-10
 */
function isValidISBN10(isbn: string): boolean {
  let sum = 0;
  for (let i = 0; i < 9; i++) {
    sum += (10 - i) * parseInt(isbn[i], 10);
  }
  const checksum = isbn[9].toUpperCase() === 'X' ? 10 : parseInt(isbn[9], 10);
  return sum % 11 === checksum % 11;
}

/**
 * 验证ISBN-13
 */
function isValidISBN13(isbn: string): boolean {
  let sum = 0;
  for (let i = 0; i < 12; i++) {
    sum += (i % 2 === 0 ? 1 : 3) * parseInt(isbn[i], 10);
  }
  const checksum = (10 - (sum % 10)) % 10;
  return checksum === parseInt(isbn[12], 10);
}

/**
 * 验证用户名格式
 */
export function isValidUsername(username: string): boolean {
  // 3-20个字符，只能包含字母、数字、下划线
  const usernameRegex = /^[a-zA-Z0-9_]{3,20}$/;
  return usernameRegex.test(username);
}

/**
 * 验证密码强度
 */
export function validatePassword(password: string): {
  isValid: boolean;
  strength: 'weak' | 'medium' | 'strong';
  errors: string[];
} {
  const errors: string[] = [];

  if (password.length < 8) {
    errors.push('密码至少需要8个字符');
  }

  if (!/[a-z]/.test(password)) {
    errors.push('密码需要包含小写字母');
  }

  if (!/[A-Z]/.test(password)) {
    errors.push('密码需要包含大写字母');
  }

  if (!/[0-9]/.test(password)) {
    errors.push('密码需要包含数字');
  }

  if (!/[^a-zA-Z0-9]/.test(password)) {
    errors.push('密码需要包含特殊字符');
  }

  // 计算强度
  let strength: 'weak' | 'medium' | 'strong' = 'weak';
  if (errors.length === 0) {
    strength = 'strong';
  } else if (errors.length <= 2) {
    strength = 'medium';
  }

  return {
    isValid: errors.length === 0,
    strength,
    errors,
  };
}

/**
 * ================
 * 类型推断工具
 * ================
 */

/**
 * 获取枚举值数组
 */
export function getEnumValues<T extends Record<string, string | number>>(
  enumObj: T
): Array<T[keyof T]> {
  return Object.values(enumObj);
}

/**
 * 获取枚举键数组
 */
export function getEnumKeys<T extends Record<string, string | number>>(
  enumObj: T
): Array<keyof T> {
  return Object.keys(enumObj) as Array<keyof T>;
}

/**
 * 从值获取枚举键
 */
export function getEnumKeyByValue<T extends Record<string, string | number>>(
  enumObj: T,
  value: T[keyof T]
): keyof T | undefined {
  return (Object.keys(enumObj) as Array<keyof T>).find(
    (key) => enumObj[key] === value
  );
}

/**
 * ================
 * 泛型类型工具
 * ================
 */

/**
 * 确保值不为null/undefined
 */
export function ensure<T>(value: T | null | undefined, message?: string): T {
  if (value === null || value === undefined) {
    throw new Error(message || 'Value is null or undefined');
  }
  return value;
}

/**
 * 获取数组第一个元素
 */
export function first<T>(array: T[]): T | undefined {
  return array[0];
}

/**
 * 获取数组最后一个元素
 */
export function last<T>(array: T[]): T | undefined {
  return array[array.length - 1];
}

/**
 * 数组去重
 */
export function unique<T>(array: T[]): T[] {
  return Array.from(new Set(array));
}

/**
 * 数组分组
 */
export function groupBy<T, K extends keyof T>(
  array: T[],
  key: K
): Record<string, T[]> {
  return array.reduce((result, item) => {
    const groupKey = String(item[key]);
    if (!result[groupKey]) {
      result[groupKey] = [];
    }
    result[groupKey].push(item);
    return result;
  }, {} as Record<string, T[]>);
}

/**
 * 数组排序
 */
export function sortBy<T>(
  array: T[],
  selector: (item: T) => any,
  order: 'asc' | 'desc' = 'asc'
): T[] {
  return [...array].sort((a, b) => {
    const aVal = selector(a);
    const bVal = selector(b);

    if (aVal < bVal) return order === 'asc' ? -1 : 1;
    if (aVal > bVal) return order === 'asc' ? 1 : -1;
    return 0;
  });
}

/**
 * 数组分块
 */
export function chunk<T>(array: T[], size: number): T[][] {
  const result: T[][] = [];
  for (let i = 0; i < array.length; i += size) {
    result.push(array.slice(i, i + size));
  }
  return result;
}

/**
 * 对象映射
 */
export function mapObject<T, U>(
  obj: Record<string, T>,
  mapper: (key: string, value: T) => [string, U]
): Record<string, U> {
  return Object.fromEntries(
    Object.entries(obj).map(([key, value]) => mapper(key, value))
  );
}

/**
 * 对象过滤
 */
export function filterObject<T>(
  obj: Record<string, T>,
  predicate: (key: string, value: T) => boolean
): Record<string, T> {
  return Object.fromEntries(
    Object.entries(obj).filter(([key, value]) => predicate(key, value))
  ) as Record<string, T>;
}

/**
 * 对象合并
 */
export function mergeObjects<T extends Record<string, any>>(
  ...objs: Partial<T>[]
): T {
  return Object.assign({}, ...objs) as T;
}

/**
 * 深度克隆
 */
export function deepClone<T>(obj: T): T {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }

  if (obj instanceof Date) {
    return new Date(obj.getTime()) as any;
  }

  if (Array.isArray(obj)) {
    return obj.map((item) => deepClone(item)) as any;
  }

  const clonedObj = {} as T;
  for (const key in obj) {
    if (obj.hasOwnProperty(key)) {
      (clonedObj as any)[key] = deepClone(obj[key]);
    }
  }

  return clonedObj;
}

/**
 * 深度比较
 */
export function deepEqual(a: any, b: any): boolean {
  if (a === b) return true;

  if (typeof a !== typeof b) return false;
  if (typeof a !== 'object' || a === null || b === null) return false;

  if (Array.isArray(a) !== Array.isArray(b)) return false;
  if (Array.isArray(a)) {
    if (a.length !== b.length) return false;
    return a.every((item, index) => deepEqual(item, b[index]));
  }

  const keysA = Object.keys(a);
  const keysB = Object.keys(b);

  if (keysA.length !== keysB.length) return false;

  for (const key of keysA) {
    if (!keysB.includes(key) || !deepEqual(a[key], b[key])) {
      return false;
    }
  }

  return true;
}

export default {
  // 类型守卫
  isBook,
  isPage,
  isUser,
  isBookStatus,
  isBookStyle,
  isTargetAge,
  isEmpty,
  isPromise,
  isDate,
  isArray,
  isObject,
  isFunction,
  isString,
  isNumber,
  isBoolean,
  isNil,

  // 类型断言
  assertNonNull,
  assertString,
  assertNumber,
  assertArray,
  assertObject,

  // 类型转换
  toBook,
  toBookArray,
  safeGet,
  deepGet,

  // 验证
  validateBook,
  isValidEmail,
  isValidUrl,
  isValidISBN,
  isValidUsername,
  validatePassword,

  // 工具
  ensure,
  first,
  last,
  unique,
  groupBy,
  sortBy,
  chunk,
  mapObject,
  filterObject,
  mergeObjects,
  deepClone,
  deepEqual,
};
