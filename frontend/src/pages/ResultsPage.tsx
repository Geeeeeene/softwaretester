import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { executionsApi, type TestExecution } from '@/lib/api'
import type { AxiosResponse } from 'axios'
import { BarChart3, CheckCircle2, XCircle, AlertTriangle, TrendingUp, MemoryStick, FileText, Loader2 } from 'lucide-react'

interface CoverageData {
  percentage?: number
  lines_covered?: number
  lines_total?: number
  branches_covered?: number
  branches_total?: number
  functions_covered?: number
  functions_total?: number
}

interface MemoryIssue {
  id: string
  type: string
  severity: string
  message: string
  stack_trace?: Array<{
    frame: number
    function: string
    file: string
    line?: number
  }>
}

interface Artifact {
  type: string
  path: string
}

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>()
  const [selectedExecutionId, setSelectedExecutionId] = useState<number | null>(
    id ? parseInt(id, 10) : null
  )

  // 当 URL 参数变化时，更新选中的执行ID
  useEffect(() => {
    if (id) {
      const parsedId = parseInt(id, 10)
      if (!isNaN(parsedId)) {
        setSelectedExecutionId(parsedId)
      }
    } else {
      setSelectedExecutionId(null)
    }
  }, [id])

  // 获取执行列表（不依赖 selectedExecutionId）
  const { data: executions, isLoading: isLoadingExecutions, error: executionsError } = useQuery({
    queryKey: ['executions'],
    queryFn: () => executionsApi.list().then((res: AxiosResponse<TestExecution[]>) => res.data),
  })

  // 获取选中的执行详情
  const { data: execution, isLoading: isLoadingExecution, error: executionError } = useQuery({
    queryKey: ['execution', selectedExecutionId],
    queryFn: () => executionsApi.get(selectedExecutionId!).then((res: AxiosResponse<TestExecution>) => res.data),
    enabled: !!selectedExecutionId && !isNaN(selectedExecutionId),
  })

  // 解析覆盖率数据
  const coverageData: CoverageData | null = execution?.coverage_data 
    ? (execution.coverage_data as CoverageData)
    : null

  // 解析内存问题（从result中提取）
  const memoryIssues: MemoryIssue[] = execution?.result?.issues 
    ? (execution.result.issues as MemoryIssue[])
    : execution?.result && typeof execution.result === 'object' && 'issues' in execution.result
    ? (execution.result as any).issues || []
    : []

  // 计算覆盖率百分比
  const getCoveragePercentage = (covered: number = 0, total: number = 0) => {
    if (total === 0) return 0
    return Math.round((covered / total) * 100)
  }

  // 获取严重程度颜色
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'error':
        return 'text-red-600 bg-red-50'
      case 'warning':
        return 'text-yellow-600 bg-yellow-50'
      case 'info':
        return 'text-blue-600 bg-blue-50'
      default:
        return 'text-gray-600 bg-gray-50'
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">结果分析</h1>
        <p className="text-gray-600 mt-2">查看测试结果、覆盖率和内存调试信息</p>
      </div>

      {/* 错误提示 */}
      {executionsError && (
        <Card>
          <CardContent className="text-center py-12">
            <AlertTriangle className="h-12 w-12 mx-auto text-red-400 mb-4" />
            <p className="text-red-500">加载执行列表失败，请稍后重试</p>
          </CardContent>
        </Card>
      )}

      {/* 执行列表选择 */}
      {!executionsError && executions && executions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>执行记录</CardTitle>
            <CardDescription>选择要查看的执行记录</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {executions.map((exec: TestExecution) => (
                <div
                  key={exec.id}
                  onClick={() => setSelectedExecutionId(exec.id)}
                  className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                    selectedExecutionId === exec.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-medium">执行 #{exec.id}</p>
                      <p className="text-sm text-gray-500">
                        {exec.executor_type} • {new Date(exec.created_at).toLocaleString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {exec.status === 'passed' && (
                        <CheckCircle2 className="h-5 w-5 text-green-500" />
                      )}
                      {exec.status === 'failed' && (
                        <XCircle className="h-5 w-5 text-red-500" />
                      )}
                      {exec.status === 'error' && (
                        <AlertTriangle className="h-5 w-5 text-yellow-500" />
                      )}
                      <span className="text-sm font-medium capitalize">{exec.status}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 执行详情加载状态 */}
      {selectedExecutionId && isLoadingExecution && (
        <Card>
          <CardContent className="text-center py-12">
            <Loader2 className="h-12 w-12 mx-auto text-blue-400 mb-4 animate-spin" />
            <p className="text-gray-500">加载执行详情中...</p>
          </CardContent>
        </Card>
      )}

      {/* 执行详情错误 */}
      {selectedExecutionId && executionError && (
        <Card>
          <CardContent className="text-center py-12">
            <AlertTriangle className="h-12 w-12 mx-auto text-red-400 mb-4" />
            <p className="text-red-500">加载执行详情失败，请稍后重试</p>
          </CardContent>
        </Card>
      )}

      {/* 执行详情 */}
      {execution && !isLoadingExecution && (
        <>
          {/* 执行概览 */}
          <Card>
            <CardHeader>
              <CardTitle>执行概览</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-gray-500">状态</p>
                  <p className="text-lg font-semibold capitalize">{execution.status}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">通过数</p>
                  <p className="text-lg font-semibold text-green-600">{execution.passed_tests}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">失败数</p>
                  <p className="text-lg font-semibold text-red-600">{execution.failed_tests}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">耗时</p>
                  <p className="text-lg font-semibold">
                    {execution.duration_seconds?.toFixed(2) || '--'}s
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 代码覆盖率 */}
          {coverageData && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  代码覆盖率
                </CardTitle>
                <CardDescription>
                  由 gcov + lcov 生成的覆盖率报告
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* 总体覆盖率 */}
                {coverageData.percentage !== undefined && (
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium">总体覆盖率</span>
                      <span className="text-2xl font-bold text-blue-600">
                        {coverageData.percentage.toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-4">
                      <div
                        className="bg-blue-600 h-4 rounded-full transition-all"
                        style={{ width: `${coverageData.percentage}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* 详细统计 */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t">
                  {/* 行覆盖率 */}
                  {coverageData.lines_total !== undefined && (
                    <div>
                      <p className="text-sm text-gray-500 mb-1">行覆盖率</p>
                      <p className="text-lg font-semibold">
                        {coverageData.lines_covered || 0} / {coverageData.lines_total}
                      </p>
                      <p className="text-xs text-gray-400">
                        {getCoveragePercentage(
                          coverageData.lines_covered,
                          coverageData.lines_total
                        )}%
                      </p>
                    </div>
                  )}

                  {/* 分支覆盖率 */}
                  {coverageData.branches_total !== undefined && (
                    <div>
                      <p className="text-sm text-gray-500 mb-1">分支覆盖率</p>
                      <p className="text-lg font-semibold">
                        {coverageData.branches_covered || 0} / {coverageData.branches_total}
                      </p>
                      <p className="text-xs text-gray-400">
                        {getCoveragePercentage(
                          coverageData.branches_covered,
                          coverageData.branches_total
                        )}%
                      </p>
                    </div>
                  )}

                  {/* 函数覆盖率 */}
                  {coverageData.functions_total !== undefined && (
                    <div>
                      <p className="text-sm text-gray-500 mb-1">函数覆盖率</p>
                      <p className="text-lg font-semibold">
                        {coverageData.functions_covered || 0} / {coverageData.functions_total}
                      </p>
                      <p className="text-xs text-gray-400">
                        {getCoveragePercentage(
                          coverageData.functions_covered,
                          coverageData.functions_total
                        )}%
                      </p>
                    </div>
                  )}
                </div>

                {/* 覆盖率报告链接 */}
                {execution.artifacts && execution.artifacts.length > 0 && (
                  <div className="pt-4 border-t space-y-2">
                    <p className="text-sm font-medium text-gray-700">生成的报告：</p>
                    {execution.artifacts
                      .filter((a: Artifact) => a.type === 'coverage_report')
                      .map((artifact: Artifact, idx: number) => (
                        <a
                          key={idx}
                          href={`http://localhost:8000${artifact.path}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline flex items-center gap-2"
                        >
                          <FileText className="h-4 w-4" />
                          查看详细HTML覆盖率报告
                        </a>
                      ))}
                    {execution.artifacts
                      .filter((a: Artifact) => a.type === 'test_code')
                      .map((artifact: Artifact, idx: number) => (
                        <a
                          key={idx}
                          href={`http://localhost:8000${artifact.path}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline flex items-center gap-2"
                        >
                          <FileText className="h-4 w-4" />
                          查看生成的测试代码
                        </a>
                      ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* 内存调试结果 */}
          {memoryIssues.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MemoryStick className="h-5 w-5" />
                  内存调试结果 (Dr. Memory)
                </CardTitle>
                <CardDescription>
                  发现 {memoryIssues.length} 个内存问题
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {memoryIssues.map((issue) => (
                  <div
                    key={issue.id}
                    className={`p-4 border rounded-lg ${getSeverityColor(issue.severity)}`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <p className="font-semibold">问题 #{issue.id}</p>
                        <p className="text-sm opacity-80">{issue.message}</p>
                      </div>
                      <span
                        className={`px-2 py-1 text-xs rounded-full ${
                          issue.severity === 'error'
                            ? 'bg-red-100 text-red-800'
                            : issue.severity === 'warning'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-blue-100 text-blue-800'
                        }`}
                      >
                        {issue.severity}
                      </span>
                    </div>

                    {/* 堆栈跟踪 */}
                    {issue.stack_trace && issue.stack_trace.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-opacity-20">
                        <p className="text-xs font-medium mb-2">堆栈跟踪:</p>
                        <div className="space-y-1 font-mono text-xs">
                          {issue.stack_trace.slice(0, 5).map((frame, idx) => (
                            <div key={idx} className="opacity-80">
                              #{frame.frame} {frame.function}
                              {frame.file && (
                                <span className="text-gray-600">
                                  {' '}at {frame.file}
                                  {frame.line && `:${frame.line}`}
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}

                {/* 内存报告链接 */}
                {execution.artifacts && execution.artifacts.length > 0 && (
                  <div className="pt-4 border-t space-y-2">
                    <p className="text-sm font-medium text-gray-700">生成的报告：</p>
                    {execution.artifacts
                      .filter((a: Artifact) => a.type === 'memory_report')
                      .map((artifact: Artifact, idx: number) => (
                        <a
                          key={idx}
                          href={`http://localhost:8000${artifact.path}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline flex items-center gap-2"
                        >
                          <FileText className="h-4 w-4" />
                          查看详细JSON内存调试报告
                        </a>
                      ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* 执行日志 */}
          {execution.logs && (
            <Card>
              <CardHeader>
                <CardTitle>执行日志</CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="bg-gray-50 p-4 rounded-lg text-sm overflow-auto max-h-96 whitespace-pre-wrap">
                  {execution.logs}
                </pre>
              </CardContent>
            </Card>
          )}

          {/* 错误信息 */}
          {execution.error_message && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-red-600">
                  <AlertTriangle className="h-5 w-5" />
                  错误信息
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-red-600">{execution.error_message}</p>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* 空状态 */}
      {!isLoadingExecutions && !executionsError && (!executions || executions.length === 0) && (
        <Card>
          <CardContent className="text-center py-12">
            <BarChart3 className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">暂无执行记录</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

