import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ArrowLeft, Play, Loader2, AlertCircle, FileCode, Beaker, CheckCircle2, XCircle, Code, Terminal } from 'lucide-react'
import { unitTestsApi, projectsApi } from '@/lib/api'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'

export default function UnitTestPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const projectId = id ? parseInt(id, 10) : null

  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [generatedCode, setGeneratedCode] = useState<string>('')
  const [testResult, setTestResult] = useState<any>(null)
  const [logs, setLogs] = useState<string>('')

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

  // 获取源文件列表
  const { data: filesData, isLoading: filesLoading } = useQuery({
    queryKey: ['unit-test-files', projectId],
    queryFn: async () => {
      if (!projectId) throw new Error('无效的项目ID')
      const response = await unitTestsApi.getFiles(projectId)
      return response.data
    },
    enabled: !!projectId,
  })

  // 生成测试变体
  const generateMutation = useMutation({
    mutationFn: async () => {
      if (!projectId || !selectedFile) throw new Error('请选择文件')
      return unitTestsApi.generate(projectId, selectedFile)
    },
    onSuccess: (data) => {
      setGeneratedCode(data.data.test_code)
      setTestResult(null)
      setLogs('✅ 测试用例生成成功，你可以根据需要修改代码。')
    },
    onError: (error: any) => {
      alert('生成失败: ' + (error.response?.data?.detail || error.message))
    }
  })

  // 执行测试变体
  const executeMutation = useMutation({
    mutationFn: async () => {
      if (!projectId || !selectedFile || !generatedCode) throw new Error('缺少必要参数')
      return unitTestsApi.execute(projectId, selectedFile, generatedCode)
    },
    onSuccess: (data) => {
      setTestResult(data.data)
      setLogs(data.data.logs)
    },
    onError: (error: any) => {
      alert('执行失败: ' + (error.response?.data?.detail || error.message))
    }
  })

  return (
    <div className="space-y-6">
      {/* 页头 */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate(`/projects/${id}`)}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Catch2 单元测试</h1>
            <p className="text-gray-500">{project?.name || '加载中...'}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* 左侧文件列表 */}
        <Card className="lg:col-span-3 h-[calc(100vh-200px)] overflow-y-auto">
          <CardHeader>
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <FileCode className="h-4 w-4" />
              源文件列表
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {filesLoading ? (
              <div className="p-4 text-center text-gray-500">加载中...</div>
            ) : (
              <div className="divide-y divide-gray-100">
                {filesData?.files?.map((file: any) => (
                  <button
                    key={file.path}
                    className={`w-full text-left px-4 py-3 text-sm transition-colors hover:bg-gray-50 ${
                      selectedFile === file.path ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-600' : 'text-gray-600'
                    }`}
                    onClick={() => setSelectedFile(file.path)}
                  >
                    <div className="truncate font-medium">{file.name}</div>
                    <div className="text-xs opacity-60 mt-1">{file.path}</div>
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* 右侧主区域 */}
        <div className="lg:col-span-9 space-y-6">
          {/* 操作栏 */}
          <Card>
            <CardContent className="p-4 flex gap-4">
              <Button 
                disabled={!selectedFile || generateMutation.isPending}
                onClick={() => generateMutation.mutate()}
                className="flex-1"
              >
                {generateMutation.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Beaker className="mr-2 h-4 w-4" />
                )}
                生成测试用例
              </Button>
              <Button 
                variant="success"
                disabled={!generatedCode || executeMutation.isPending}
                onClick={() => executeMutation.mutate()}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white"
              >
                {executeMutation.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Play className="mr-2 h-4 w-4" />
                )}
                开始测试
              </Button>
            </CardContent>
          </Card>

          {/* 代码视图 */}
          <Card className="min-h-[400px]">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Code className="h-4 w-4" />
                生成的 Catch2 测试代码
              </CardTitle>
            </CardHeader>
            <CardContent>
              {generatedCode ? (
                <div className="relative">
                  <SyntaxHighlighter
                    language="cpp"
                    style={vscDarkPlus}
                    customStyle={{ borderRadius: '0.5rem', maxHeight: '500px' }}
                  >
                    {generatedCode}
                  </SyntaxHighlighter>
                </div>
              ) : (
                <div className="h-[300px] flex flex-col items-center justify-center text-gray-400 border-2 border-dashed rounded-lg">
                  <Beaker className="h-12 w-12 mb-2 opacity-20" />
                  <p>请先选择一个源文件并点击“生成用例”</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 结果和日志 */}
          {testResult && (
            <div className="space-y-4">
              <Card className={testResult.summary.failed > 0 ? 'border-red-200 bg-red-50' : 'border-green-200 bg-green-50'}>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    {testResult.summary.failed > 0 ? (
                      <XCircle className="text-red-500 h-6 w-6" />
                    ) : (
                      <CheckCircle2 className="text-green-500 h-6 w-6" />
                    )}
                    测试结果摘要
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-4 gap-4 text-center">
                    <div className="p-4 bg-white rounded-lg shadow-sm">
                      <div className="text-2xl font-bold">{testResult.summary.total}</div>
                      <div className="text-xs text-gray-500">总用例</div>
                    </div>
                    <div className="p-4 bg-white rounded-lg shadow-sm">
                      <div className="text-2xl font-bold text-green-600">{testResult.summary.passed}</div>
                      <div className="text-xs text-gray-500">通过</div>
                    </div>
                    <div className="p-4 bg-white rounded-lg shadow-sm">
                      <div className="text-2xl font-bold text-red-600">{testResult.summary.failed}</div>
                      <div className="text-xs text-gray-500">失败</div>
                    </div>
                    <div className="p-4 bg-white rounded-lg shadow-sm">
                      <div className="text-2xl font-bold">
                        {testResult.summary?.assertions?.successes ?? 0} / { (testResult.summary?.assertions?.successes ?? 0) + (testResult.summary?.assertions?.failures ?? 0) }
                      </div>
                      <div className="text-xs text-gray-500">断言通过 / 总数</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* 详细用例与分节列表 */}
              {Array.isArray(testResult.summary?.cases) && testResult.summary.cases.length > 0 && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">用例详情</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {testResult.summary.cases.map((c: any, idx: number) => (
                      <div key={idx} className="border rounded-lg p-3 bg-white">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="font-semibold text-gray-900">{c.name}</div>
                          <div className="text-xs text-gray-500">
                            {c.file ? `${c.file}${c.line ? `:${c.line}` : ''}` : ''}
                          </div>
                        </div>
                        <div className="mt-1 text-xs text-gray-500">
                          标签: {c.tags || '-'}
                        </div>
                        <div className="mt-2 flex gap-4 text-sm">
                          <span className="text-green-600">通过: {c.successes}</span>
                          <span className="text-red-600">失败: {c.failures}</span>
                        </div>
                        {Array.isArray(c.sections) && c.sections.length > 0 && (
                          <div className="mt-3 space-y-1">
                            <div className="text-xs font-medium text-gray-600">Sections</div>
                            {c.sections.map((s: any, si: number) => (
                              <div key={si} className="text-xs bg-gray-50 rounded px-2 py-1 flex flex-wrap justify-between">
                                <span className="font-medium text-gray-800">{s.name}</span>
                                <span className="text-gray-500">{s.file ? `${s.file}${s.line ? `:${s.line}` : ''}` : ''}</span>
                                <span className="text-green-600 ml-2">✔ {s.successes}</span>
                                <span className="text-red-600 ml-2">✖ {s.failures}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {logs && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Terminal className="h-4 w-4" />
                  执行日志
                </CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg text-xs overflow-x-auto whitespace-pre-wrap font-mono max-h-[300px]">
                  {logs}
                </pre>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

