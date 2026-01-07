// frontend/src/components/BookViewer.tsx
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronLeft, ChevronRight, Edit2, RefreshCw,
  Download, ZoomIn, ZoomOut
} from 'lucide-react';
import { useBookStore } from '../stores/bookStore';
import { bookApi } from '../services/api';
import toast from 'react-hot-toast';

interface BookViewerProps {
  bookId: number;
}

export const BookViewer: React.FC<BookViewerProps> = ({ bookId }) => {
  const { currentBook, fetchBook, updatePage, regenerateImage, isLoading } = useBookStore();
  const [currentPage, setCurrentPage] = useState(0);
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState('');
  const [viewMode, setViewMode] = useState<'single' | 'spread'>('single');
  const [zoom, setZoom] = useState(1);

  useEffect(() => {
    fetchBook(bookId);
  }, [bookId]);

  useEffect(() => {
    if (currentBook?.pages[currentPage]) {
      setEditText(currentBook.pages[currentPage].text_content);
    }
  }, [currentPage, currentBook]);

  if (!currentBook) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-purple-500 border-t-transparent" />
      </div>
    );
  }

  const totalPages = currentBook.pages.length;
  const page = currentBook.pages[currentPage];

  const handlePrevPage = () => {
    setCurrentPage(Math.max(0, currentPage - 1));
  };

  const handleNextPage = () => {
    setCurrentPage(Math.min(totalPages - 1, currentPage + 1));
  };

  const handleSaveEdit = async () => {
    if (page) {
      await updatePage(bookId, page.page_number, editText);
      setIsEditing(false);
      toast.success('保存成功');
    }
  };

  const handleRegenerateImage = async () => {
    if (page) {
      toast.loading('正在重新生成图片...');
      await regenerateImage(bookId, page.page_number);
      toast.dismiss();
      toast.success('图片已更新');
    }
  };

  const handleExport = async (format: string) => {
    try {
      toast.loading('正在导出...');
      const result = await bookApi.export(bookId, format, 'high');
      toast.dismiss();
      toast.success('导出成功');
      // 下载文件
      window.open(result.download_url, '_blank');
    } catch (error) {
      toast.dismiss();
      toast.error('导出失败');
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-4">
      {/* 工具栏 */}
      <div className="flex items-center justify-between mb-4 bg-white rounded-lg shadow p-3">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold text-gray-800">{currentBook.title}</h1>
          <span className={`px-2 py-1 rounded text-xs ${
            currentBook.status === 'completed' ? 'bg-green-100 text-green-600' :
            currentBook.status === 'generating' ? 'bg-yellow-100 text-yellow-600' :
            'bg-gray-100 text-gray-600'
          }`}>
            {currentBook.status === 'completed' ? '已完成' :
             currentBook.status === 'generating' ? '生成中' : '草稿'}
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          {/* 缩放控制 */}
          <button
            onClick={() => setZoom(Math.max(0.5, zoom - 0.1))}
            className="p-2 hover:bg-gray-100 rounded"
          >
            <ZoomOut className="w-5 h-5" />
          </button>
          <span className="text-sm text-gray-600">{Math.round(zoom * 100)}%</span>
          <button
            onClick={() => setZoom(Math.min(2, zoom + 0.1))}
            className="p-2 hover:bg-gray-100 rounded"
          >
            <ZoomIn className="w-5 h-5" />
          </button>
          
          <div className="w-px h-6 bg-gray-300 mx-2" />
          
          {/* 视图模式 */}
          <button
            onClick={() => setViewMode(viewMode === 'single' ? 'spread' : 'single')}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded"
          >
            {viewMode === 'single' ? '单页' : '跨页'}
          </button>
          
          <div className="w-px h-6 bg-gray-300 mx-2" />
          
          {/* 导出按钮 */}
          <div className="relative group">
            <button className="flex items-center gap-1 px-3 py-2 bg-purple-500 text-white rounded hover:bg-purple-600">
              <Download className="w-4 h-4" />
              导出
            </button>
            <div className="absolute right-0 mt-1 w-32 bg-white rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
              <button
                onClick={() => handleExport('pdf')}
                className="w-full px-4 py-2 text-left hover:bg-gray-100 rounded-t-lg"
              >
                导出PDF
              </button>
              <button
                onClick={() => handleExport('png')}
                className="w-full px-4 py-2 text-left hover:bg-gray-100 rounded-b-lg"
              >
                导出图片
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 绘本内容 */}
      <div className="relative bg-gray-100 rounded-2xl overflow-hidden" style={{ minHeight: '600px' }}>
        <AnimatePresence mode="wait">
          <motion.div
            key={currentPage}
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ duration: 0.3 }}
            className="flex h-full"
            style={{ transform: `scale(${zoom})`, transformOrigin: 'center center' }}
          >
            {/* 图片区域 */}
            <div className="flex-1 p-8 flex items-center justify-center bg-white">
              {page?.image_url ? (
                <div className="relative group">
                  <img
                    src={page.image_url}
                    alt={`第${page.page_number}页`}
                    className="max-w-full max-h-[500px] rounded-lg shadow-lg"
                  />
                  <button
                    onClick={handleRegenerateImage}
                    disabled={isLoading}
                    className="absolute top-2 right-2 p-2 bg-white/80 rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-white"
                  >
                    <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
                  </button>
                </div>
              ) : (
                <div className="w-full h-64 bg-gray-200 rounded-lg flex items-center justify-center">
                  <span className="text-gray-400">图片生成中...</span>
                </div>
              )}
            </div>

            {/* 文字区域 */}
            <div className="w-96 p-8 bg-gradient-to-br from-amber-50 to-orange-50 flex flex-col">
              <div className="flex-1">
                {isEditing ? (
                  <textarea
                    value={editText}
                    onChange={(e) => setEditText(e.target.value)}
                    className="w-full h-full p-4 rounded-lg border-2 border-purple-300 focus:border-purple-500 resize-none"
                  />
                ) : (
                  <p className="text-lg leading-relaxed text-gray-800 whitespace-pre-wrap">
                    {page?.text_content}
                  </p>
                )}
              </div>
              
              <div className="mt-4 flex justify-between items-center">
                <span className="text-sm text-gray-500">
                  第 {currentPage + 1} / {totalPages} 页
                </span>
                
                {isEditing ? (
                  <div className="flex gap-2">
                    <button
                      onClick={() => setIsEditing(false)}
                      className="px-3 py-1 text-gray-600 hover:bg-gray-200 rounded"
                    >
                      取消
                    </button>
                    <button
                      onClick={handleSaveEdit}
                      className="px-3 py-1 bg-purple-500 text-white rounded hover:bg-purple-600"
                    >
                      保存
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setIsEditing(true)}
                    className="flex items-center gap-1 px-3 py-1 text-purple-600 hover:bg-purple-100 rounded"
                  >
                    <Edit2 className="w-4 h-4" />
                    编辑
                  </button>
                )}
              </div>
            </div>
          </motion.div>
        </AnimatePresence>

        {/* 翻页按钮 */}
        <button
          onClick={handlePrevPage}
          disabled={currentPage === 0}
          className="absolute left-4 top-1/2 -translate-y-1/2 p-3 bg-white/80 rounded-full shadow-lg hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ChevronLeft className="w-6 h-6" />
        </button>
        
        <button
          onClick={handleNextPage}
          disabled={currentPage === totalPages - 1}
          className="absolute right-4 top-1/2 -translate-y-1/2 p-3 bg-white/80 rounded-full shadow-lg hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ChevronRight className="w-6 h-6" />
        </button>
      </div>

      {/* 页面缩略图 */}
      <div className="mt-4 flex gap-2 overflow-x-auto pb-2">
        {currentBook.pages.map((p, index) => (
          <button
            key={p.page_number}
            onClick={() => setCurrentPage(index)}
            className={`flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden border-2 transition-all ${
              currentPage === index ? 'border-purple-500 shadow-lg' : 'border-transparent hover:border-gray-300'
            }`}
          >
            {p.image_url ? (
              <img src={p.image_url} alt="" className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full bg-gray-200 flex items-center justify-center text-xs text-gray-400">
                {p.page_number}
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
};
