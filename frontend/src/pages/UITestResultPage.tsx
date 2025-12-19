import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ArrowLeft, CheckCircle, XCircle, Loader2, FileCode, Clock } from 'lucide-react'
import { uiTestApi, projectsApi } from '@/lib/api'

export default function UITestResultPage() {
  const { id, executionId } = useParams<{ id: string; executionId: string }>()
  const navigate = useNavigate()
  const projectId = id ? parseInt(id, 10) : null
  const execId = executionId ? parseInt(executionId, 10) : null

  // 获取项目信息
  const { data: project } = useQuery({
    queryKey: ['project', projectId],
    queryFn: async () => {
      if (!projectId) throw new Error('无效的项目ID')
      const response = await projectsApi.get(projectId)
      return response.data
    },
    enabled: !!projectId,
  })

  // 获取测试结果
  const { data: testResult, isLoading } = useQuery({
    queryKey: ['ui-test-result', projectId, execId],
    queryFn: async () => {
      if (!projectId || !execId) throw new Error('无效的参数')
      const response = await uiTestApi.getTestResult(projectId, execId)
      return response.data
    },
    enabled: !!projectId && !!execId,
    refetchInterval: (data) => {
      // 如果状态是running，每2秒轮询一次
      if (data?.status === 'running') {
        return 2000
      }
      return false
    }
  })

  if (!projectId || !execId) {
    return (
      <div className="text-center py-12">
        <p className="text-red-500">无效的参数</p>
      </div>
    )
  }

  if (isLoading || !testResult) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <Button variant="ghost" onClick={() => navigate(`/projects/${projectId}/ui-test`)}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            返回
          </Button>
        </div>
        <div className="text-center py-12">
          <Loader2 className="h-8 w-8 mx-auto text-gray-400 animate-spin mb-4" />
          <p className="text-gray-500">加载中...</p>
        </div>
      </div>
    )
  }

  const isPassed = testResult.passed
  const isRunning = testResult.status === 'running'
  const isFailed = !testResult.passed

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部工具栏 */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={() => navigate(`/projects/${projectId}/ui-test`)}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              返回
            </Button>
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                {project?.name || '项目'} - 测试结果 #{execId}
              </h1>
              <div className="flex items-center gap-2 mt-1">
                {isRunning && (
                  <>
                    <Clock className="h-4 w-4 text-blue-500" />
                    <span className="text-sm text-blue-600">执行中...</span>
                  </>
                )}
                {isPassed && !isRunning && (
                  <>
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span className="text-sm text-green-600">测试通过</span>
                  </>
                )}
                {isFailed && !isRunning && (
                  <>
                    <XCircle className="h-4 w-4 text-red-500" />
                    <span className="text-sm text-red-600">测试失败</span>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 内容区域 */}
      <div className="p-6 space-y-6">
        {/* 执行信息 */}
        <Card>
          <CardHeader>
            <CardTitle>执行信息</CardTitle>
            <CardDescription>测试执行的基本信息</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <div className="text-sm font-medium text-gray-700">执行ID</div>
                <div className="text-lg font-semibold text-gray-900">{testResult.execution_id}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-700">状态</div>
                <div className={`text-lg font-semibold ${
                  isRunning ? 'text-blue-600' :
                  isPassed ? 'text-green-600' : 'text-red-600'
                }`}>
                  {isRunning ? '执行中' : isPassed ? '通过' : '失败'}
                </div>
              </div>
              {testResult.duration_seconds && (
                <div>
                  <div className="text-sm font-medium text-gray-700">执行时长</div>
                  <div className="text-lg font-semibold text-gray-900">
                    {testResult.duration_seconds.toFixed(2)} 秒
                  </div>
                </div>
              )}
              <div>
                <div className="text-sm font-medium text-gray-700">执行时间</div>
                <div className="text-sm text-gray-900">
                  {new Date(testResult.created_at).toLocaleString('zh-CN')}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 错误信息 */}
        {testResult.error_message && (
          <Card>
            <CardHeader>
              <CardTitle className="text-red-700">错误信息</CardTitle>
              <CardDescription>测试执行过程中发生的错误</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <p className="text-sm text-red-800 whitespace-pre-wrap">{testResult.error_message}</p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* 测试日志 */}
        {testResult.logs && (
          <Card>
            <CardHeader>
              <CardTitle>测试日志</CardTitle>
              <CardDescription>完整的测试执行日志</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="bg-gray-900 text-gray-100 p-4 rounded-md overflow-x-auto max-h-[600px] overflow-y-auto">
                <pre className="text-xs">
                  <code>{testResult.logs}</code>
                </pre>
              </div>
            </CardContent>
          </Card>
        )}

        {/* 生成的文件 */}
        {testResult.artifacts && testResult.artifacts.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>生成的文件</CardTitle>
              <CardDescription>测试执行过程中生成的报告和截图</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {testResult.artifacts.map((artifact, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
                  >
                    <div className="flex items-center gap-3">
                      <FileCode className="h-5 w-5 text-gray-500" />
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {artifact.name || artifact.path.split('/').pop()}
                        </div>
                        <div className="text-xs text-gray-500">
                          {artifact.type === 'robot_output' && 'Robot Framework 输出文件'}
                          {artifact.type === 'robot_log' && 'Robot Framework 日志'}
                          {artifact.type === 'robot_report' && 'Robot Framework 报告'}
                          {artifact.type === 'screenshot' && '测试截图'}
                          {!['robot_output', 'robot_log', 'robot_report', 'screenshot'].includes(artifact.type) && artifact.type}
                        </div>
                      </div>
                    </div>
                    <div className="text-xs text-gray-500">
                      {artifact.path}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

