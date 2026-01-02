import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ArrowLeft, Plus, Play, CheckCircle, XCircle, Clock, Loader2, FileText, RefreshCw, Trash2, Eye } from 'lucide-react'
import { projectsApi, uiTestApi, testCasesApi } from '@/lib/api'
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

  // 获取UI测试用例列表
  const { data: testCasesData, isLoading: testCasesLoading, refetch: refetchTestCases } = useQuery({
    queryKey: ['ui-test-cases', projectId],
    queryFn: async () => {
      if (!projectId) throw new Error('无效的项目ID')
      const response = await testCasesApi.list({ project_id: projectId, test_type: 'ui' })
      return response.data
    },
    enabled: !!projectId,
  })

  const handleTestComplete = () => {
    refetchExecutions()
    refetchTestCases()
  }

  // 重新执行测试用例
  const handleReExecute = async (testCase: any) => {
    if (!testCase.test_ir?.robot_script) {
      alert('测试用例缺少Robot Framework脚本')
      return
    }

    try {
      const response = await uiTestApi.executeTest(projectId!, {
        name: testCase.name,
        description: testCase.description || '',
        robot_script: testCase.test_ir.robot_script
      })
      
      if (response.data.execution_id) {
        alert('测试已开始执行')
        // 使用 setTimeout 延迟刷新，避免在状态更新过程中出错
        setTimeout(() => {
          try {
            refetchExecutions().catch((err) => {
              console.error('刷新执行记录失败:', err)
              // 不显示错误，因为测试已经成功提交
            })
          } catch (err) {
            console.error('刷新执行记录时出错:', err)
          }
        }, 100)
      }
    } catch (error: any) {
      console.error('执行测试失败:', error)
      const errorMessage = error.response?.data?.detail || error.message || '未知错误'
      alert(`执行失败: ${errorMessage}`)
    }
  }

  // 删除测试用例
  const handleDeleteTestCase = async (testCaseId: number) => {
    if (!confirm('确定要删除这个测试用例吗？此操作不可恢复。')) {
      return
    }

    try {
      await testCasesApi.delete(testCaseId)
      alert('测试用例已删除')
      refetchTestCases()
      // 同时刷新执行记录，因为统计可能会变化
      refetchExecutions()
    } catch (error: any) {
      console.error('删除测试用例失败:', error)
      alert(`删除失败: ${error.response?.data?.detail || error.message || '未知错误'}`)
    }
  }

  // 删除执行记录
  const handleDeleteExecution = async (executionId: number) => {
    if (!confirm('确定要删除这个执行记录吗？此操作不可恢复。')) {
      return
    }

    try {
      await uiTestApi.deleteExecution(projectId!, executionId)
      alert('执行记录已删除')
      // 使用 setTimeout 延迟刷新，避免在状态更新过程中出错
      setTimeout(() => {
        try {
          refetchExecutions().catch((err) => {
            console.error('刷新执行记录失败:', err)
            // 不显示错误，因为删除已经成功
          })
        } catch (err) {
          console.error('刷新执行记录时出错:', err)
        }
      }, 100)
    } catch (error: any) {
      console.error('删除执行记录失败:', error)
      const errorMessage = error.response?.data?.detail || error.message || '未知错误'
      alert(`删除失败: ${errorMessage}`)
    }
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

  // 测试用例数量（从测试用例列表获取）
  const testCaseCount = testCasesData?.total || 0

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

          {/* 第三栏：应用程序信息 */}
          <Card>
            <CardHeader>
              <CardTitle>应用程序信息</CardTitle>
              <CardDescription>待测试应用程序的路径信息</CardDescription>
            </CardHeader>
            <CardContent>
              {project.source_path ? (
                <div>
                  <div className="text-sm font-medium text-gray-700 mb-1">应用程序路径</div>
                  <div className="text-sm text-gray-900 bg-gray-100 p-2 rounded border border-gray-200 break-all">
                    {project.source_path}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">此路径指向待测试应用程序的可执行文件（.exe）</p>
                </div>
              ) : (
                <p className="text-sm text-gray-500">未配置应用程序路径</p>
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
                <div className="text-2xl font-bold text-gray-900">{testCaseCount}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-700">执行次数</div>
                <div className="text-2xl font-bold text-gray-900">{statistics.total_executions}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-700">通过率</div>
                <div className="text-2xl font-bold text-green-600">{statistics.pass_rate.toFixed(1)}%</div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 测试用例目录 */}
        <div className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                测试用例目录
              </CardTitle>
              <CardDescription>管理和重复执行已生成的测试用例</CardDescription>
            </CardHeader>
            <CardContent>
              {testCasesLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 text-gray-400 animate-spin" />
                </div>
              ) : testCasesData?.items && testCasesData.items.length > 0 ? (
                <div className="space-y-3">
                  {testCasesData.items.map((testCase) => (
                    <div
                      key={testCase.id}
                      className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <FileText className="h-5 w-5 text-blue-500" />
                            <span className="font-medium text-gray-900">{testCase.name}</span>
                          </div>
                          {testCase.description && (
                            <p className="text-sm text-gray-600 mt-1">{testCase.description}</p>
                          )}
                          <div className="mt-2 text-xs text-gray-500">
                            创建时间：{new Date(testCase.created_at).toLocaleString('zh-CN')}
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => navigate(`/projects/${projectId}/ui-test/cases/${testCase.id}`)}
                          >
                            <Eye className="mr-2 h-4 w-4" />
                            详情
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleReExecute(testCase)}
                          >
                            <Play className="mr-2 h-4 w-4" />
                            执行
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDeleteTestCase(testCase.id)}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            删除
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <FileText className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                  <p className="text-gray-500">暂无测试用例</p>
                  <p className="text-sm text-gray-400 mt-1">点击"UI测试"按钮创建第一个测试用例</p>
                </div>
              )}
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
                  {executionsData.items.map((execution, index) => {
                    try {
                      // 安全地获取执行状态
                      const status = execution?.status || 'unknown'
                      const failedTests = typeof execution?.failed_tests === 'number' ? execution.failed_tests : 0
                      const passedTests = typeof execution?.passed_tests === 'number' ? execution.passed_tests : 0
                      
                      const isPassed = status === 'completed' && failedTests === 0
                      const isRunning = status === 'running'
                      const isFailed = status === 'failed' || (status === 'completed' && failedTests > 0)
                      
                      // 尝试从test_results获取测试用例信息
                      let testCase = null
                      try {
                        if (execution.test_results && Array.isArray(execution.test_results) && execution.test_results.length > 0) {
                          const testCaseId = execution.test_results[0]?.test_case_id
                          if (testCaseId) {
                            testCase = testCasesData?.items?.find(tc => tc.id === testCaseId)
                          }
                        }
                        
                        // 如果找不到，尝试通过test_ir中的name匹配（如果test_ir存在）
                        if (!testCase && execution.result?.test_ir?.name) {
                          testCase = testCasesData?.items?.find(tc => tc.name === execution.result.test_ir.name)
                        }
                      } catch (err) {
                        console.error('获取测试用例信息时出错:', err)
                      }
                      
                      const testCaseName = testCase?.name || '未知用例'
                      
                      // 计算该用例的执行次数（统计该用例的所有执行记录，按时间排序）
                      let executionCount = index + 1
                      try {
                        if (testCase && executionsData.items) {
                          // 找到该用例的所有执行记录，按时间排序
                          const sameTestCaseExecutions = executionsData.items
                            .filter(e => {
                              try {
                                // 通过test_results匹配
                                if (e.test_results?.some(tr => tr.test_case_id === testCase.id)) {
                                  return true
                                }
                                // 通过test_ir中的name匹配
                                if (e.result?.test_ir?.name === testCase.name) {
                                  return true
                                }
                              } catch (err) {
                                return false
                              }
                              return false
                            })
                            .sort((a, b) => {
                              try {
                                const timeA = a.created_at ? new Date(a.created_at).getTime() : 0
                                const timeB = b.created_at ? new Date(b.created_at).getTime() : 0
                                return timeA - timeB
                              } catch (err) {
                                return 0
                              }
                            })
                          
                          // 找到当前执行记录在该用例执行记录中的位置
                          const currentIndex = sameTestCaseExecutions.findIndex(e => e.id === execution.id)
                          executionCount = currentIndex >= 0 ? currentIndex + 1 : sameTestCaseExecutions.length + 1
                        }
                      } catch (err) {
                        console.error('计算执行次数时出错:', err)
                      }

                      // 安全地格式化日期
                      let formattedDate = '未知时间'
                      try {
                        if (execution.created_at) {
                          const date = new Date(execution.created_at)
                          if (!isNaN(date.getTime())) {
                            formattedDate = date.toLocaleString('zh-CN')
                          }
                        }
                      } catch (err) {
                        console.error('格式化日期时出错:', err)
                      }

                      // 安全地格式化时长
                      let formattedDuration = null
                      try {
                        if (execution.duration_seconds != null && typeof execution.duration_seconds === 'number') {
                          formattedDuration = execution.duration_seconds.toFixed(2)
                        }
                      } catch (err) {
                        console.error('格式化时长时出错:', err)
                      }

                      return (
                        <div
                          key={execution.id || index}
                          className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 flex-wrap">
                                {isRunning && <Clock className="h-5 w-5 text-blue-500" />}
                                {isPassed && <CheckCircle className="h-5 w-5 text-green-500" />}
                                {isFailed && <XCircle className="h-5 w-5 text-red-500" />}
                                <span className="font-medium text-gray-900">
                                  序号：{index + 1}
                                </span>
                                <span className="font-medium text-gray-900">
                                  用例名称：{testCaseName}
                                </span>
                                <span className="text-sm text-gray-600">
                                  第 {executionCount} 次执行
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
                                  执行时间：{formattedDate}
                                </div>
                                {formattedDuration && (
                                  <div>
                                    执行时长：{formattedDuration} 秒
                                  </div>
                                )}
                                <div>
                                  测试结果：通过 {passedTests}，失败 {failedTests}
                                </div>
                                {execution.error_message && (
                                  <div className="text-red-600 mt-1">
                                    错误：{execution.error_message}
                                  </div>
                                )}
                              </div>
                            </div>
                            <div className="flex gap-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  try {
                                    navigate(`/projects/${projectId}/ui-test/results/${execution.id}`)
                                  } catch (err) {
                                    console.error('导航时出错:', err)
                                    alert('导航失败，请刷新页面后重试')
                                  }
                                }}
                              >
                                查看详情
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  try {
                                    handleDeleteExecution(execution.id)
                                  } catch (err) {
                                    console.error('删除执行记录时出错:', err)
                                    alert('删除失败，请刷新页面后重试')
                                  }
                                }}
                                className="text-red-600 hover:text-red-700 hover:bg-red-50"
                              >
                                <Trash2 className="mr-2 h-4 w-4" />
                                删除
                              </Button>
                            </div>
                          </div>
                        </div>
                      )
                    } catch (error) {
                      console.error('渲染执行记录时出错:', error, execution)
                      // 返回一个错误占位符，而不是让整个页面崩溃
                      return (
                        <div
                          key={execution.id || index}
                          className="border border-red-200 rounded-lg p-4 bg-red-50"
                        >
                          <div className="text-sm text-red-600">
                            ⚠️ 渲染执行记录时出错（ID: {execution.id || '未知'}）
                          </div>
                        </div>
                      )
                    }
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

