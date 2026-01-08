# 导出功能修复说明

## 修复的问题

### 1. **下载URL路径错误**
**问题**: 返回的 `download_url` 包含完整文件路径，不是有效的URL
```python
# 之前 (错误)
"download_url": f"/api/v1/download/{output_path}"  # output_path 是完整路径

# 修复后
return {
    "message": "导出成功",
    "filename": filename,  # 只返回文件名
    "file_type": file_type,
    "book_id": book_id
}
```

### 2. **缺少文件下载API端点**
**问题**: 没有 `/download` 路由处理文件下载

**修复**: 在 [routes.py:203-235](backend/app/api/routes.py#L203-L235) 添加了下载端点
```python
@router.get("/download/{book_id}/{filename}")
async def download_file(book_id: int, filename: str):
    """下载导出的文件"""
    # 安全检查
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="无效的文件名")

    # 查找文件
    file_path = Path(settings.OUTPUT_DIR) / filename
    if not file_path.exists():
        book_dir = Path(settings.OUTPUT_DIR) / f"book_{book_id}"
        file_path = book_dir / filename

    # 返回文件
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
    )
```

**安全特性**:
- 路径遍历攻击防护 (检查 `..`、`/`、`\`)
- 文件存在性验证
- 正确的 MIME 类型设置

### 3. **前端下载逻辑问题**
**问题**: 使用 `window.open` 无法正确触发下载

**修复**: 在 [BookViewer.tsx:79-100](frontend/src/components/BookViewer.tsx#L79-L100) 使用编程式下载
```typescript
const handleExport = async (format: string) => {
  try {
    toast.loading('正在导出，请稍候...');
    const result = await bookApi.export(bookId, format, 'high');
    toast.dismiss();
    toast.success('导出成功！');

    // 构建下载URL
    const downloadUrl = bookApi.getDownloadUrl(result.book_id, result.filename);

    // 创建隐藏的a标签来触发下载
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = result.filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } catch (error: any) {
    toast.dismiss();
    toast.error(error.response?.data?.detail || '导出失败，请重试');
  }
};
```

### 4. **中文字体支持增强**
**问题**: 只有单一字体路径，找不到时中文会显示为方块

**修复**: 在 [export_service.py:28-59](backend/app/services/export_service.py#L28-L59) 添加多字体路径自动查找
- 支持多种中文字体（SimHei、微软雅黑、宋体）
- 自动检测 Windows/Linux/macOS 系统字体
- 找不到字体时给出警告提示

## 测试导出功能

### PDF 导出测试
1. 选择一个已完成的绘本
2. 点击"导出" -> "导出PDF"
3. 等待生成完成（首次可能较慢）
4. 应该自动下载 PDF 文件
5. 打开 PDF 检查：
   - ✅ 封面显示正确
   - ✅ 每页图片和文字显示正常
   - ✅ 中文显示正常（不是方块）
   - ✅ 页码正确

### 图片导出测试
1. 点击"导出" -> "导出图片"
2. 应该下载第一页的图片

## 文件变更清单

### 后端
- [backend/app/api/routes.py:5](backend/app/api/routes.py#L5) - 添加 `Path` 导入
- [backend/app/api/routes.py:168-235](backend/app/api/routes.py#L168-L235) - 重构导出和下载API
- [backend/app/services/export_service.py:28-59](backend/app/services/export_service.py#L28-L59) - 增强字体查找逻辑

### 前端
- [frontend/src/services/api.ts:102-120](frontend/src/services/api.ts#L102-L120) - 更新API接口
- [frontend/src/components/BookViewer.tsx:79-100](frontend/src/components/BookViewer.tsx#L79-L100) - 修复下载逻辑

## 常见问题

### Q: 导出失败"文件不存在"
**A**: 检查 `backend/outputs` 目录是否存在且有写权限

### Q: PDF中文显示为方块
**A**:
- Windows: 应该会自动找到系统字体
- Linux: 需要安装中文字体 `sudo apt-get install fonts-wqy-zenhei`
- macOS: 应该会自动找到系统字体

### Q: 点击导出没反应
**A**:
1. 打开浏览器控制台查看错误
2. 检查后端是否正常运行
3. 查看后端日志确认导出是否成功

### Q: 导出很慢
**A**:
- 第一次导出会下载所有图片，需要时间
- 后续导出会使用缓存的图片
- 可以在代码中调整导出质量参数来平衡速度和质量
