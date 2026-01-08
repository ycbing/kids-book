# 实时更新优化说明

## 问题分析

原有问题：
- 前端只在组件挂载时获取一次绘本数据
- 后端生成图片是异步后台任务，前端无法实时感知进度
- 用户进入详情页看到的是旧数据，图片一直显示"生成中"状态

## 解决方案

采用**轮询 + WebSocket 双重保障**机制：

### 1. **轮询机制** (保底方案)
- **位置**: `frontend/src/stores/bookStore.ts:129-159`
- **策略**: 每 3 秒轮询一次绘本状态
- **智能停止**:
  - 生成完成时自动停止
  - 生成失败时自动停止
- **优点**: 简单可靠，确保最终一致性

### 2. **WebSocket 实时推送** (主要方案)
- **后端实现**:
  - `backend/app/services/book_service.py:40-168` - 在生成过程中推送进度
  - `backend/app/api/routes.py:42-62` - 传递 WebSocket manager

- **前端实现**:
  - `frontend/src/services/websocket.ts` - WebSocket 服务层
  - `frontend/src/stores/bookStore.ts:167-251` - 状态管理集成
  - `frontend/src/components/BookViewer.tsx:16-34` - 组件层集成

- **推送消息类型**:
  - `status_update` - 状态更新（生成开始）
  - `page_completed` - 单页图片生成完成（实时更新UI）
  - `image_progress` - 整体进度更新
  - `generation_completed` - 生成完成
  - `generation_failed` - 生成失败

## 用户体验提升

### 之前：
- ❌ 图片一直显示"生成中"
- ❌ 需要手动刷新页面才能看到更新
- ❌ 不知道进度，体验不佳

### 现在：
- ✅ 实时显示生成进度（已完成 X / 总页数）
- ✅ 图片生成完成后立即显示（无需刷新）
- ✅ 清晰的状态指示器
- ✅ 自动停止轮询，节省资源
- ✅ WebSocket 断线自动重连

## 技术亮点

1. **渐进式更新**：每生成一页图片就立即推送更新，不用等全部完成
2. **优雅降级**：WebSocket 失败时轮询机制依然工作
3. **资源管理**：组件卸载时自动清理连接和定时器
4. **错误处理**：生成失败时推送错误信息

## 文件变更清单

### 后端
- `backend/app/services/book_service.py` - 添加 WebSocket 推送逻辑
- `backend/app/api/routes.py` - 传递 WebSocket manager

### 前端
- `frontend/src/services/websocket.ts` - **新增** WebSocket 服务
- `frontend/src/stores/bookStore.ts` - 集成轮询和 WebSocket
- `frontend/src/components/BookViewer.tsx` - 显示进度指示器

## 测试建议

1. 创建新绘本，观察进度是否实时更新
2. 刷新页面，确认能看到已生成的图片
3. 切换到其他页面再回来，确认轮询正常工作
4. 查看 Console，确认 WebSocket 消息正常接收
