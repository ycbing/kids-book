// frontend/src/components/BookCreator.tsx
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Wand2, BookOpen, Palette, Users, Sparkles } from 'lucide-react';
import { useBookStore } from '../stores/bookStore';
import toast from 'react-hot-toast';

const AGE_GROUPS = [
  { value: '0-3岁', label: '0-3岁 (幼儿)', icon: '👶' },
  { value: '3-6岁', label: '3-6岁 (学龄前)', icon: '💒' },
  { value: '6-9岁', label: '6-9岁 (低年级)', icon: '📚' },
  { value: '9-12岁', label: '9-12岁 (高年级)', icon: '🎓' },
];

const ART_STYLES = [
  { value: '水彩风格', label: '水彩风格', preview: '🎨' },
  { value: '卡通风格', label: '卡通风格', preview: '🎪' },
  { value: '扁平插画', label: '扁平插画', preview: '📐' },
  { value: '手绘风格', label: '手绘风格', preview: '✏️' },
  { value: '动漫风格', label: '动漫风格', preview: '🌸' },
  { value: '剪纸风格', label: '剪纸风格', preview: '✂️' },
];

const THEME_SUGGESTIONS = [
  '友谊与分享', '勇气与冒险', '环保与自然',
  '家庭与亲情', '梦想与坚持', '善良与助人',
  '好奇与探索', '诚实与信任'
];

