// frontend/src/components/BookList.tsx
import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import { Plus, BookOpen, Trash2, Clock } from 'lucide-react';
import { useBookStore } from '../stores/bookStore';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';

export const BookList: React.FC = () => {
  const { books, fetchBooks, deleteBook, isLoading } = useBookStore();

  useEffect(() => {
    fetchBooks();
  }, []);

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (window.confirm('确定要删除这本绘本吗？')) {
      await deleteBook(id);
      toast.success('删除成功');
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-800">我的绘本</h1>
        <Link
          to="/create"
          className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:opacity-90 transition-opacity"
        >
          <Plus className="w-5 h-5" />
          创作新绘本
        </Link>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-purple-500 border-t-transparent" />
        </div>
      ) : books.length === 0 ? (
        <div className="text-center py-16">
          <BookOpen className="w-16 h-16 mx-auto text-gray-300 mb-4" />
          <h3 className="text-xl text-gray-500 mb-2">还没有绘本</h3>
          <p className="text-gray-400 mb-6">开始创作你的第一本AI绘本吧！</p>
          <Link
            to="/create"
            className="inline-flex items-center gap-2 px-6 py-3 bg-purple-500 text-white rounded-lg hover:bg-purple-600"
          >
            <Plus className="w-5 h-5" />
            开始创作
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {books.map((book, index) => (
            <motion.div
              key={book.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Link
                to={`/book/${book.id}`}
                className="block bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow group"
              >
                {/* 封面图 */}
                <div className="relative h-48 bg-gradient-to-br from-purple-100 to-pink-100">
                  {book.cover_image ? (
                    <img
                      src={book.cover_image}
                      alt={book.title}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <BookOpen className="w-16 h-16 text-purple-300" />
                    </div>
                  )}
                  
                  {/* 状态标签 */}
                  <div className={`absolute top-3 right-3 px-2 py-1 rounded text-xs font-medium ${
                    book.status === 'completed' ? 'bg-green-500 text-white' :
                    book.status === 'generating' ? 'bg-yellow-500 text-white' :
                    'bg-gray-500 text-white'
                  }`}>
                    {book.status === 'completed' ? '已完成' :
                     book.status === 'generating' ? '生成中' : '草稿'}
                  </div>
                  
                  {/* 删除按钮 */}
                  <button
                    onClick={(e) => handleDelete(book.id, e)}
                    className="absolute top-3 left-3 p-2 bg-white/80 rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-100"
                  >
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </button>
                </div>

                {/* 信息 */}
                <div className="p-4">
                  <h3 className="font-bold text-lg text-gray-800 mb-1 truncate">
                    {book.title}
                  </h3>
                  <p className="text-sm text-gray-500 mb-3 line-clamp-2">
                    {book.description}
                  </p>
                  
                  <div className="flex items-center justify-between text-xs text-gray-400">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatDate(book.created_at)}
                    </span>
                    <span className="px-2 py-1 bg-purple-100 text-purple-600 rounded">
                      {book.style}
                    </span>
                  </div>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
};
