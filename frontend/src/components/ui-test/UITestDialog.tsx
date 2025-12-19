import { useState, useEffect } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Loader2, Play, FileCode, CheckCircle, XCircle } from 'lucide-react'
import { uiTestApi, type UITestCaseGenerateResponse, type UITestResult } from '@/lib/api'

interface UITestDialogProps {
  open: boolean
  onClose: () => void
  projectId: number
  onTestComplete?: () => void
}

export function UITestDialog({ open, onClose, projectId, onTestComplete }: UITestDialogProps) {
  const [step, setStep] = useState<'input' | 'generated' | 'executing' | 'result'>('input')
  const [testName, setTestName] = useState('')
  const [testDescription, setTestDescription] = useState('')
  const [generatedTest, setGeneratedTest] = useState<UITestCaseGenerateResponse | null>(null)
  const [executionId, setExecutionId] = useState<number | null>(null)

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
      setStep('generated')
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

  // 轮询测试结果
  const { data: testResult } = useQuery<UITestResult>({
    queryKey: ['ui-test-result', projectId, executionId],
    queryFn: async () => {
      if (!executionId) throw new Error('无执行ID')
      const response = await uiTestApi.getTestResult(projectId, executionId)
      return response.data
    },
    enabled: !!executionId && step === 'executing',
    refetchInterval: (query) => {
      // 如果状态是running，每2秒轮询一次
      // 注意：初始时 query.state.data 可能为 undefined，需要继续轮询
      const data = query.state.data
      if (!data || data.status === 'running') {
        return 2000
      }
      // 否则停止轮询（completed 或 failed）
      return false
    }
  })

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

  const handleClose = () => {
    setStep('input')
    setTestName('')
    setTestDescription('')
    setGeneratedTest(null)
    setExecutionId(null)
    onClose()
  }

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
          <DialogTitle>UI测试（使用AI生成测试用例）</DialogTitle>
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

          {/* 步骤2: 显示生成的脚本 */}
          {step === 'generated' && generatedTest && (
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-2">测试用例名称</h3>
                <p className="text-sm text-gray-700">{generatedTest.name}</p>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-2">测试描述</h3>
                <p className="text-sm text-gray-700 whitespace-pre-wrap">{generatedTest.description}</p>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-2">Robot Framework 脚本</h3>
                <div className="bg-gray-900 text-gray-100 p-4 rounded-md overflow-x-auto">
                  <pre className="text-sm">
                    <code>{generatedTest.robot_script}</code>
                  </pre>
                </div>
              </div>

              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={handleClose}>
                  取消
                </Button>
                <Button
                  onClick={handleExecute}
                  disabled={executeMutation.isPending}
                >
                  {executeMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      启动中...
                    </>
                  ) : (
                    <>
                      <Play className="mr-2 h-4 w-4" />
                      执行UI测试
                    </>
                  )}
                </Button>
              </div>
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

