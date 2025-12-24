import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ArrowLeft, Loader2, AlertCircle, FileCode, Beaker, Code, Terminal, Upload } from 'lucide-react'
import { integrationTestsApi, projectsApi, uploadApi } from '@/lib/api'
import { FileTree } from '@/components/static-analysis/FileTree'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'

export default function IntegrationTestPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const projectId = id ? parseInt(id, 10) : null

  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [generatedCode, setGeneratedCode] = useState<string>('')
  const [testResult, setTestResult] = useState<any>(null)
  const [logs, setLogs] = useState<string>('')
  const [aiAnalysis, setAiAnalysis] = useState<string>('')

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

  // 获取源文件列表（文件树）
  const { data: filesData, isLoading: filesLoading, refetch: refetchFiles, error: filesError } = useQuery({
    queryKey: ['integration-test-files', projectId],
    queryFn: async () => {
      if (!projectId) throw new Error('无效的项目ID')
      const response = await integrationTestsApi.getFiles(projectId)
      return response.data
    },
    enabled: !!projectId,
    retry: 1, // 只重试一次
  })

  // 当项目信息加载完成后，刷新文件列表
  useEffect(() => {
    if (project && projectId) {
      // 延迟一下，确保后端已经处理完文件上传
      const timer = setTimeout(() => {
        refetchFiles()
      }, 500)
      return () => clearTimeout(timer)
    }
  }, [project, projectId, refetchFiles])

  // 文件上传
  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      if (!projectId) throw new Error('无效的项目ID')
      if (!file.name.toLowerCase().endsWith('.zip')) {
        throw new Error('请上传ZIP格式的压缩包')
      }
      return uploadApi.uploadProjectSource(projectId, file, true)
    },
    onSuccess: (data) => {
      console.log('上传成功:', data)
      alert('文件上传成功！正在刷新文件列表...')
      // 延迟一下，确保后端已经处理完文件解压和数据库更新
      setTimeout(() => {
        refetchFiles()
      }, 1500)
    },
    onError: (error: any) => {
      const errorMsg = error.response?.data?.detail || error.message || '上传失败'
      alert('上传失败: ' + errorMsg)
      console.error('上传错误:', error)
    }
  })

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      uploadMutation.mutate(file)
    }
  }

  // 生成并执行集成测试（一步完成）- 分析整个项目
  const generateAndExecuteMutation = useMutation({
    mutationFn: async () => {
      if (!projectId) throw new Error('项目ID无效')
      // 不传file_path，表示分析整个项目
      return integrationTestsApi.generateAndExecute(projectId, undefined)
    },
    onSuccess: (data) => {
      setGeneratedCode(data.data.test_code)
      setTestResult(data.data.execution_result)
      setLogs(data.data.logs || '测试执行完成')
      setAiAnalysis(data.data.ai_analysis || '')  // 设置AI分析结果
      if (data.data.success) {
        alert('✅ 测试用例生成并执行成功！AI已分析结果，请查看下方详细信息。')
      } else {
        alert('⚠️ 测试用例已生成。AI已分析原因，请查看下方详细结果。')
      }
    },
    onError: (error: any) => {
      const errorMsg = error.response?.data?.detail || error.message || '生成或执行失败'
      alert('生成或执行失败: ' + errorMsg)
      setLogs('❌ 生成或执行失败: ' + errorMsg + '\n\n请检查：\n1. 测试代码是否正确\n2. 源代码路径是否存在')
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
            <h1 className="text-2xl font-bold text-gray-900">Catch2 集成测试</h1>
            <p className="text-gray-500">{project?.name || '加载中...'}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <label className="cursor-pointer">
            <input
              type="file"
              className="hidden"
              onChange={handleFileUpload}
              accept=".zip,.tar,.gz"
            />
            <Button variant="outline" disabled={uploadMutation.isPending}>
              <Upload className="mr-2 h-4 w-4" />
              {uploadMutation.isPending ? '上传中...' : '上传源代码'}
            </Button>
          </label>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* 左侧文件树 */}
        <Card className="lg:col-span-3 h-[calc(100vh-200px)] flex flex-col">
          <CardHeader>
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <FileCode className="h-4 w-4" />
              源文件列表
            </CardTitle>
            <CardDescription className="text-xs">
              选择文件后，AI将分析代码并生成集成测试用例
            </CardDescription>
          </CardHeader>
          <CardContent className="flex-1 p-0 overflow-hidden">
            {filesLoading ? (
              <div className="p-4 text-center text-gray-500">
                <Loader2 className="h-6 w-6 mx-auto mb-2 animate-spin text-gray-400" />
                加载中...
              </div>
            ) : filesError ? (
              <div className="p-4 text-center text-gray-500">
                <AlertCircle className="h-8 w-8 mx-auto mb-2 text-yellow-500" />
                <p className="text-sm text-yellow-600">加载文件列表失败</p>
                <p className="text-xs mt-1 text-gray-500">
                  {(filesError as any)?.response?.data?.detail || '未找到源代码文件夹，请先上传源代码'}
                </p>
                <Button
                  size="sm"
                  variant="outline"
                  className="mt-2"
                  onClick={() => refetchFiles()}
                >
                  重试
                </Button>
              </div>
            ) : !filesData?.file_tree || filesData.file_tree.length === 0 ? (
              <div className="p-4 text-center text-gray-500">
                <AlertCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">暂无源文件</p>
                <p className="text-xs mt-1">请先上传源代码</p>
                <Button
                  size="sm"
                  variant="outline"
                  className="mt-2"
                  onClick={() => refetchFiles()}
                >
                  刷新列表
                </Button>
              </div>
            ) : (
              <div className="h-full overflow-hidden">
                <FileTree
                  tree={filesData.file_tree}
                  selectedPath={selectedFile || undefined}
                  onFileSelect={(path) => {
                    setSelectedFile(path)
                    setGeneratedCode('') // 清除之前的测试代码
                    setTestResult(null) // 清除之前的测试结果
                    setLogs('') // 清除之前的日志
                  }}
                  showTitle={false}
                />
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
                disabled={generateAndExecuteMutation.isPending}
                onClick={() => {
                  // 不传file_path，表示分析整个项目
                  generateAndExecuteMutation.mutate()
                }}
                className="flex-1"
                title="AI将分析整个项目，生成测试用例并自动执行"
              >
                {generateAndExecuteMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    AI分析整个项目并执行中...
                  </>
                ) : (
                  <>
                    <Beaker className="mr-2 h-4 w-4" />
                    分析整个项目并执行测试
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* 代码视图 */}
          <Card className="min-h-[400px]">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Code className="h-4 w-4" />
                生成的 Catch2 集成测试代码
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
                  <p className="text-xs mt-2 opacity-60">AI将分析代码并生成集成测试用例</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 结果和日志 */}
          {testResult && (
            <div className="space-y-4">
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
                <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg text-xs overflow-x-auto whitespace-pre-wrap font-mono max-h-[300px] overflow-y-auto">
                  {logs}
                </pre>
              </CardContent>
            </Card>
          )}

          {aiAnalysis && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Beaker className="h-4 w-4" />
                  AI 分析结果
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="prose prose-sm max-w-none">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm whitespace-pre-wrap">
                    {aiAnalysis}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