export const BookCreator: React.FC = () => {
  const { createBook, isGenerating, generationProgress } = useBookStore();
  
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    title: '',
    theme: '',
    keywords: [] as string[],
    target_age: '3-6岁',
    style: '水彩风格',
    page_count: 8,
    custom_prompt: ''
  });
  const [keywordInput, setKeywordInput] = useState('');

  const handleAddKeyword = () => {
    if (keywordInput.trim() && formData.keywords.length < 5) {
      setFormData({
        ...formData,
        keywords: [...formData.keywords, keywordInput.trim()]
      });
      setKeywordInput('');
    }
  };

  const handleRemoveKeyword = (index: number) => {
    setFormData({
      ...formData,
      keywords: formData.keywords.filter((_, i) => i !== index)
    });
  };

  const handleSubmit = async () => {
    if (!formData.theme) {
      toast.error('请输入故事主题');
      return;
    }

    try {
      const book = await createBook(formData);
      toast.success('绘本创建成功！正在生成内容...');
      // 跳转到绘本详情页
      window.location.href = `/book/${book.id}`;
    } catch (error) {
      toast.error('创建失败，请重试');
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-2xl shadow-xl overflow-hidden"
      >
        {/* 头部 */}
        <div className="bg-gradient-to-r from-purple-500 to-pink-500 p-6 text-white">
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Wand2 className="w-8 h-8" />
            创作你的AI绘本
          </h1>
          <p className="mt-2 opacity-90">让AI帮你创作独一无二的儿童绘本故事</p>
        </div>

        {/* 步骤指示器 */}
        <div className="flex border-b">
          {[1, 2, 3].map((s) => (
            <button
              key={s}
              onClick={() => setStep(s)}
              className={`flex-1 py-4 text-center transition-colors ${
                step === s
                  ? 'bg-purple-50 text-purple-600 border-b-2 border-purple-500'
                  : 'text-gray-500 hover:bg-gray-50'
              }`}
            >
              {s === 1 && '📖 故事主题'}
              {s === 2 && '🎨 风格设置'}
              {s === 3 && '✨ 确认创建'}
            </button>
          ))}
        </div>

        {/* 步骤内容 */}
        <div className="p-6">
          <AnimatePresence mode="wait">
            {step === 1 && (
              <motion.div
                key="step1"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-6"
              >
                {/* 主题输入 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <BookOpen className="w-4 h-4 inline mr-1" />
                    故事主题 *
                  </label>
                  <input
                    type="text"
                    value={formData.theme}
                    onChange={(e) => setFormData({ ...formData, theme: e.target.value })}
                    placeholder="例如：小兔子学会分享"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                  
                  {/* 主题建议 */}
                  <div className="mt-3 flex flex-wrap gap-2">
                    {THEME_SUGGESTIONS.map((theme) => (
                      <button
                        key={theme}
                        onClick={() => setFormData({ ...formData, theme })}
                        className="px-3 py-1 bg-gray-100 hover:bg-purple-100 rounded-full text-sm text-gray-600 hover:text-purple-600 transition-colors"
                      >
                        {theme}
                      </button>
                    ))}
                  </div>
                </div>

                {/* 关键词 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    关键词（可选，最多5个）
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={keywordInput}
                      onChange={(e) => setKeywordInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleAddKeyword()}
                      placeholder="输入关键词后按回车"
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                    />
                    <button
                      onClick={handleAddKeyword}
                      className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600"
                    >
                      添加
                    </button>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {formData.keywords.map((kw, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-purple-100 text-purple-600 rounded-full text-sm flex items-center gap-1"
                      >
                        {kw}
                        <button
                          onClick={() => handleRemoveKeyword(index)}
                          className="hover:text-purple-800"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                </div>

                {/* 自定义要求 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    额外要求（可选）
                  </label>
                  <textarea
                    value={formData.custom_prompt}
                    onChange={(e) => setFormData({ ...formData, custom_prompt: e.target.value })}
                    placeholder="例如：希望故事中有一只会说话的小猫..."
                    rows={3}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </motion.div>
            )}

            {step === 2 && (
              <motion.div
                key="step2"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-6"
              >
                {/* 目标年龄 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    <Users className="w-4 h-4 inline mr-1" />
                    目标年龄段
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    {AGE_GROUPS.map((age) => (
                      <button
                        key={age.value}
                        onClick={() => setFormData({ ...formData, target_age: age.value })}
                        className={`p-4 rounded-lg border-2 transition-all ${
                          formData.target_age === age.value
                            ? 'border-purple-500 bg-purple-50'
                            : 'border-gray-200 hover:border-purple-300'
                        }`}
                      >
                        <span className="text-2xl">{age.icon}</span>
                        <p className="mt-1 font-medium">{age.label}</p>
                      </button>
                    ))}
                  </div>
                </div>

                {/* 绘画风格 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    <Palette className="w-4 h-4 inline mr-1" />
                    绘画风格
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {ART_STYLES.map((style) => (
                      <button
                        key={style.value}
                        onClick={() => setFormData({ ...formData, style: style.value })}
                        className={`p-4 rounded-lg border-2 transition-all ${
                          formData.style === style.value
                            ? 'border-purple-500 bg-purple-50'
                            : 'border-gray-200 hover:border-purple-300'
                        }`}
                      >
                        <span className="text-2xl">{style.preview}</span>
                        <p className="mt-1 text-sm font-medium">{style.label}</p>
                      </button>
                    ))}
                  </div>
                </div>

                {/* 页数 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    绘本页数: {formData.page_count}页
                  </label>
                  <input
                    type="range"
                    min="4"
                    max="16"
                    step="2"
                    value={formData.page_count}
                    onChange={(e) => setFormData({ ...formData, page_count: parseInt(e.target.value) })}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-purple-500"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>4页</span>
                    <span>16页</span>
                  </div>
                </div>
              </motion.div>
            )}

            {step === 3 && (
              <motion.div
                key="step3"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-6"
              >
                {/* 预览卡片 */}
                <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4">创作预览</h3>
                  
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600">故事主题</span>
                      <span className="font-medium">{formData.theme || '未设置'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">目标年龄</span>
                      <span className="font-medium">{formData.target_age}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">绘画风格</span>
                      <span className="font-medium">{formData.style}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">页数</span>
                      <span className="font-medium">{formData.page_count}页</span>
                    </div>
                    {formData.keywords.length > 0 && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">关键词</span>
                        <span className="font-medium">{formData.keywords.join('、')}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* 标题输入 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    绘本标题（可选，AI会自动生成）
                  </label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    placeholder="留空则由AI自动生成标题"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  />
                </div>

                {/* 生成进度 */}
                {isGenerating && (
                  <div className="bg-blue-50 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Sparkles className="w-5 h-5 text-blue-500 animate-pulse" />
                      <span className="font-medium text-blue-700">
                        {generationProgress.stage || '准备中...'}
                      </span>
                    </div>
                    <div className="w-full bg-blue-200 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${generationProgress.progress}%` }}
                      />
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* 底部按钮 */}
        <div className="px-6 py-4 bg-gray-50 flex justify-between">
          <button
            onClick={() => setStep(Math.max(1, step - 1))}
            disabled={step === 1}
            className="px-6 py-2 text-gray-600 hover:text-gray-800 disabled:opacity-50"
          >
            上一步
          </button>
          
          {step < 3 ? (
            <button
              onClick={() => setStep(step + 1)}
              className="px-6 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600"
            >
              下一步
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={isGenerating || !formData.theme}
              className="px-8 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:opacity-90 disabled:opacity-50 flex items-center gap-2"
            >
              {isGenerating ? (
                <>
                  <span className="animate-spin">⏳</span>
                  生成中...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  开始创作
                </>
              )}
            </button>
          )}
        </div>
      </motion.div>
    </div>
  );
};
