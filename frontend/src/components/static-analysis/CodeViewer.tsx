import { useEffect, useRef } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { cn } from '@/lib/utils'
import type { FileContent } from '@/lib/api'

interface CodeViewerProps {
  fileContent?: FileContent
  issues?: Array<{
    line_number: number
    severity: string
    description: string
    type: string
  }>
  onLineClick?: (lineNumber: number) => void
  className?: string
}

export function CodeViewer({ fileContent, issues = [], onLineClick, className }: CodeViewerProps) {
  const codeRef = useRef<HTMLDivElement>(null)

  // 根据文件路径确定语言
  const getLanguage = (path: string): string => {
    const ext = path.split('.').pop()?.toLowerCase()
    const langMap: Record<string, string> = {
      'py': 'python',
      'js': 'javascript',
      'ts': 'typescript',
      'jsx': 'javascript',
      'tsx': 'typescript',
      'cpp': 'cpp',
      'c': 'c',
      'h': 'c',
      'hpp': 'cpp',
      'java': 'java',
      'go': 'go',
      'rs': 'rust',
      'php': 'php',
      'rb': 'ruby',
      'swift': 'swift',
      'kt': 'kotlin',
      'cs': 'csharp',
      'sh': 'bash',
      'sql': 'sql',
      'html': 'html',
      'css': 'css',
      'json': 'json',
      'xml': 'xml',
      'yaml': 'yaml',
      'yml': 'yaml',
    }
    return langMap[ext || ''] || 'text'
  }

  // 创建行号到问题的映射
  const issuesByLine = new Map<number, typeof issues>()
  issues.forEach(issue => {
    const line = issue.line_number
    if (!issuesByLine.has(line)) {
      issuesByLine.set(line, [])
    }
    issuesByLine.get(line)!.push(issue)
  })

  // 滚动到指定行
  useEffect(() => {
    if (codeRef.current && issues.length > 0) {
      const firstIssue = issues[0]
      const lineElement = codeRef.current.querySelector(`[data-line-number="${firstIssue.line_number}"]`)
      if (lineElement) {
        lineElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }
  }, [issues])

  if (!fileContent) {
    return (
      <div className={cn("h-full flex items-center justify-center bg-gray-50", className)}>
        <p className="text-gray-500">请选择一个文件查看代码</p>
      </div>
    )
  }

  const language = getLanguage(fileContent.path)
  const lines = fileContent.lines || fileContent.content.split('\n')

  return (
    <div className={cn("h-full overflow-auto bg-gray-50", className)}>
      <div className="sticky top-0 bg-white border-b border-gray-200 px-4 py-2 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-gray-700">{fileContent.path}</h3>
          <p className="text-xs text-gray-500">
            编码: {fileContent.encoding}
            {fileContent.detected_encoding && fileContent.detected_encoding !== fileContent.encoding && (
              <span> (检测到: {fileContent.detected_encoding})</span>
            )}
          </p>
        </div>
        <div className="text-xs text-gray-500">
          {lines.length} 行
        </div>
      </div>
      <div ref={codeRef} className="relative">
        <SyntaxHighlighter
          language={language}
          style={vscDarkPlus}
          customStyle={{
            margin: 0,
            padding: '1rem',
            background: '#1e1e1e',
            fontSize: '14px',
          }}
          lineNumberStyle={{
            minWidth: '3em',
            paddingRight: '1em',
            color: '#858585',
            userSelect: 'none',
          }}
          showLineNumbers
          lineProps={(lineNumber) => {
            const lineIssues = issuesByLine.get(lineNumber)
            const hasIssue = !!lineIssues
            const severity = lineIssues?.[0]?.severity || 'LOW'
            
            return {
              'data-line-number': lineNumber,
              onClick: () => onLineClick?.(lineNumber),
              style: {
                cursor: hasIssue ? 'pointer' : 'default',
                backgroundColor: hasIssue
                  ? severity === 'HIGH'
                    ? 'rgba(239, 68, 68, 0.2)'
                    : severity === 'MEDIUM'
                    ? 'rgba(251, 191, 36, 0.2)'
                    : 'rgba(59, 130, 246, 0.2)'
                  : 'transparent',
                display: 'block',
                paddingLeft: '0.5rem',
                marginLeft: '-0.5rem',
                marginRight: '-0.5rem',
              },
            }
          }}
        >
          {fileContent.content}
        </SyntaxHighlighter>
      </div>
    </div>
  )
}

