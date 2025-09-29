import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from '../Button'

describe('Button Component', () => {
  it('renders with default props', () => {
    render(<Button>Click me</Button>)
    const button = screen.getByRole('button', { name: /click me/i })
    expect(button).toBeInTheDocument()
  })

  it('renders with different variants', () => {
    const { rerender } = render(<Button variant="outline">Outline Button</Button>)
    expect(screen.getByRole('button')).toHaveClass('border')

    rerender(<Button variant="secondary">Secondary Button</Button>)
    expect(screen.getByRole('button')).toHaveClass('bg-gray-100')

    rerender(<Button variant="destructive">Destructive Button</Button>)
    expect(screen.getByRole('button')).toHaveClass('bg-red-600')
  })

  it('renders with different sizes', () => {
    const { rerender } = render(<Button size="sm">Small Button</Button>)
    expect(screen.getByRole('button')).toHaveClass('h-9')

    rerender(<Button size="lg">Large Button</Button>)
    expect(screen.getByRole('button')).toHaveClass('h-11')

    rerender(<Button size="icon">Icon Button</Button>)
    expect(screen.getByRole('button')).toHaveClass('h-10', 'w-10')
  })

  it('handles click events', () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>Clickable Button</Button>)

    fireEvent.click(screen.getByRole('button'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('shows loading state', () => {
    render(<Button loading>Loading Button</Button>)
    const button = screen.getByRole('button')

    expect(button).toBeDisabled()
    expect(button.querySelector('svg')).toBeInTheDocument() // Loading spinner
  })

  it('renders with icon', () => {
    const icon = <span data-testid="test-icon">📍</span>
    render(<Button icon={icon}>Button with Icon</Button>)

    expect(screen.getByTestId('test-icon')).toBeInTheDocument()
  })

  it('renders with icon on the right', () => {
    const icon = <span data-testid="test-icon">→</span>
    render(<Button icon={icon} iconPosition="right">Button with Right Icon</Button>)

    const button = screen.getByRole('button')
    const iconElement = screen.getByTestId('test-icon')

    expect(iconElement).toBeInTheDocument()
    expect(button.innerHTML.includes('→')).toBe(true)
  })

  it('is disabled when loading', () => {
    const handleClick = vi.fn()
    render(<Button loading onClick={handleClick}>Loading Button</Button>)

    const button = screen.getByRole('button')
    expect(button).toBeDisabled()

    fireEvent.click(button)
    expect(handleClick).not.toHaveBeenCalled()
  })

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled Button</Button>)

    const button = screen.getByRole('button')
    expect(button).toBeDisabled()
  })
})