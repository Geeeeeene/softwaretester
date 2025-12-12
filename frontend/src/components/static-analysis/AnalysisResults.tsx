import { useState } from 'react'
import { AlertCircle, CheckCircle2, AlertTriangle, Info, XCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { StaticAnalysisResult } from '@/lib/api'

interface AnalysisResultsProps {
  results?: StaticAnalysisResult
  onIssueClick?: (filePath: string, lineNumber: number) => void
  className?: string
}

export function AnalysisResults({ results, onIssueClick, className }: AnalysisResultsProps) {
  const [severityFilter, setSeverityFilter] = useState<'ALL' | 'HIGH' | 'MEDIUM' | 'LOW'>('ALL')

  if (!results || !results.results) {
    return (
      <div className={cn("h-full flex items-center justify-center bg-gray-50", className)}>
        <p className="text-gray-500">暂无分析结果</p>
      </div>
    )
  }

  const analysisData = results.results
  const summary = analysisData.summary || {}
  const severityCount = summary.severity_count || { HIGH: 0, MEDIUM: 0, LOW: 0 }

  // 收集所有问题
  const allIssues: Array<{
    file: string
    line: number
    severity: string
    type: string
    description: string
    tool?: string
  }> = []

  Object.entries(analysisData.file_results || {}).forEach(([filePath, fileResult]: [string, any]) => {
    const issues = fileResult.issues || []
    issues.forEach((issue: any) => {
      // 后端返回的字段是"line"不是"line_number"，支持两种格式
      const lineNumber = issue.line !== undefined ? issue.line : (issue.line_number !== undefined ? issue.line_number : null)
      allIssues.push({
        file: filePath,
        line: lineNumber,  // 保留null，不要转换为0
        severity: issue.severity || 'MEDIUM',
        type: issue.type || issue.id || 'unknown',
        description: issue.message || issue.description || '',
        tool: issue.tool,
      })
    })
  })

  // 过滤问题
  const filteredIssues = severityFilter === 'ALL'
    ? allIssues
    : allIssues.filter(issue => issue.severity === severityFilter)

  // 按严重程度排序
  const severityOrder = { HIGH: 0, MEDIUM: 1, LOW: 2 }
  filteredIssues.sort((a, b) => {
    const orderA = severityOrder[a.severity as keyof typeof severityOrder] ?? 3
    const orderB = severityOrder[b.severity as keyof typeof severityOrder] ?? 3
    if (orderA !== orderB) return orderA - orderB
    // 处理null行号：null排在最后
    if (a.line === null || a.line === undefined) return 1
    if (b.line === null || b.line === undefined) return -1
    return a.line - b.line
  })

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'HIGH':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'MEDIUM':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      case 'LOW':
        return <Info className="h-4 w-4 text-blue-500" />
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'HIGH':
        return 'border-red-200 bg-red-50'
      case 'MEDIUM':
        return 'border-yellow-200 bg-yellow-50'
      case 'LOW':
        return 'border-blue-200 bg-blue-50'
      default:
        return 'border-gray-200 bg-gray-50'
    }
  }

  return (
    <div className={cn("h-full flex flex-col bg-white border-l border-gray-200", className)}>
      {/* 头部统计 */}
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">分析结果</h3>
        <div className="grid grid-cols-3 gap-2 mb-3">
          <div className="text-center p-2 bg-red-50 rounded">
            <div className="text-lg font-bold text-red-600">{severityCount.HIGH || 0}</div>
            <div className="text-xs text-red-600">高</div>
          </div>
          <div className="text-center p-2 bg-yellow-50 rounded">
            <div className="text-lg font-bold text-yellow-600">{severityCount.MEDIUM || 0}</div>
            <div className="text-xs text-yellow-600">中</div>
          </div>
          <div className="text-center p-2 bg-blue-50 rounded">
            <div className="text-lg font-bold text-blue-600">{severityCount.LOW || 0}</div>
            <div className="text-xs text-blue-600">低</div>
          </div>
        </div>
        <div className="flex gap-2">
          {(['ALL', 'HIGH', 'MEDIUM', 'LOW'] as const).map(severity => (
            <button
              key={severity}
              onClick={() => setSeverityFilter(severity)}
              className={cn(
                "px-2 py-1 text-xs rounded",
                severityFilter === severity
                  ? "bg-blue-500 text-white"
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              )}
            >
              {severity === 'ALL' ? '全部' : severity === 'HIGH' ? '高' : severity === 'MEDIUM' ? '中' : '低'}
            </button>
          ))}
        </div>
      </div>

      {/* 问题列表 */}
      <div className="flex-1 overflow-y-auto p-2">
        {filteredIssues.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <CheckCircle2 className="h-12 w-12 mx-auto text-green-500 mb-2" />
            <p>没有发现{severityFilter !== 'ALL' ? severityFilter : ''}级别的问题</p>
          </div>
        ) : (
          <div className="space-y-2">
            {filteredIssues.map((issue, index) => (
              <div
                key={`${issue.file}-${issue.line}-${index}`}
                className={cn(
                  "p-3 rounded border cursor-pointer hover:shadow-md transition-shadow",
                  getSeverityColor(issue.severity)
                )}
                onClick={() => {
                  if (issue.line !== null && issue.line !== undefined) {
                    onIssueClick?.(issue.file, issue.line)
                  } else {
                    // 文件级别问题，只跳转到文件，不跳转到具体行
                    onIssueClick?.(issue.file, 1)  // 跳转到第1行
                  }
                }}
              >
                <div className="flex items-start gap-2">
                  {getSeverityIcon(issue.severity)}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-semibold text-gray-700">
                        {issue.severity}
                      </span>
                      {issue.tool && (
                        <span className="text-xs text-gray-500 bg-gray-200 px-1.5 py-0.5 rounded">
                          {issue.tool}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-800 mb-1">{issue.description}</p>
                    <div className="text-xs text-gray-600">
                      <span className="font-mono">{issue.file}</span>
                      {issue.line !== null && issue.line !== undefined ? (
                        <>
                          <span className="mx-1">:</span>
                          <span className="font-semibold">行 {issue.line}</span>
                        </>
                      ) : (
                        <span className="mx-1 text-gray-500">(文件级别问题)</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 大模型分析结果 */}
      {analysisData.file_results && Object.values(analysisData.file_results).some((fr: any) => fr.llm_analysis) && (
        <div className="p-4 border-t border-gray-200 bg-blue-50">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">🤖 大模型深度分析</h4>
          <div className="text-xs text-gray-700 whitespace-pre-wrap max-h-32 overflow-y-auto">
            {Object.values(analysisData.file_results).find((fr: any) => fr.llm_analysis)?.llm_analysis?.analysis || '暂无分析结果'}
          </div>
        </div>
      )}
    </div>
  )
}

