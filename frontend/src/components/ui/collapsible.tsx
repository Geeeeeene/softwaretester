import * as React from "react"
import { ChevronDown, ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"

interface CollapsibleProps {
  title: string | React.ReactNode
  defaultOpen?: boolean
  children: React.ReactNode
  className?: string
}

export function Collapsible({ title, defaultOpen = false, children, className }: CollapsibleProps) {
  const [isOpen, setIsOpen] = React.useState(defaultOpen)

  return (
    <div className={cn("border border-gray-200 rounded-lg", className)}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
      >
        <div className="font-medium text-gray-900 flex items-center gap-2">
          {typeof title === 'string' ? <span>{title}</span> : title}
        </div>
        {isOpen ? (
          <ChevronDown className="h-5 w-5 text-gray-500" />
        ) : (
          <ChevronRight className="h-5 w-5 text-gray-500" />
        )}
      </button>
      {isOpen && (
        <div className="border-t border-gray-200 p-4">
          {children}
        </div>
      )}
    </div>
  )
}

