import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Play, RefreshCw, CheckCircle, XCircle, Clock, AlertCircle } from 'lucide-react'
import { executionsApi, type TestExecution } from '@/lib/api'
import { formatDateTime } from '@/lib/utils'
import { useEffect } from 'react'

export default function TestExecutionPage() {
  const [searchParams] = useSearchParams()
  const executionId = searchParams.get('execution_id') ? Number(searchParams.get('execution_id')) : null

  const { data: execution, isLoading, error, refetch } = useQuery({
    queryKey: ['execution', executionId],
    queryFn: () => executionsApi.get(executionId!).then(res => res.data),
    enabled: !!executionId,
  })

  // 如果正在运行，自动刷新
  useEffect(() => {
    if (execution?.status === 'running' || execution?.status === 'pending') {
      const interval = setInterval(() => {
        refetch()
      }, 2000)
      return () => clearInterval(interval)
    }
  }, [execution?.status, refetch])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'passed':
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-600" />
      case 'running':
        return <RefreshCw className="h-5 w-5 text-blue-600 animate-spin" />
      case 'pending':
        return <Clock className="h-5 w-5 text-yellow-600" />
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-600" />
      default:
        return <Clock className="h-5 w-5 text-gray-600" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'passed':
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'failed':
      case 'error':
        return 'bg-red-100 text-red-800'
      case 'running':
        return 'bg-blue-100 text-blue-800'
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  if (!executionId) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">测试执行</h1>
        <p className="text-gray-600 mt-2">启动和监控测试执行</p>
      </div>
      <Card>
        <CardContent className="text-center py-12">
          <Play className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">请从测试用例页面运行测试，或输入执行ID查看结果</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">加载中...</p>
      </div>
    )
  }

  if (error || !execution) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">测试执行</h1>
          <p className="text-gray-600 mt-2">执行记录不存在</p>
        </div>
        <Card>
          <CardContent className="text-center py-12">
            <p className="text-red-500">无法加载执行记录，请检查执行ID是否正确</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">测试执行详情</h1>
          <p className="text-gray-600 mt-2">执行ID: {execution.id}</p>
        </div>
        <Button variant="outline" onClick={() => refetch()}>
          <RefreshCw className="mr-2 h-4 w-4" />
          刷新
        </Button>
      </div>

      {/* 执行状态 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>执行状态</CardTitle>
            <span className={`px-3 py-1 rounded-full text-sm font-medium flex items-center gap-2 ${getStatusColor(execution.status)}`}>
              {getStatusIcon(execution.status)}
              {execution.status.toUpperCase()}
            </span>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-500">执行器类型</p>
              <p className="text-base font-medium capitalize">{execution.executor_type}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">总测试数</p>
              <p className="text-base font-medium">{execution.total_tests}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">通过</p>
              <p className="text-base font-medium text-green-600">{execution.passed_tests}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">失败</p>
              <p className="text-base font-medium text-red-600">{execution.failed_tests}</p>
            </div>
          </div>
          {execution.duration_seconds && (
            <div>
              <p className="text-sm text-gray-500">执行时间</p>
              <p className="text-base font-medium">{execution.duration_seconds.toFixed(2)} 秒</p>
            </div>
          )}
          {execution.error_message && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <p className="text-sm font-medium text-red-800">错误信息</p>
              <p className="text-sm text-red-600 mt-1">{execution.error_message}</p>
            </div>
          )}
          <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
            <div>
              <p className="text-gray-500">创建时间</p>
              <p>{formatDateTime(execution.created_at)}</p>
            </div>
            {execution.started_at && (
              <div>
                <p className="text-gray-500">开始时间</p>
                <p>{formatDateTime(execution.started_at)}</p>
              </div>
            )}
            {execution.completed_at && (
              <div>
                <p className="text-gray-500">完成时间</p>
                <p>{formatDateTime(execution.completed_at)}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 如果正在运行，显示提示 */}
      {(execution.status === 'running' || execution.status === 'pending') && (
        <Card>
          <CardContent className="text-center py-8">
            <RefreshCw className="h-12 w-12 mx-auto text-blue-600 mb-4 animate-spin" />
            <p className="text-gray-600">测试正在执行中，页面会自动刷新...</p>
            <p className="text-sm text-gray-500 mt-2">执行器: {execution.executor_type}</p>
          </CardContent>
        </Card>
      )}

      {/* 静态分析结果详情 */}
      {execution.status === 'completed' && execution.test_results && execution.test_results.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>详细结果</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {execution.test_results.map((result) => (
              <div key={result.id} className="space-y-4">
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-medium">状态: 
                    <span className={`ml-2 px-2 py-0.5 rounded text-sm ${getStatusColor(result.status)}`}>
                      {result.status}
                    </span>
                  </h3>
                </div>

                {/* 错误信息（如果有） */}
                {result.error_message && (
                  <div className="bg-red-50 p-4 rounded-md text-red-700 whitespace-pre-wrap">
                    {result.error_message}
                  </div>
                )}
                
                {/* 静态分析 Issues 列表 */}
                {result.extra_data?.issues && result.extra_data.issues.length > 0 ? (
                  <div className="border rounded-md overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-2 text-left">Severity</th>
                          <th className="px-4 py-2 text-left">File:Line</th>
                          <th className="px-4 py-2 text-left">Message</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {result.extra_data.issues.map((issue: any, index: number) => (
                          <tr key={index} className="hover:bg-gray-50">
                            <td className="px-4 py-2">
                              <span className={`px-2 py-0.5 rounded text-xs font-medium
                                ${issue.severity === 'error' ? 'bg-red-100 text-red-800' : 
                                  issue.severity === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                                  'bg-blue-100 text-blue-800'}`}>
                                {issue.severity}
                              </span>
                            </td>
                            <td className="px-4 py-2 font-mono text-gray-600">
                              {issue.file}:{issue.line ?? '未知'}
                            </td>
                            <td className="px-4 py-2 text-gray-900">
                              {issue.message}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  result.status === 'passed' && (
                    <div className="text-green-600 flex items-center gap-2 bg-green-50 p-4 rounded">
                      <CheckCircle className="h-5 w-5" />
                      未发现静态分析问题
                    </div>
                  )
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

