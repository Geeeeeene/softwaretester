import { useState, useEffect } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { ArrowLeft, Save, Loader2, Play, Sparkles, X } from 'lucide-react'
import { testCasesApi, uiTestApi } from '@/lib/api'
// import { useToast } from '@/hooks/use-toast'

export default function UITestCaseDetailPage() {
  const { id, testCaseId } = useParams<{ id: string; testCaseId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  // const { toast } = useToast()
  const projectId = id ? parseInt(id, 10) : null
  const caseId = testCaseId ? parseInt(testCaseId, 10) : null

  const [description, setDescription] = useState('')
  const [robotScript, setRobotScript] = useState('')
  const [scriptSource, setScriptSource] = useState<'ai' | 'manual'>('ai') // AI生成或直接编写
  const [isEditing, setIsEditing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isSaved, setIsSaved] = useState(false) // 是否已保存
  const [isGenerating, setIsGenerating] = useState(false) // 是否正在生成脚本

  // 获取测试用例详情
  const { data: testCase, isLoading, error } = useQuery({
    queryKey: ['test-case', caseId],
    queryFn: async () => {
      if (!caseId) throw new Error('无效的测试用例ID')
      const response = await testCasesApi.get(caseId)
      return response.data
    },
    enabled: !!caseId,
  })

  // 当测试用例加载后，初始化编辑状态
  useEffect(() => {
    if (testCase) {
      setDescription(testCase.description || '')
      setRobotScript(testCase.test_ir?.robot_script || '')
      // 检查URL参数，如果包含edit=true，自动进入编辑模式
      if (searchParams.get('edit') === 'true') {
        setIsEditing(true)
        // 移除URL参数
        setSearchParams({}, { replace: true })
      }
    }
  }, [testCase, searchParams, setSearchParams])

  // AI生成脚本
  const generateScriptMutation = useMutation({
    mutationFn: async () => {
      if (!testCase) throw new Error('测试用例不存在')
      return uiTestApi.generateTestCase(projectId!, {
        name: testCase.name,
        description: description || testCase.description || ''
      })
    },
    onSuccess: (response) => {
      setRobotScript(response.data.robot_script)
      setScriptSource('ai')
      alert('AI生成脚本成功')
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || error.message || '未知错误'
      alert(`AI生成脚本失败: ${errorMessage}`)
    }
  })

  // 保存修改
  const handleSave = async () => {
    if (!caseId || !testCase) return

    setIsSaving(true)
    try {
      // 更新test_ir中的robot_script
      const updatedTestIr = {
        ...testCase.test_ir,
        robot_script: robotScript,
        description: description,
      }

      await testCasesApi.update(caseId, {
        description: description,
        test_ir: updatedTestIr,
      })

      // 刷新查询缓存
      queryClient.invalidateQueries({ queryKey: ['test-case', caseId] })
      queryClient.invalidateQueries({ queryKey: ['ui-test-cases', projectId] })

      alert('保存成功：测试用例已更新')
      setIsSaved(true) // 标记为已保存
      setIsEditing(false)
    } catch (error: any) {
      console.error('保存失败:', error)
      alert(`保存失败: ${error.response?.data?.detail || error.message || '未知错误'}`)
    } finally {
      setIsSaving(false)
    }
  }

  // 执行测试
  const executeMutation = useMutation({
    mutationFn: async () => {
      if (!testCase) throw new Error('测试用例不存在')
      return uiTestApi.executeTest(projectId!, {
        name: testCase.name,
        description: description || testCase.description || '',
        robot_script: robotScript
      })
    },
    onSuccess: (response) => {
      // 跳转到执行结果页面或刷新执行列表
      navigate(`/projects/${projectId}/system-test/results/${response.data.execution_id}`)
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || error.message || '未知错误'
      alert(`执行测试失败: ${errorMessage}`)
    }
  })

  // 取消编辑
  const handleCancel = () => {
    if (testCase) {
      setDescription(testCase.description || '')
      setRobotScript(testCase.test_ir?.robot_script || '')
    }
    setIsEditing(false)
    setIsSaved(false) // 重置保存状态
  }

  // 处理AI生成脚本
  const handleGenerateScript = () => {
    setIsGenerating(true)
    generateScriptMutation.mutate()
    setTimeout(() => setIsGenerating(false), 1000)
  }

  if (!caseId) {
    return (
      <div className="text-center py-12">
        <p className="text-red-500">无效的测试用例ID</p>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="h-8 w-8 text-gray-400 animate-spin" />
      </div>
    )
  }

  if (error || !testCase) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-500 mb-4">加载测试用例失败</p>
          <Button onClick={() => navigate(`/projects/${projectId}/system-test`)}>
            返回
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部工具栏 */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={() => navigate(`/projects/${projectId}/system-test`)}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              返回
            </Button>
            <div>
              <h1 className="text-xl font-bold text-gray-900">{testCase.name}</h1>
              <p className="text-sm text-gray-600 mt-1">测试用例详情</p>
            </div>
          </div>
          <div className="flex gap-2">
            {isEditing ? (
              <>
                <Button
                  variant="outline"
                  onClick={handleCancel}
                  disabled={isSaving}
                >
                  取消
                </Button>
                <Button
                  onClick={handleSave}
                  disabled={isSaving}
                >
                  {isSaving ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      保存中...
                    </>
                  ) : (
                    <>
                      <Save className="mr-2 h-4 w-4" />
                      保存
                    </>
                  )}
                </Button>
              </>
            ) : (
              <Button onClick={() => setIsEditing(true)}>
                <Save className="mr-2 h-4 w-4" />
                编辑
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* 内容区域 */}
      <div className="p-6 max-w-7xl mx-auto pb-24">
        <div className="space-y-6">
          {/* 基本信息 */}
          <Card>
            <CardHeader>
              <CardTitle>基本信息</CardTitle>
              <CardDescription>测试用例的基本信息</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>测试用例名称</Label>
                <div className="mt-1 text-sm text-gray-900 font-medium">{testCase.name}</div>
              </div>
              <div>
                <Label>测试类型</Label>
                <div className="mt-1 text-sm text-gray-900">{testCase.test_type}</div>
              </div>
              <div>
                <Label>优先级</Label>
                <div className="mt-1 text-sm text-gray-900">{testCase.priority}</div>
              </div>
              <div>
                <Label>创建时间</Label>
                <div className="mt-1 text-sm text-gray-600">
                  {new Date(testCase.created_at).toLocaleString('zh-CN')}
                </div>
              </div>
              {testCase.updated_at && (
                <div>
                  <Label>更新时间</Label>
                  <div className="mt-1 text-sm text-gray-600">
                    {new Date(testCase.updated_at).toLocaleString('zh-CN')}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 测试描述 */}
          <Card>
            <CardHeader>
              <CardTitle>测试描述</CardTitle>
              <CardDescription>测试用例的详细描述</CardDescription>
            </CardHeader>
            <CardContent>
              {isEditing ? (
                <div className="space-y-2">
                  <Label htmlFor="description">描述</Label>
                  <Textarea
                    id="description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    rows={6}
                    className="font-mono text-sm"
                    placeholder="请输入测试用例的描述..."
                  />
                </div>
              ) : (
                <div className="text-sm text-gray-700 whitespace-pre-wrap">
                  {description || <span className="text-gray-400">暂无描述</span>}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Robot Framework脚本 */}
          <Card>
            <CardHeader>
              <CardTitle>Robot Framework脚本</CardTitle>
              <CardDescription>AI生成的测试脚本，可以手动修改</CardDescription>
            </CardHeader>
            <CardContent>
              {isEditing ? (
                <div className="space-y-4">
                  {/* 脚本来源选择 */}
                  <div className="space-y-2">
                    <Label>脚本来源</Label>
                    <div className="flex gap-2">
                      <Button
                        type="button"
                        variant={scriptSource === 'ai' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setScriptSource('ai')}
                      >
                        使用AI生成脚本
                      </Button>
                      <Button
                        type="button"
                        variant={scriptSource === 'manual' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setScriptSource('manual')}
                      >
                        直接编写脚本
                      </Button>
                    </div>
                  </div>

                  {/* 脚本编辑区域 */}
                  <div className="space-y-2">
                    <Label htmlFor="robot-script">脚本内容</Label>
                    <Textarea
                      id="robot-script"
                      value={robotScript}
                      onChange={(e) => setRobotScript(e.target.value)}
                      rows={30}
                      className="font-mono text-sm"
                      placeholder="Robot Framework脚本内容..."
                    />
                    <p className="text-xs text-gray-500 mt-2">
                      提示：修改脚本后，请确保语法正确，否则执行时可能会失败。
                    </p>
                  </div>

                  {/* 脚本编辑区域右下角按钮 */}
                  <div className="flex justify-end gap-2 pt-2 border-t">
                    <Button
                      variant="outline"
                      onClick={handleCancel}
                      disabled={isSaving}
                    >
                      <X className="mr-2 h-4 w-4" />
                      取消
                    </Button>
                    <Button
                      variant="outline"
                      onClick={handleGenerateScript}
                      disabled={isSaving || isGenerating || generateScriptMutation.isPending}
                    >
                      {isGenerating || generateScriptMutation.isPending ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          生成中...
                        </>
                      ) : (
                        <>
                          <Sparkles className="mr-2 h-4 w-4" />
                          AI生成
                        </>
                      )}
                    </Button>
                    <Button
                      onClick={handleSave}
                      disabled={isSaving}
                    >
                      {isSaving ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          保存中...
                        </>
                      ) : (
                        <>
                          <Save className="mr-2 h-4 w-4" />
                          保存
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
                    <pre className="text-sm font-mono whitespace-pre-wrap">
                      {robotScript || <span className="text-gray-400">暂无脚本</span>}
                    </pre>
                  </div>
                  <p className="text-xs text-gray-500">
                    点击"编辑"按钮可以修改脚本内容
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* 底部固定执行按钮 */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 px-6 py-4 shadow-lg z-10">
        <div className="max-w-7xl mx-auto flex justify-end">
          <Button
            onClick={() => executeMutation.mutate()}
            disabled={!isSaved || executeMutation.isPending || !robotScript.trim()}
            size="lg"
            className={!isSaved ? 'opacity-50 cursor-not-allowed' : ''}
          >
            {executeMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                执行中...
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                执行
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}

