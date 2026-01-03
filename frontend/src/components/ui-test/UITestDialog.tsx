import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Loader2, Play, FileCode, CheckCircle, XCircle } from 'lucide-react'
import { uiTestApi, testCasesApi, type UITestCaseGenerateResponse, type UITestResult } from '@/lib/api'

interface UITestDialogProps {
  open: boolean
  onClose: () => void
  projectId: number
  onTestComplete?: () => void
}

export function UITestDialog({ open, onClose, projectId, onTestComplete }: UITestDialogProps) {
  const navigate = useNavigate()
  const [step, setStep] = useState<'input' | 'generated' | 'executing' | 'result'>('input')
  const [testName, setTestName] = useState('')
  const [testDescription, setTestDescription] = useState('')
  const [generatedTest, setGeneratedTest] = useState<UITestCaseGenerateResponse | null>(null)
  const [executionId, setExecutionId] = useState<number | null>(null)

  // 使用 useCallback 定义 handleClose，确保函数引用稳定
  const handleClose = useCallback(() => {
    setStep('input')
    setTestName('')
    setTestDescription('')
    setGeneratedTest(null)
    setExecutionId(null)
    onClose()
  }, [onClose])

  // 保存测试用例
  const saveTestCaseMutation = useMutation({
    mutationFn: async (testData: UITestCaseGenerateResponse) => {
      return testCasesApi.create({
        project_id: projectId,
        name: testData.name,
        description: testData.description,
        test_type: 'ui',
        test_ir: testData.test_ir,
        priority: 'medium',
        tags: ['ui', 'robot_framework', 'ai_generated']
      })
    },
    onSuccess: (response) => {
      // 跳转到详情页面，并自动进入编辑模式
      navigate(`/projects/${projectId}/ui-test/cases/${response.data.id}?edit=true`)
      handleClose()
      if (onTestComplete) {
        onTestComplete()
      }
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || error.message || '未知错误'
      alert(`保存测试用例失败: ${errorMessage}`)
    }
  })

  // 生成测试用例
  const generateMutation = useMutation({
    mutationFn: async () => {
      return uiTestApi.generateTestCase(projectId, {
        name: testName,
        description: testDescription
      })
    },
    onSuccess: (response) => {
      setGeneratedTest(response.data)
      // 自动保存并跳转到详情页面
      saveTestCaseMutation.mutate(response.data)
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || error.message || '未知错误'
      alert(`生成测试用例失败: ${errorMessage}`)
    }
  })

  // 执行测试
  const executeMutation = useMutation({
    mutationFn: async () => {
      if (!generatedTest) throw new Error('没有生成的测试用例')
      return uiTestApi.executeTest(projectId, {
        name: generatedTest.name,
        description: generatedTest.description,
        robot_script: generatedTest.robot_script
      })
    },
    onSuccess: (response) => {
      setExecutionId(response.data.execution_id)
      setStep('executing')
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || error.message || '未知错误'
      alert(`执行测试失败: ${errorMessage}`)
    }
  })

  // 轮询测试结果（添加超时处理）
  // 使用 useRef 存储轮询开始时间，避免在 refetchInterval 中引用 state 导致 hooks 顺序问题
  const pollStartTimeRef = useRef<number | null>(null)
  
  // 计算是否应该启用查询 - 使用 useMemo 确保值稳定
  const isQueryEnabled = useMemo(() => {
    return !!executionId && step === 'executing'
  }, [executionId, step])
  
  // 使用 useCallback 稳定 refetchInterval 函数引用，避免每次渲染时重新创建
  // 函数内部会检查查询是否启用，确保引用始终稳定
  const refetchIntervalFn = useCallback((query: any) => {
    // 如果查询未启用，不轮询
    if (!isQueryEnabled) {
      return false
    }
    // 如果状态是running，每2秒轮询一次
    // 注意：初始时 query.state.data 可能为 undefined，需要继续轮询
    const data = query.state.data
    if (!data || data.status === 'running') {
      // 检查超时（5分钟）
      if (pollStartTimeRef.current && Date.now() - pollStartTimeRef.current > 5 * 60 * 1000) {
        alert('⚠️ 测试执行超时（超过5分钟）。\n\n可能的原因：\n1. Windows Worker未运行\n2. Worker无法连接到Redis\n3. 测试执行时间过长\n\n解决方案：\n1. 检查Windows Worker是否正在运行\n2. 运行: cd backend && .\\start_worker.ps1\n3. 或运行: python -m app.worker.worker')
        return false
      }
      return 2000
    }
    // 否则停止轮询（completed 或 failed）
    return false
  }, [isQueryEnabled])
  
  // 确保 useQuery 始终被调用，但通过 enabled 控制是否实际执行
  // 这确保了 hooks 的执行顺序始终一致
  // refetchInterval 始终传递同一个函数引用，确保配置稳定
  const { data: testResult, error: testResultError } = useQuery<UITestResult>({
    queryKey: ['ui-test-result', projectId, executionId],
    queryFn: async () => {
      if (!executionId) throw new Error('无执行ID')
      const response = await uiTestApi.getTestResult(projectId, executionId)
      return response.data
    },
    enabled: isQueryEnabled,
    refetchInterval: refetchIntervalFn
  })

  // 当开始执行时，记录轮询开始时间
  useEffect(() => {
    if (executionId && step === 'executing') {
      pollStartTimeRef.current = Date.now()
    } else {
      pollStartTimeRef.current = null
    }
  }, [executionId, step])

  // 监听测试结果状态变化
  useEffect(() => {
    if (testResult && testResult.status !== 'running') {
      setStep('result')
      // 如果测试完成，通知父组件刷新执行列表
      if (onTestComplete) {
        onTestComplete()
      }
    }
  }, [testResult, onTestComplete])

  const handleGenerate = () => {
    if (!testName.trim() || !testDescription.trim()) {
      alert('请填写测试用例名称和描述')
      return
    }
    generateMutation.mutate()
  }

  const handleExecute = () => {
    executeMutation.mutate()
  }

  const handleComplete = () => {
    if (onTestComplete) {
      onTestComplete()
    }
    handleClose()
  }

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && handleClose()}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>功能测试（使用AI生成测试用例）</DialogTitle>
          <DialogDescription>
            {step === 'input' && '填写测试用例信息，AI将自动生成Robot Framework脚本'}
            {step === 'generated' && '查看生成的测试脚本，点击执行按钮开始测试'}
            {step === 'executing' && '测试执行中，请稍候...'}
            {step === 'result' && '测试执行完成'}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* 步骤1: 输入测试信息 */}
          {step === 'input' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  测试用例名称 *
                </label>
                <input
                  type="text"
                  value={testName}
                  onChange={(e) => setTestName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="例如：登录功能测试"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  测试描述 *
                </label>
                <textarea
                  value={testDescription}
                  onChange={(e) => setTestDescription(e.target.value)}
                  rows={6}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="详细描述测试场景和步骤，例如：&#10;1. 打开登录页面&#10;2. 输入用户名和密码&#10;3. 点击登录按钮&#10;4. 验证登录成功"
                />
              </div>

              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={handleClose}>
                  取消
                </Button>
                <Button
                  onClick={handleGenerate}
                  disabled={generateMutation.isPending || !testName.trim() || !testDescription.trim()}
                >
                  {generateMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      生成中...
                    </>
                  ) : (
                    <>
                      <FileCode className="mr-2 h-4 w-4" />
                      生成测试用例
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}

          {/* 步骤2: 显示生成的脚本（已移除，直接跳转到详情页面） */}
          {step === 'generated' && generatedTest && (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="h-12 w-12 text-primary animate-spin mb-4" />
              <p className="text-lg font-medium text-gray-900">正在保存测试用例...</p>
              <p className="text-sm text-gray-600 mt-2">即将跳转到详情页面</p>
            </div>
          )}

          {/* 步骤3: 执行中 */}
          {step === 'executing' && (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="h-12 w-12 text-primary animate-spin mb-4" />
              <p className="text-lg font-medium text-gray-900">测试执行中...</p>
              <p className="text-sm text-gray-600 mt-2">请稍候，这可能需要几分钟时间</p>
            </div>
          )}

          {/* 步骤4: 显示结果 */}
          {step === 'result' && testResult && (
            <div className="space-y-4">
              {/* 测试状态 */}
              <div className="flex items-center gap-2">
                {testResult.passed ? (
                  <>
                    <CheckCircle className="h-6 w-6 text-green-500" />
                    <span className="text-lg font-medium text-green-700">测试通过</span>
                  </>
                ) : (
                  <>
                    <XCircle className="h-6 w-6 text-red-500" />
                    <span className="text-lg font-medium text-red-700">测试失败</span>
                  </>
                )}
              </div>

              {/* 执行信息 */}
              {testResult.duration_seconds && (
                <div>
                  <span className="text-sm font-medium text-gray-700">执行时长：</span>
                  <span className="text-sm text-gray-600">{testResult.duration_seconds.toFixed(2)} 秒</span>
                </div>
              )}

              {/* 错误信息 */}
              {testResult.error_message && (
                <div>
                  <h3 className="text-sm font-medium text-red-700 mb-2">错误信息</h3>
                  <div className="bg-red-50 border border-red-200 rounded-md p-3">
                    <p className="text-sm text-red-800 whitespace-pre-wrap">{testResult.error_message}</p>
                  </div>
                </div>
              )}

              {/* 测试日志 */}
              {testResult.logs && (
                <div>
                  <h3 className="text-sm font-medium text-gray-900 mb-2">测试日志</h3>
                  <div className="bg-gray-900 text-gray-100 p-4 rounded-md overflow-x-auto max-h-96">
                    <pre className="text-xs">
                      <code>{testResult.logs}</code>
                    </pre>
                  </div>
                </div>
              )}

              {/* 生成的文件 */}
              {testResult.artifacts && testResult.artifacts.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-900 mb-2">生成的文件</h3>
                  <div className="space-y-2">
                    {testResult.artifacts.map((artifact, index) => (
                      <div key={index} className="flex items-center gap-2 text-sm">
                        <FileCode className="h-4 w-4 text-gray-500" />
                        <span className="text-gray-700">{artifact.name || artifact.path}</span>
                        <span className="text-gray-500">({artifact.type})</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex justify-end gap-2">
                <Button onClick={handleComplete}>
                  完成
                </Button>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

