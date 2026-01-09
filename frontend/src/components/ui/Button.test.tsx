// frontend/src/components/ui/Button.test.tsx
/**
 * Button组件测试
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from './Button';

describe('Button组件', () => {
  describe('基础渲染', () => {
    it('应该正确渲染按钮文本', () => {
      render(<Button>点击我</Button>);
      expect(screen.getByRole('button')).toHaveTextContent('点击我');
    });

    it('应该有正确的默认类名', () => {
      render(<Button>测试</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('btn');
    });

    it('应该支持自定义className', () => {
      render(<Button className="custom-class">测试</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('custom-class');
    });
  });

  describe('变体', () => {
    it('应该渲染primary变体', () => {
      render(<Button variant="primary">Primary</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('btn-primary');
    });

    it('应该渲染secondary变体', () => {
      render(<Button variant="secondary">Secondary</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('btn-secondary');
    });

    it('应该渲染danger变体', () => {
      render(<Button variant="danger">Delete</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('btn-danger');
    });

    it('应该渲染ghost变体', () => {
      render(<Button variant="ghost">Ghost</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('btn-ghost');
    });

    it('应该渲染link变体', () => {
      render(<Button variant="link">Link</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('btn-link');
    });
  });

  describe('尺寸', () => {
    it('应该渲染small尺寸', () => {
      render(<Button size="small">Small</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('btn-small');
    });

    it('应该渲染medium尺寸（默认）', () => {
      render(<Button size="medium">Medium</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('btn-medium');
    });

    it('应该渲染large尺寸', () => {
      render(<Button size="large">Large</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('btn-large');
    });
  });

  describe('加载状态', () => {
    it('在加载时应该显示loading指示器', () => {
      render(<Button loading>Loading</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('loading');
      expect(button).toBeDisabled();
    });

    it('在加载时不应该触发onClick', async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();

      render(
        <Button loading onClick={handleClick}>
          Click Me
        </Button>
      );

      await user.click(screen.getByRole('button'));
      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  describe('禁用状态', () => {
    it('禁用时应该disabled属性', () => {
      render(<Button disabled>Disabled</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });

    it('禁用时不应该触发onClick', async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();

      render(
        <Button disabled onClick={handleClick}>
          Disabled
        </Button>
      );

      await user.click(screen.getByRole('button'));
      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  describe('点击事件', () => {
    it('应该正确触发onClick', async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();

      render(
        <Button onClick={handleClick}>Click Me</Button>
      );

      await user.click(screen.getByRole('button'));
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('应该传递事件对象', async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();

      render(
        <Button onClick={handleClick}>Click Me</Button>
      );

      await user.click(screen.getByRole('button'));
      expect(handleClick).toHaveBeenCalledWith(
        expect.any(MouseEvent)
      );
    });
  });

  describe('全宽', () => {
    it('fullWidth为true时应该有全宽类', () => {
      render(<Button fullWidth>Full Width</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('btn-full-width');
    });
  });

  describe('图标', () => {
    it('应该渲染图标', () => {
      render(
        <Button icon={<span data-testid="icon">★</span>}>
          With Icon
        </Button>
      );

      expect(screen.getByTestId('icon')).toBeInTheDocument();
    });

    it('应该正确放置图标位置', () => {
      const { container } = render(
        <Button icon={<span data-testid="icon">★</span>}>
          Button
        </Button>
      );

      const button = container.querySelector('.btn');
      const icon = screen.getByTestId('icon');

      expect(button?.firstChild).toBe(icon);
    });
  });

  describe('可访问性', () => {
    it('应该支持通过props传递aria属性', () => {
      render(
        <Button aria-label="Close dialog">×</Button>
      );

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-label', 'Close dialog');
    });

    it('应该支持disabled时的aria属性', () => {
      render(
        <Button disabled aria-describedby="help-text">
          Disabled Button
        </Button>
      );

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-describedby', 'help-text');
      expect(button).toHaveAttribute('aria-disabled', 'true');
    });
  });

  describe('HTML属性传递', () => {
    it('应该传递type属性', () => {
      render(<Button type="submit">Submit</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('type', 'submit');
    });

    it('应该传递自定义data属性', () => {
      render(<Button data-testid="custom-button">Test</Button>);
      expect(screen.getByTestId('custom-button')).toBeInTheDocument();
    });

    it('应该传递form属性', () => {
      render(<Button form="my-form">Submit</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('form', 'my-form');
    });
  });
});
