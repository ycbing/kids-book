# backend/app/services/ai_service.py
import openai
from typing import List, Optional
import json
import asyncio
import logging
from app.config import settings
from app.models.schemas import (
    StoryGenerateRequest, StoryResponse, StoryPage,
    ImageGenerateRequest, ImageResponse, ArtStyle, AgeGroup
)
from app.services.retry_helper import retry_on_failure, handle_api_error, APICallError

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        # 配置超时时间
        self.timeout = settings.API_TIMEOUT

        # 获取文本和图像的配置
        text_api_key, text_base_url, text_model = settings.get_text_config()
        image_api_key, image_base_url, image_model = settings.get_image_config()

        # 创建文本生成客户端
        self.text_client = openai.AsyncOpenAI(
            api_key=text_api_key,
            base_url=text_base_url,
            timeout=self.timeout
        )

        # 创建图像生成客户端
        self.image_client = openai.AsyncOpenAI(
            api_key=image_api_key,
            base_url=image_base_url,
            timeout=self.timeout
        )

        logger.info(f"AI服务初始化完成")
        logger.info(f"文本API地址: {text_base_url}")
        logger.info(f"文本模型: {text_model}")
        logger.info(f"图像API地址: {image_base_url}")
        logger.info(f"图像模型: {image_model}")
        logger.info(f"超时设置: {self.timeout}秒")
        logger.info(f"最大重试: {settings.API_MAX_RETRIES}次")
    
    def _get_age_appropriate_guidelines(self, age_group: AgeGroup) -> str:
        """根据年龄段获取写作指南"""
        guidelines = {
            AgeGroup.TODDLER: """
                - 使用简单的词汇和短句
                - 每页不超过2-3句话
                - 重复性的语言模式
                - 熟悉的日常场景
                - 明亮、简单的视觉元素
            """,
            AgeGroup.PRESCHOOL: """
                - 简单但有趣的情节
                - 每页3-5句话
                - 引入简单的情感和道德概念
                - 可爱的动物或儿童角色
                - 色彩丰富的场景
            """,
            AgeGroup.EARLY_ELEMENTARY: """
                - 更复杂的故事情节
                - 每页5-8句话
                - 可以包含简单的冲突和解决
                - 更多样化的角色
                - 详细的背景描绘
            """,
            AgeGroup.ELEMENTARY: """
                - 完整的故事结构
                - 每页可以更长
                - 复杂的情感和主题
                - 多样化的角色关系
                - 丰富的世界观设定
            """
        }
        return guidelines.get(age_group, guidelines[AgeGroup.PRESCHOOL])
    
    def _get_style_prompt(self, style: ArtStyle) -> str:
        """获取艺术风格的提示词"""
        style_prompts = {
            ArtStyle.WATERCOLOR: "watercolor illustration style, soft colors, gentle brush strokes, dreamy atmosphere",
            ArtStyle.CARTOON: "cartoon style, bold outlines, vibrant colors, expressive characters",
            ArtStyle.REALISTIC: "realistic illustration, detailed textures, natural lighting, lifelike characters",
            ArtStyle.FLAT: "flat design illustration, minimal shadows, geometric shapes, modern aesthetic",
            ArtStyle.HAND_DRAWN: "hand-drawn sketch style, pencil textures, warm and cozy feeling",
            ArtStyle.ANIME: "anime style illustration, big expressive eyes, dynamic poses, Japanese animation aesthetic",
            ArtStyle.PAPER_CUT: "paper cut art style, layered paper effect, traditional Chinese aesthetic",
            ArtStyle.OIL_PAINTING: "oil painting style, rich textures, classical art feeling, warm color palette"
        }
        return style_prompts.get(style, style_prompts[ArtStyle.WATERCOLOR])
    
    @retry_on_failure(
        max_retries=3,
        delay=2,
        backoff_factor=2.0,
        exceptions=(openai.APIError, openai.APITimeoutError, openai.APIConnectionError, Exception)
    )
    async def generate_story(self, request: StoryGenerateRequest) -> StoryResponse:
        """生成完整的绘本故事（带自动重试）"""

        logger.info("="*60)
        logger.info(f"🎨 开始生成故事")
        logger.info(f"主题: {request.theme}")
        logger.info(f"关键词: {request.keywords}")
        logger.info(f"年龄段: {request.target_age.value}")
        logger.info(f"页数: {request.page_count}")
        logger.info("="*60)

        age_guidelines = self._get_age_appropriate_guidelines(request.target_age)
        keywords_str = "、".join(request.keywords) if request.keywords else "无特定关键词"
        
        system_prompt = f"""你是一位专业的儿童绘本作家，擅长创作温馨、有教育意义的故事。
        
请根据以下要求创作一个绘本故事：

目标年龄段：{request.target_age.value}
写作指南：{age_guidelines}

请确保：
1. 故事有清晰的开头、发展和结尾
2. 语言适合目标年龄段
3. 包含积极正面的价值观
4. 每一页都有生动的场景描述，便于配图

输出格式要求（JSON）：
{{
    "title": "故事标题",
    "description": "故事简介（50字以内）",
    "pages": [
        {{
            "page_number": 1,
            "text": "这一页的故事文字",
            "scene_description": "场景描述（用于理解画面）",
            "image_prompt": "英文图像生成提示词，详细描述画面内容、角色、场景、氛围"
        }}
    ]
}}

重要提示：
- 必须严格按照上面的JSON格式输出
- 字段名必须使用下划线，如 image_prompt（不要使用 image.prompt）
- image_prompt 必须是英文
- scene_description 和 text 可以使用中文"""

        user_prompt = f"""请创作一个关于"{request.theme}"的绘本故事。

关键词：{keywords_str}
页数要求：{request.page_count}页
{"额外要求：" + request.custom_prompt if request.custom_prompt else ""}

请直接输出JSON格式的故事内容。"""

        try:
            _, _, model = settings.get_text_config()

            logger.info(f"📤 向AI发送请求...")
            logger.info(f"模型: {model}")
            logger.info(f"超时设置: {self.timeout}秒")

            response = await self.text_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,
                timeout=self.timeout
            )

            content = response.choices[0].message.content
            logger.info(f"📥 收到AI响应 (长度: {len(content)} 字符)")
            logger.info(f"原始响应前500字符:\n{content[:500]}...")

            # 尝试解析 JSON，处理可能的格式问题
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                # 如果直接解析失败，尝试修复常见问题
                import re

                # 尝试提取 JSON 部分
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if not json_match:
                    raise Exception(f"无法从响应中提取有效的 JSON: {content[:1000]}...")

                json_str = json_match.group()

                # 修复常见的 JSON 格式问题
                # 1. 移除对象和数组中的尾部逗号
                json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
                # 2. 修复未闭合的字符串（截断响应）
                json_str = re.sub(r',\s*$', '', json_str)
                # 3. 移除注释（如果存在）
                json_str = re.sub(r'//.*?\n', '', json_str)
                json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)

                try:
                    result = json.loads(json_str)
                except json.JSONDecodeError as parse_error:
                    # 如果还是失败，提供更详细的错误信息
                    error_line = content.split('\n')[min(e.lineno-1, len(content.split('\n'))-1)] if hasattr(e, 'lineno') else ""
                    raise Exception(
                        f"JSON 解析失败: {str(parse_error)}\n"
                        f"错误行: {error_line[:200] if error_line else 'N/A'}\n"
                        f"修复后的JSON: {json_str[:500]}..."
                    )

            # 验证返回的数据结构
            if "pages" not in result:
                raise Exception(f"AI 返回的数据缺少 'pages' 字段: {result}")

            pages = []
            for i, p in enumerate(result["pages"]):
                # 确保必需字段存在，否则使用默认值
                page_number = p.get("page_number", i + 1)
                text = p.get("text", "")
                scene_description = p.get("scene_description", p.get("description", ""))

                # 处理多种可能的字段名
                image_prompt = p.get("image_prompt") or p.get("image.prompt") or p.get("image_description") or scene_description

                pages.append(StoryPage(
                    page_number=page_number,
                    text=text,
                    scene_description=scene_description,
                    image_prompt=image_prompt
                ))

            logger.info(f"✅ 故事生成成功!")
            logger.info(f"标题: {result['title']}")
            logger.info(f"描述: {result['description']}")
            logger.info(f"页数: {len(pages)}")
            logger.info("="*60 + "\n")

            return StoryResponse(
                title=result["title"],
                description=result["description"],
                pages=pages
            )
            
        except openai.APITimeoutError as e:
            logger.error(f"❌ API请求超时!")
            logger.error(f"超时时间: {self.timeout}秒")
            logger.error(f"建议: 增加API_TIMEOUT配置或检查网络连接")
            raise APICallError(
                f"API请求超时（{self.timeout}秒），请稍后重试",
                status_code=None,
                response_text=str(e)
            )
        except openai.APIConnectionError as e:
            logger.error(f"❌ API连接失败!")
            logger.error(f"错误信息: {str(e)}")
            logger.error(f"建议: 检查网络连接和API地址是否正确")
            raise APICallError(
                "无法连接到API服务器，请检查网络连接",
                status_code=None,
                response_text=str(e)
            )
        except openai.AuthenticationError as e:
            logger.error(f"❌ API认证失败!")
            logger.error(f"建议: 检查API密钥是否正确")
            raise APICallError(
                "API密钥无效，请检查配置",
                status_code=401,
                response_text=str(e)
            )
        except openai.RateLimitError as e:
            logger.error(f"❌ API速率限制!")
            logger.error(f"建议: 稍后再试或升级API套餐")
            raise APICallError(
                handle_api_error(str(e)),
                status_code=429,
                response_text=str(e)
            )
        except openai.APIStatusError as e:
            logger.error(f"❌ API服务错误!")
            logger.error(f"状态码: {e.status_code}")
            logger.error(f"响应: {e.response.text if hasattr(e, 'response') else str(e)}")
            raise APICallError(
                handle_api_error(str(e)),
                status_code=e.status_code,
                response_text=e.response.text if hasattr(e, 'response') else str(e)
            )
        except Exception as e:
            logger.error(f"❌ 故事生成失败!")
            logger.error(f"错误信息: {str(e)}")
            logger.error(f"错误类型: {type(e).__name__}")
            logger.error("="*60 + "\n")
            raise APICallError(
                f"故事生成失败: {str(e)}",
                status_code=None,
                response_text=str(e)
            )
    
    @retry_on_failure(
        max_retries=3,
        delay=2,
        backoff_factor=2.0,
        exceptions=(openai.APIError, openai.APITimeoutError, openai.APIConnectionError, Exception)
    )
    async def generate_image(self, request: ImageGenerateRequest) -> ImageResponse:
        """生成单张配图（带自动重试）"""

        logger.info("="*60)
        logger.info(f"🎨 开始生成图像")
        logger.info(f"提示词: {request.prompt[:100]}...")
        logger.info(f"风格: {request.style.value}")
        logger.info("="*60)

        style_prompt = self._get_style_prompt(request.style)

        full_prompt = f"""Children's picture book illustration, {style_prompt}.

Scene: {request.prompt}

Requirements:
- Safe for children, no scary or inappropriate content
- Bright and appealing colors
- Clear focal point
- Suitable for picture book format
- High quality, detailed illustration"""

        try:
            _, _, model = settings.get_image_config()

            logger.info(f"📤 向AI发送图像生成请求...")
            logger.info(f"模型: {model}")
            logger.info(f"尺寸: {settings.IMAGE_SIZE}")

            response = await self.image_client.images.generate(
                model=model,
                prompt=full_prompt,
                size=settings.IMAGE_SIZE,
                quality="hd",
                n=1,
                timeout=self.timeout
            )

            logger.info(f"✅ 图像生成成功!")
            logger.info(f"图像URL: {response.data[0].url}")
            logger.info("="*60 + "\n")

            return ImageResponse(
                image_url=response.data[0].url,
                revised_prompt=response.data[0].revised_prompt
            )

        except openai.APITimeoutError as e:
            logger.error(f"❌ 图像生成超时!")
            raise APICallError(
                f"图像生成超时（{self.timeout}秒），请稍后重试",
                status_code=None,
                response_text=str(e)
            )
        except openai.APIConnectionError as e:
            logger.error(f"❌ API连接失败!")
            raise APICallError(
                "无法连接到API服务器",
                status_code=None,
                response_text=str(e)
            )
        except openai.RateLimitError as e:
            logger.error(f"❌ API速率限制!")
            raise APICallError(
                handle_api_error(str(e)),
                status_code=429,
                response_text=str(e)
            )
        except Exception as e:
            logger.error(f"❌ 图像生成失败!")
            logger.error(f"错误信息: {str(e)}")
            logger.error("="*60 + "\n")
            raise APICallError(
                f"图像生成失败: {str(e)}",
                status_code=None,
                response_text=str(e)
            )
    
    async def generate_book_images(
        self, 
        pages: List[StoryPage], 
        style: ArtStyle,
        progress_callback=None
    ) -> List[str]:
        """批量生成绘本配图"""
        
        image_urls = []
        total = len(pages)
        
        for i, page in enumerate(pages):
            try:
                request = ImageGenerateRequest(
                    prompt=page.image_prompt,
                    style=style
                )
                result = await self.generate_image(request)
                image_urls.append(result.image_url)
                
                if progress_callback:
                    await progress_callback(i + 1, total)
                    
                # 避免API限流
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"页面 {page.page_number} 图像生成失败: {e}")
                image_urls.append(None)
        
        return image_urls

# 创建服务实例
ai_service = AIService()
