// frontend/src/App.tsx
import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { BookOpen, Home, PlusCircle } from 'lucide-react';

import { BookCreator } from './components/BookCreator';
import { BookViewer } from './components/BookViewer';
import { BookList } from './components/BookList';

const queryClient = new QueryClient();

// 导航栏组件
const Navbar: React.FC = () => {
  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2 text-xl font-bold text-purple-600">
            <BookOpen className="w-8 h-8" />
            AI绘本工坊
          </Link>
          
          <div className="flex items-center gap-4">
            <Link
              to="/"
              className="flex items-center gap-1 px-3 py-2 text-gray-600 hover:text-purple-600 transition-colors"
            >
              <Home className="w-5 h-5" />
              首页
            </Link>
            <Link
              to="/create"
              className="flex items-center gap-1 px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors"
            >
              <PlusCircle className="w-5 h-5" />
              创作绘本
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
};

// 首页组件
const HomePage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-50 to-pink-50">
      {/* Hero区域 */}
      <div className="max-w-6xl mx-auto px-4 py-16 text-center">
        <h1 className="text-5xl font-bold text-gray-800 mb-6">
          用AI创作专属
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-500 to-pink-500">
            儿童绘本
          </span>
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
          只需输入主题，AI将为您生成完整的故事和精美配图，
          创作独一无二的儿童绘本
        </p>
        <Link
          to="/create"
          className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-lg font-semibold rounded-full hover:opacity-90 transition-opacity shadow-lg"
        >
          <PlusCircle className="w-6 h-6" />
          开始创作
        </Link>
      </div>

      {/* 特性展示 */}
      <div className="max-w-6xl mx-auto px-4 py-16">
        <div className="grid md:grid-cols-3 gap-8">
          <div className="bg-white p-6 rounded-2xl shadow-lg text-center">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-3xl">✨</span>
            </div>
            <h3 className="text-xl font-bold mb-2">AI智能创作</h3>
            <p className="text-gray-600">
              基于先进的AI技术，自动生成适合儿童的故事内容
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-2xl shadow-lg text-center">
            <div className="w-16 h-16 bg-pink-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-3xl">🎨</span>
            </div>
            <h3 className="text-xl font-bold mb-2">精美配图</h3>
            <p className="text-gray-600">
              多种艺术风格可选，AI自动生成与故事匹配的插画
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-2xl shadow-lg text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-3xl">📚</span>
            </div>
            <h3 className="text-xl font-bold mb-2">一键导出</h3>
            <p className="text-gray-600">
              支持导出PDF和图片，方便打印或分享
            </p>
          </div>
        </div>
      </div>

      {/* 我的绘本 */}
      <BookList />
    </div>
  );
};

// 绘本详情页
const BookPage: React.FC = () => {
  const bookId = parseInt(window.location.pathname.split('/').pop() || '0');
  return <BookViewer bookId={bookId} />;
};

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50">
          <Navbar />
          <main>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/create" element={<BookCreator />} />
              <Route path="/book/:id" element={<BookPage />} />
            </Routes>
          </main>
        </div>
        <Toaster position="top-center" />
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
