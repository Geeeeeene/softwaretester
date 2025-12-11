import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { BarChart3, CheckCircle2, XCircle, AlertTriangle, TrendingUp, MemoryStick, FileText, Loader2 } from 'lucide-react'
import { executionsApi, type TestExecution } from '@/lib/api'
import type { AxiosResponse } from 'axios'
import { useSearchParams } from 'react-router-dom'
import { useToolStatus } from '@/hooks/useToolStatus'

interface ReportsTabProps {
  projectId: number
}

export function ReportsTab({ projectId }: ReportsTabProps) {
  const [searchParams, setSearchParams] = useSearchParams()
  const executionIdParam = searchParams.get('executionId')
  const [selectedExecutionId, setSelectedExecutionId] = useState<number | null>(
    executionIdParam ? parseInt(executionIdParam, 10) : null
  )
  
  // 检查工具状态
  const { checkUnitTestTools } = useToolStatus()
  const toolCheck = checkUnitTestTools()

  // 获取执行列表
  const { data: executions } = useQuery({
    queryKey: ['executions', projectId],
    queryFn: async () => {
      const response = await executionsApi.list({ project_id: projectId, limit: 20 })
      return response.data
    },
  })

  // 获取选中的执行详情
  const { data: execution, isLoading } = useQuery({
    queryKey: ['execution', selectedExecutionId],
    queryFn: () => executionsApi.get(selectedExecutionId!).then((res: AxiosResponse<TestExecution>) => res.data),
    enabled: !!selectedExecutionId && !isNaN(selectedExecutionId),
  })

  // 当URL参数变化时更新选中的执行ID
  useEffect(() => {
    if (executionIdParam) {
      const parsedId = parseInt(executionIdParam, 10)
      if (!isNaN(parsedId)) {
        setSelectedExecutionId(parsedId)
      }
    }
  }, [executionIdParam])

  const getCoveragePercentage = (covered: number = 0, total: number = 0) => {
    if (total === 0) return 0
    return Math.round((covered / total) * 100)
  }

  return (
    <div className="space-y-6">
      {/* 工具状态警告横幅 */}
      {!toolCheck.allAvailable && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-medium text-yellow-900 mb-1">
                  部分工具未安装
                </p>
                <p className="text-xs text-yellow-700">
                  报告可能不完整，因为以下工具未找到：{toolCheck.missing.map(m => m.name).join('、')}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 执行记录选择器 */}
      {executions && executions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>执行记录</CardTitle>
            <CardDescription>选择要查看的执行记录</CardDescription>
          </CardHeader>
          <CardContent>
            <select
              value={selectedExecutionId || ''}
              onChange={(e) => {
                const id = e.target.value ? parseInt(e.target.value, 10) : null
                setSelectedExecutionId(id)
                if (id) {
                  setSearchParams({ executionId: id.toString() })
                } else {
                  setSearchParams({})
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="">选择执行记录...</option>
              {executions.map((exec: TestExecution) => (
                <option key={exec.id} value={exec.id}>
                  执行 #{exec.id} - {new Date(exec.created_at).toLocaleString()}
                </option>
              ))}
            </select>
          </CardContent>
        </Card>
      )}

      {/* 执行详情加载状态 */}
      {selectedExecutionId && isLoading && (
        <Card>
          <CardContent className="text-center py-12">
            <Loader2 className="h-12 w-12 mx-auto text-blue-400 mb-4 animate-spin" />
            <p className="text-gray-500">加载执行详情中...</p>
          </CardContent>
        </Card>
      )}

      {/* 执行详情 */}
      {execution && !isLoading && (
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
          {execution.coverage_data && (
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
                {execution.coverage_data.percentage !== undefined && (
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium">总体覆盖率</span>
                      <span className="text-2xl font-bold text-blue-600">
                        {execution.coverage_data.percentage.toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-4">
                      <div
                        className="bg-blue-600 h-4 rounded-full transition-all"
                        style={{ width: `${execution.coverage_data.percentage}%` }}
                      />
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t">
                  {execution.coverage_data.lines_total !== undefined && (
                    <div>
                      <p className="text-sm text-gray-500 mb-1">行覆盖率</p>
                      <p className="text-lg font-semibold">
                        {execution.coverage_data.lines_covered || 0} / {execution.coverage_data.lines_total}
                      </p>
                      <p className="text-xs text-gray-400">
                        {getCoveragePercentage(
                          execution.coverage_data.lines_covered,
                          execution.coverage_data.lines_total
                        )}%
                      </p>
                    </div>
                  )}

                  {execution.coverage_data.branches_total !== undefined && (
                    <div>
                      <p className="text-sm text-gray-500 mb-1">分支覆盖率</p>
                      <p className="text-lg font-semibold">
                        {execution.coverage_data.branches_covered || 0} / {execution.coverage_data.branches_total}
                      </p>
                      <p className="text-xs text-gray-400">
                        {getCoveragePercentage(
                          execution.coverage_data.branches_covered,
                          execution.coverage_data.branches_total
                        )}%
                      </p>
                    </div>
                  )}

                  {execution.coverage_data.functions_total !== undefined && (
                    <div>
                      <p className="text-sm text-gray-500 mb-1">函数覆盖率</p>
                      <p className="text-lg font-semibold">
                        {execution.coverage_data.functions_covered || 0} / {execution.coverage_data.functions_total}
                      </p>
                      <p className="text-xs text-gray-400">
                        {getCoveragePercentage(
                          execution.coverage_data.functions_covered,
                          execution.coverage_data.functions_total
                        )}%
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* 内存调试结果 */}
          {execution.result?.issues && execution.result.issues.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MemoryStick className="h-5 w-5" />
                  内存调试结果 (Dr. Memory)
                </CardTitle>
                <CardDescription>
                  发现 {execution.result.total_issues || execution.result.issues.length} 个内存问题
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {execution.result.issues.map((issue: any) => (
                  <div
                    key={issue.id}
                    className={`p-4 border rounded-lg ${
                      issue.severity === 'error'
                        ? 'bg-red-50 border-red-200'
                        : issue.severity === 'warning'
                        ? 'bg-yellow-50 border-yellow-200'
                        : 'bg-blue-50 border-blue-200'
                    }`}
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

                    {issue.stack_trace && issue.stack_trace.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-opacity-20">
                        <p className="text-xs font-medium mb-2">堆栈跟踪:</p>
                        <div className="space-y-1 font-mono text-xs">
                          {issue.stack_trace.slice(0, 5).map((frame: any, idx: number) => (
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
        </>
      )}

      {/* 空状态 */}
      {!selectedExecutionId && (
        <Card>
          <CardContent className="text-center py-12">
            <BarChart3 className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">请选择一个执行记录查看报告</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

