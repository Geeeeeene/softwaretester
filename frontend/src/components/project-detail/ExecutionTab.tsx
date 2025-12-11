import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Play, Loader2, CheckCircle2, XCircle } from 'lucide-react'
import { executionsApi } from '@/lib/api'
import { useQuery } from '@tanstack/react-query'
import type { AxiosResponse } from 'axios'
import type { TestExecution } from '@/lib/api'
import { useToolStatus } from '@/hooks/useToolStatus'
import { ToolErrorDialog } from '@/components/ToolErrorDialog'

interface ExecutionTabProps {
  projectId: number
  onNavigateToTab: (tab: string, params?: Record<string, any>) => void
}

export function ExecutionTab({ projectId, onNavigateToTab }: ExecutionTabProps) {
  const [isExecuting, setIsExecuting] = useState(false)
  const [currentExecutionId, setCurrentExecutionId] = useState<number | null>(null)
  const [toolErrorDialogOpen, setToolErrorDialogOpen] = useState(false)
  const { checkUnitTestTools, isLoading: isLoadingTools } = useToolStatus()

  // 获取历史执行列表
  const { data: executions, isLoading } = useQuery({
    queryKey: ['executions', projectId],
    queryFn: async () => {
      const response = await executionsApi.list({ project_id: projectId, limit: 20 })
      return response.data
    },
  })

  const handleExecute = async () => {
    // 检查工具可用性
    const toolCheck = checkUnitTestTools()
    
    if (!toolCheck.allAvailable) {
      setToolErrorDialogOpen(true)
      return
    }

    try {
      setIsExecuting(true)
      const response = await executionsApi.runUnitTest(projectId)
      const executionId = response.data.execution_id
      setCurrentExecutionId(executionId)
      
      // 轮询获取执行结果
      const pollExecution = async () => {
        try {
          const execResponse = await executionsApi.get(executionId)
          const exec = execResponse.data
          
          if (exec.status === 'completed' || exec.status === 'failed') {
            setIsExecuting(false)
            onNavigateToTab('reports', { executionId: executionId.toString() })
          } else {
            setTimeout(pollExecution, 5000)
          }
        } catch (error) {
          console.error('轮询执行结果失败:', error)
          setTimeout(pollExecution, 5000)
        }
      }
      
      setTimeout(pollExecution, 2000)
    } catch (error: any) {
      console.error('执行测试失败:', error)
      alert(`执行失败: ${error.response?.data?.detail || error.message || '未知错误'}`)
      setIsExecuting(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* 运行配置 */}
      <Card>
        <CardHeader>
          <CardTitle>运行配置</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                执行模式
              </label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-md">
                <option value="all">全部用例</option>
                <option value="selected">指定用例</option>
                <option value="custom">自定义</option>
              </select>
            </div>
            <Button
              onClick={handleExecute}
              disabled={isExecuting}
              className="w-full"
              size="lg"
            >
              {isExecuting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  执行中...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  立即执行
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 历史执行列表 */}
      <Card>
        <CardHeader>
          <CardTitle>历史执行</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8">
              <Loader2 className="h-8 w-8 mx-auto text-gray-400 animate-spin mb-4" />
              <p className="text-gray-500">加载中...</p>
            </div>
          ) : executions && executions.length > 0 ? (
            <div className="space-y-2">
              {executions.map((exec: TestExecution) => (
                <div
                  key={exec.id}
                  className="p-3 border rounded-lg hover:bg-gray-50 cursor-pointer"
                  onClick={() => onNavigateToTab('reports', { executionId: exec.id.toString() })}
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-medium">执行 #{exec.id}</p>
                      <p className="text-sm text-gray-500">
                        {exec.passed_tests}/{exec.total_tests} 通过
                        {exec.duration_seconds && ` • ${exec.duration_seconds.toFixed(2)}s`}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {exec.status === 'completed' && exec.failed_tests === 0 ? (
                        <CheckCircle2 className="h-5 w-5 text-green-500" />
                      ) : (
                        <XCircle className="h-5 w-5 text-red-500" />
                      )}
                      <span className="text-sm capitalize">{exec.status}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              暂无执行记录
            </div>
          )}
        </CardContent>
      </Card>

      {/* 工具错误对话框 */}
      <ToolErrorDialog
        open={toolErrorDialogOpen}
        onOpenChange={setToolErrorDialogOpen}
        missingTools={checkUnitTestTools().missing}
        onRetry={handleExecute}
      />
    </div>
  )
}

