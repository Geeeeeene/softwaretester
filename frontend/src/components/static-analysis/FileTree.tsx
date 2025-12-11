import { useState } from 'react'
import { File, Folder, FolderOpen, ChevronRight, ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { FileTreeNode } from '@/lib/api'

interface FileTreeProps {
  tree: FileTreeNode[]
  selectedPath?: string
  onFileSelect: (path: string) => void
  className?: string
}

export function FileTree({ tree, selectedPath, onFileSelect, className }: FileTreeProps) {
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(new Set())

  const toggleExpand = (path: string) => {
    const newExpanded = new Set(expandedPaths)
    if (newExpanded.has(path)) {
      newExpanded.delete(path)
    } else {
      newExpanded.add(path)
    }
    setExpandedPaths(newExpanded)
  }

  const renderNode = (node: FileTreeNode, level: number = 0) => {
    const isExpanded = expandedPaths.has(node.path)
    const isSelected = selectedPath === node.path
    const isDirectory = node.type === 'directory'

    return (
      <div key={node.path}>
        <div
          className={cn(
            "flex items-center py-1 px-2 cursor-pointer hover:bg-gray-100 rounded",
            isSelected && "bg-blue-100 hover:bg-blue-200",
            className
          )}
          style={{ paddingLeft: `${level * 16 + 8}px` }}
          onClick={() => {
            if (isDirectory) {
              toggleExpand(node.path)
            } else {
              onFileSelect(node.path)
            }
          }}
        >
          {isDirectory ? (
            <>
              {isExpanded ? (
                <ChevronDown className="h-4 w-4 mr-1 text-gray-500" />
              ) : (
                <ChevronRight className="h-4 w-4 mr-1 text-gray-500" />
              )}
              {isExpanded ? (
                <FolderOpen className="h-4 w-4 mr-2 text-blue-500" />
              ) : (
                <Folder className="h-4 w-4 mr-2 text-blue-500" />
              )}
            </>
          ) : (
            <>
              <div className="w-5 mr-1" /> {/* 占位符，保持对齐 */}
              <File className="h-4 w-4 mr-2 text-gray-500" />
            </>
          )}
          <span className="text-sm flex-1 truncate">{node.name}</span>
          {!isDirectory && node.size && (
            <span className="text-xs text-gray-400 ml-2">
              {(node.size / 1024).toFixed(1)}KB
            </span>
          )}
        </div>
        {isDirectory && isExpanded && node.children && (
          <div>
            {node.children.map((child) => renderNode(child, level + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto border-r border-gray-200 bg-white">
      <div className="p-2">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">文件树</h3>
        {tree.length === 0 ? (
          <p className="text-sm text-gray-500">暂无文件</p>
        ) : (
          <div>
            {tree.map((node) => renderNode(node))}
          </div>
        )}
      </div>
    </div>
  )
}

