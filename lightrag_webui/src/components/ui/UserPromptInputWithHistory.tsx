import React, { useState, useRef, useEffect, useCallback } from 'react'
import { ChevronDown, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import Input from './Input'

interface UserPromptInputWithHistoryProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  className?: string
  id?: string
  history: string[]
  onSelectFromHistory: (prompt: string) => void
  onDeleteFromHistory?: (index: number) => void
}

export default function UserPromptInputWithHistory({
  value,
  onChange,
  placeholder,
  className,
  id,
  history,
  onSelectFromHistory,
  onDeleteFromHistory
}: UserPromptInputWithHistoryProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const [isHovered, setIsHovered] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        setSelectedIndex(-1)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  // Handle keyboard navigation
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (!isOpen) {
        if (e.key === 'ArrowDown' && history.length > 0) {
          e.preventDefault()
          setIsOpen(true)
          setSelectedIndex(0)
        }
        return
      }

      switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex((prev) => (prev < history.length - 1 ? prev + 1 : prev))
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1))
        if (selectedIndex === 0) {
          setSelectedIndex(-1)
        }
        break
      case 'Enter':
        if (selectedIndex >= 0 && selectedIndex < history.length) {
          e.preventDefault()
          const selectedPrompt = history[selectedIndex]
          onSelectFromHistory(selectedPrompt)
          setIsOpen(false)
          setSelectedIndex(-1)
        }
        break
      case 'Escape':
        e.preventDefault()
        setIsOpen(false)
        setSelectedIndex(-1)
        break
      }
    },
    [isOpen, selectedIndex, history, onSelectFromHistory]
  )

  const handleInputClick = () => {
    if (history.length > 0) {
      setIsOpen(!isOpen)
      setSelectedIndex(-1)
    }
  }

  const handleDropdownItemClick = (prompt: string) => {
    onSelectFromHistory(prompt)
    setIsOpen(false)
    setSelectedIndex(-1)
    inputRef.current?.focus()
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value)
  }

  const handleMouseEnter = () => {
    setIsHovered(true)
  }

  const handleMouseLeave = () => {
    setIsHovered(false)
  }

  // Handle delete history item with boundary cases
  const handleDeleteHistoryItem = useCallback(
    (index: number, e: React.MouseEvent) => {
      e.stopPropagation() // Prevent triggering item selection
      onDeleteFromHistory?.(index)

      // Handle boundary cases
      if (history.length === 1) {
        // Deleting the last item, close dropdown
        setIsOpen(false)
        setSelectedIndex(-1)
      } else if (selectedIndex === index) {
        // Deleting currently selected item, adjust selection
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1))
      } else if (selectedIndex > index) {
        // Deleting item before selected item, adjust index
        setSelectedIndex((prev) => prev - 1)
      }
    },
    [onDeleteFromHistory, history.length, selectedIndex]
  )

  return (
    <div
      className="relative"
      ref={dropdownRef}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <div className="relative">
        <Input
          ref={inputRef}
          id={id}
          value={value}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onClick={handleInputClick}
          placeholder={placeholder}
          autoComplete="off"
          className={cn(isHovered && history.length > 0 ? 'pr-5' : 'pr-2', 'w-full', className)}
        />
        {isHovered && history.length > 0 && (
          <button
            type="button"
            onClick={handleInputClick}
            className="absolute top-1/2 right-2 -translate-y-1/2 rounded p-0 transition-colors hover:bg-gray-100 dark:hover:bg-gray-800"
            tabIndex={-1}
          >
            <ChevronDown
              className={cn(
                'h-3 w-3 text-gray-500 transition-transform duration-200',
                isOpen && 'rotate-180'
              )}
            />
          </button>
        )}
      </div>

      {/* Dropdown */}
      {isOpen && history.length > 0 && (
        <div className="absolute top-full right-0 left-0 z-50 mt-0.5 max-h-96 min-w-0 overflow-auto rounded-md border border-gray-300 bg-gray-100 shadow-lg dark:border-gray-700 dark:bg-gray-900">
          {history.map((prompt, index) => (
            <div
              key={index}
              className={cn(
                'flex items-center justify-between py-2 pr-1 pl-3 text-sm transition-colors hover:bg-gray-200 dark:hover:bg-gray-700',
                'border-b border-gray-100 last:border-b-0 dark:border-gray-700',
                'focus-within:bg-gray-100 dark:focus-within:bg-gray-700',
                selectedIndex === index && 'bg-gray-100 dark:bg-gray-700'
              )}
            >
              <button
                type="button"
                onClick={() => handleDropdownItemClick(prompt)}
                className="mr-0 flex-1 truncate text-left focus:outline-none"
                title={prompt}
              >
                {prompt}
              </button>
              {onDeleteFromHistory && (
                <button
                  type="button"
                  onClick={(e) => handleDeleteHistoryItem(index, e)}
                  className="ml-auto flex-shrink-0 rounded p-0 transition-colors hover:bg-red-100 focus:outline-none dark:hover:bg-red-900"
                  title="Delete this history item"
                >
                  <X className="h-3 w-3 text-gray-400 hover:text-red-500" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
