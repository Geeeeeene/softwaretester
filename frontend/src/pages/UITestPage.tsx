import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ArrowLeft, Plus, Play, CheckCircle, XCircle, Clock, Loader2 } from 'lucide-react'
import { projectsApi, uiTestApi } from '@/lib/api'
import { UITestDialog } from '@/components/ui-test/UITestDialog'

export default function UITestPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const projectId = id ? parseInt(id, 10) : null

  const [showTestDialog, setShowTestDialog] = useState(false)

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

  // 获取测试执行历史
  const { data: executionsData, isLoading: executionsLoading, refetch: refetchExecutions } = useQuery({
    queryKey: ['ui-test-executions', projectId],
    queryFn: async () => {
      if (!projectId) throw new Error('无效的项目ID')
      const response = await uiTestApi.listExecutions(projectId)
      return response.data
    },
    enabled: !!projectId,
    refetchInterval: 5000, // 每5秒刷新
  })

  const handleTestComplete = () => {
    refetchExecutions()
  }

  if (!projectId) {
    return (
      <div className="text-center py-12">
        <p className="text-red-500">无效的项目ID</p>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <Loader2 className="h-8 w-8 mx-auto text-gray-400 animate-spin mb-4" />
        <p className="text-gray-500">加载中...</p>
      </div>
    )
  }

  const statistics = executionsData?.statistics || {
    total_executions: 0,
    completed_executions: 0,
    passed_executions: 0,
    pass_rate: 0
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部工具栏 */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={() => navigate(`/projects/${projectId}`)}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              返回
            </Button>
            <div>
              <h1 className="text-xl font-bold text-gray-900">{project.name} - UI测试</h1>
              <p className="text-sm text-gray-600 mt-1">
                基于Robot Framework + SikuliLibrary的UI自动化测试
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 四栏布局 */}
      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* 第一栏：测试分析 */}
          <Card>
            <CardHeader>
              <CardTitle>测试分析</CardTitle>
              <CardDescription>创建和执行UI测试</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button
                className="w-full justify-start"
                onClick={() => setShowTestDialog(true)}
              >
                <Plus className="mr-2 h-4 w-4" />
                UI测试（使用AI生成UI测试用例）
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => {
                  // 滚动到执行记录部分
                  document.getElementById('test-results')?.scrollIntoView({ behavior: 'smooth' })
                }}
              >
                <Play className="mr-2 h-4 w-4" />
                查看测试结果
              </Button>
            </CardContent>
          </Card>

          {/* 第二栏：基本信息 */}
          <Card>
            <CardHeader>
              <CardTitle>基本信息</CardTitle>
              <CardDescription>项目配置信息</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <div className="text-sm font-medium text-gray-700">项目名称</div>
                <div className="text-sm text-gray-900">{project.name}</div>
              </div>
              {project.description && (
                <div>
                  <div className="text-sm font-medium text-gray-700">项目描述</div>
                  <div className="text-sm text-gray-600">{project.description}</div>
                </div>
              )}
              <div>
                <div className="text-sm font-medium text-gray-700">项目类型</div>
                <div className="text-sm text-gray-900">UI测试</div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-700">创建时间</div>
                <div className="text-sm text-gray-600">
                  {new Date(project.created_at).toLocaleString('zh-CN')}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 第三栏：源代码文件 */}
          <Card>
            <CardHeader>
              <CardTitle>源代码文件</CardTitle>
              <CardDescription>测试目标信息</CardDescription>
            </CardHeader>
            <CardContent>
              {project.source_path ? (
                <div>
                  <div className="text-sm font-medium text-gray-700 mb-1">源代码路径</div>
                  <div className="text-sm text-gray-900 bg-gray-100 p-2 rounded border border-gray-200 break-all">
                    {project.source_path}
                  </div>
                </div>
              ) : (
                <p className="text-sm text-gray-500">未配置源代码路径</p>
              )}
            </CardContent>
          </Card>

          {/* 第四栏：测试用例、执行记录、通过率 */}
          <Card>
            <CardHeader>
              <CardTitle>测试统计</CardTitle>
              <CardDescription>执行记录和通过率</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <div className="text-sm font-medium text-gray-700">测试用例</div>
                <div className="text-2xl font-bold text-gray-900">{statistics.total_executions}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-700">执行记录</div>
                <div className="text-2xl font-bold text-gray-900">{statistics.completed_executions}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-700">通过率</div>
                <div className="text-2xl font-bold text-green-600">{statistics.pass_rate.toFixed(1)}%</div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 测试结果列表 */}
        <div id="test-results" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>测试执行历史</CardTitle>
              <CardDescription>查看所有UI测试执行记录</CardDescription>
            </CardHeader>
            <CardContent>
              {executionsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 text-gray-400 animate-spin" />
                </div>
              ) : executionsData?.items && executionsData.items.length > 0 ? (
                <div className="space-y-3">
                  {executionsData.items.map((execution) => {
                    const isPassed = execution.status === 'completed' && execution.failed_tests === 0
                    const isRunning = execution.status === 'running'
                    const isFailed = execution.status === 'failed' || (execution.status === 'completed' && execution.failed_tests > 0)

                    return (
                      <div
                        key={execution.id}
                        className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              {isRunning && <Clock className="h-5 w-5 text-blue-500" />}
                              {isPassed && <CheckCircle className="h-5 w-5 text-green-500" />}
                              {isFailed && <XCircle className="h-5 w-5 text-red-500" />}
                              <span className="font-medium text-gray-900">
                                执行 #{execution.id}
                              </span>
                              <span className={`text-sm px-2 py-1 rounded ${
                                isRunning ? 'bg-blue-100 text-blue-700' :
                                isPassed ? 'bg-green-100 text-green-700' :
                                'bg-red-100 text-red-700'
                              }`}>
                                {isRunning ? '执行中' : isPassed ? '通过' : '失败'}
                              </span>
                            </div>
                            <div className="mt-2 text-sm text-gray-600 space-y-1">
                              <div>
                                执行时间：{new Date(execution.created_at).toLocaleString('zh-CN')}
                              </div>
                              {execution.duration_seconds && (
                                <div>
                                  执行时长：{execution.duration_seconds.toFixed(2)} 秒
                                </div>
                              )}
                              <div>
                                测试结果：通过 {execution.passed_tests}，失败 {execution.failed_tests}
                              </div>
                              {execution.error_message && (
                                <div className="text-red-600 mt-1">
                                  错误：{execution.error_message}
                                </div>
                              )}
                            </div>
                          </div>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              // 可以实现查看详情功能
                              navigate(`/projects/${projectId}/ui-test/results/${execution.id}`)
                            }}
                          >
                            查看详情
                          </Button>
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-500">暂无测试执行记录</p>
                  <p className="text-sm text-gray-400 mt-1">点击"UI测试"按钮创建第一个测试用例</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* 测试对话框 */}
      <UITestDialog
        open={showTestDialog}
        onClose={() => setShowTestDialog(false)}
        projectId={projectId}
        onTestComplete={handleTestComplete}
      />
    </div>
  )
}

