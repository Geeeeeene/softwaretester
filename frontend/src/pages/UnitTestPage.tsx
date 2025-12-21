import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ArrowLeft, Play, Loader2, FileCode, Beaker, CheckCircle2, XCircle, Code, Terminal, Save, Upload, FileText, ChevronDown, ChevronUp } from 'lucide-react'
import { unitTestsApi, projectsApi } from '@/lib/api'

export default function UnitTestPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const projectId = id ? parseInt(id, 10) : null

  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const prevSelectedFileRef = useRef<string | null>(null)
  
  // 为每个文件维护独立的状态
  interface FileState {
    generatedCode: string
    testResult: any
    logs: string
    isEditing: boolean
  }
  const [fileStates, setFileStates] = useState<Record<string, FileState>>({})
  
  const [generatedCode, setGeneratedCode] = useState<string>('')
  const [testResult, setTestResult] = useState<any>(null)
  const [logs, setLogs] = useState<string>('')
  const [isEditing, setIsEditing] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false) // 防止生成后触发加载
  const [docSummary, setDocSummary] = useState<string | null>(null)
  const [hasDocSummary, setHasDocSummary] = useState(false)
  const [showDocSummary, setShowDocSummary] = useState(false) // 控制文档要点显示
  const [isEditingDocSummary, setIsEditingDocSummary] = useState(false) // 是否正在编辑文档要点
  const [editedDocSummary, setEditedDocSummary] = useState<string>('') // 编辑中的文档要点
  
  // 项目级别的测试统计（累计所有文件的测试结果）
  interface ProjectTestStats {
    total: number      // 总用例数
    passed: number     // 通过的用例数
    failed: number     // 失败的用例数
    assertionsSuccesses: number  // 通过的断言数
    assertionsTotal: number      // 总断言数
  }
  const [projectStats, setProjectStats] = useState<ProjectTestStats>({
    total: 0,
    passed: 0,
    failed: 0,
    assertionsSuccesses: 0,
    assertionsTotal: 0
  })
  
  // 跟踪每个文件stem（不含扩展名）的最新测试结果，避免.h和.cpp重复统计
  const [, setStemTestResults] = useState<Record<string, any>>({})

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

  // 获取文档要点
  const { data: docSummaryData, refetch: refetchDocSummary } = useQuery({
    queryKey: ['document-summary', projectId],
    queryFn: async () => {
      if (!projectId) throw new Error('无效的项目ID')
      const response = await unitTestsApi.getDocumentSummary(projectId)
      return response.data
    },
    enabled: !!projectId,
  })

  // 当文档要点数据更新时，更新状态
  useEffect(() => {
    if (docSummaryData) {
      setDocSummary(docSummaryData.summary)
      setEditedDocSummary(docSummaryData.summary || '')
      setHasDocSummary(docSummaryData.has_summary)
    }
  }, [docSummaryData])

  // 当selectedFile改变时，保存当前状态并恢复新文件状态
  useEffect(() => {
    if (!projectId) return
    
    const prevFile = prevSelectedFileRef.current
    const currentFile = selectedFile
    
    // 如果文件改变了，保存之前文件的状态
    if (prevFile && prevFile !== currentFile) {
      setFileStates(prev => ({
        ...prev,
        [prevFile]: {
          generatedCode,
          testResult,
          logs,
          isEditing
        }
      }))
    }
    
    // 更新ref（在恢复状态之前）
    prevSelectedFileRef.current = currentFile
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedFile, projectId, generatedCode, testResult, logs, isEditing])
  
  // 单独处理状态恢复
  useEffect(() => {
    if (!selectedFile || !projectId) {
      if (!selectedFile) {
        setGeneratedCode('')
        setTestResult(null)
        setLogs('')
        setIsEditing(false)
      }
      return
    }
    
    const savedState = fileStates[selectedFile]
    if (savedState) {
      // 有保存的状态，恢复它
      setGeneratedCode(savedState.generatedCode)
      setTestResult(savedState.testResult)
      setLogs(savedState.logs)
      setIsEditing(savedState.isEditing)
    } else {
      // 没有保存的状态，重置为空，然后尝试从文件系统加载
      setGeneratedCode('')
      setTestResult(null)
      setLogs('')
      setIsEditing(false)
      
      // 异步加载测试文件
      if (!isGenerating && projectId) {
        unitTestsApi.getTestFile(projectId, selectedFile)
          .then(response => {
            setGeneratedCode(response.data.test_code)
            setIsEditing(false)
            setLogs('✅ 已加载测试文件')
            // 保存到状态
            setFileStates(prevState => ({
              ...prevState,
              [selectedFile]: {
                generatedCode: response.data.test_code,
                testResult: prevState[selectedFile]?.testResult || null, // 保留之前的测试结果
                logs: '✅ 已加载测试文件',
                isEditing: false
              }
            }))
          })
          .catch((error: any) => {
            if (error.response?.status !== 404) {
              console.error('加载测试文件失败:', error)
            }
          })
      }
    }
  }, [selectedFile, projectId, fileStates, isGenerating])

  // 生成测试变体
  const generateMutation = useMutation({
    mutationFn: async () => {
      if (!projectId || !selectedFile) throw new Error('请选择文件')
      setIsGenerating(true)
      return unitTestsApi.generate(projectId, selectedFile)
    },
    onSuccess: (data) => {
      if (!selectedFile) return
      setGeneratedCode(data.data.test_code)
      setTestResult(null)
      setLogs(`✅ 测试用例生成成功，已保存到文件。你可以根据需要修改代码。`)
      setIsEditing(false) // 刚生成的代码视为未编辑（已自动保存）
      setIsGenerating(false)
      
      // 保存到文件状态
      setFileStates(prev => ({
        ...prev,
        [selectedFile]: {
          generatedCode: data.data.test_code,
          testResult: null,
          logs: `✅ 测试用例生成成功，已保存到文件。你可以根据需要修改代码。`,
          isEditing: false
        }
      }))
    },
    onError: (error: any) => {
      setIsGenerating(false)
      alert('生成失败: ' + (error.response?.data?.detail || error.message))
    }
  })

  // 加载测试文件
  const loadTestFile = useCallback(async () => {
    if (!projectId || !selectedFile) return
    try {
      const response = await unitTestsApi.getTestFile(projectId, selectedFile)
      setGeneratedCode(response.data.test_code)
      setIsEditing(false) // 加载的文件视为未编辑状态
      setLogs('✅ 已加载测试文件')
      
      // 保存到文件状态
      setFileStates(prev => ({
        ...prev,
        [selectedFile]: {
          generatedCode: response.data.test_code,
          testResult: prev[selectedFile]?.testResult || null, // 保留之前的测试结果
          logs: '✅ 已加载测试文件',
          isEditing: false
        }
      }))
    } catch (error: any) {
      if (error.response?.status !== 404) {
        alert('加载测试文件失败: ' + (error.response?.data?.detail || error.message))
      }
    }
  }, [projectId, selectedFile])

  // 保存测试文件
  const saveTestFileMutation = useMutation({
    mutationFn: async () => {
      if (!projectId || !selectedFile || !generatedCode) throw new Error('缺少必要参数')
      console.log('保存测试文件:', { projectId, selectedFile, codeLength: generatedCode.length })
      return unitTestsApi.updateTestFile(projectId, selectedFile, generatedCode)
    },
    onSuccess: (data) => {
      setLogs(`✅ 测试文件已保存到: ${data.data.test_file_path}`)
      setIsEditing(false) // 保存后重置编辑状态
    },
    onError: (error: any) => {
      const errorMsg = error.response?.data?.detail || error.message
      console.error('保存失败:', error)
      alert(`保存失败: ${errorMsg}\n\n请检查后端日志查看详细错误信息。`)
    }
  })

  // 当选择文件改变时，尝试加载测试文件（但不在生成过程中加载，且该文件没有保存的状态）
  useEffect(() => {
    if (selectedFile && projectId && !isGenerating && !fileStates[selectedFile]) {
      loadTestFile()
    }
  }, [selectedFile, projectId, loadTestFile, isGenerating, fileStates])

  // 上传文档
  const uploadDocumentMutation = useMutation({
    mutationFn: async (file: File) => {
      if (!projectId) throw new Error('无效的项目ID')
      return unitTestsApi.uploadDocument(projectId, file)
    },
    onSuccess: (data) => {
      setDocSummary(data.data.summary)
      setEditedDocSummary(data.data.summary)
      setHasDocSummary(true)
      setLogs(`✅ 文档上传成功！已分析并保存要点。`)
      refetchDocSummary()
    },
    onError: (error: any) => {
      alert('文档上传失败: ' + (error.response?.data?.detail || error.message))
    }
  })

  // 保存文档要点
  const saveDocSummaryMutation = useMutation({
    mutationFn: async (summary: string) => {
      if (!projectId) throw new Error('无效的项目ID')
      return unitTestsApi.updateDocumentSummary(projectId, summary)
    },
    onSuccess: (data) => {
      setDocSummary(data.data.summary)
      setEditedDocSummary(data.data.summary)
      setIsEditingDocSummary(false)
      setLogs(`✅ 文档要点已保存`)
      refetchDocSummary()
    },
    onError: (error: any) => {
      alert('保存文档要点失败: ' + (error.response?.data?.detail || error.message))
    }
  })

  // 处理文档上传
  const handleDocumentUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    
    if (!file.name.toLowerCase().endsWith('.docx')) {
      alert('只支持 .docx 格式的文档')
      return
    }
    
    uploadDocumentMutation.mutate(file)
    // 清空input，允许重复上传同一文件
    event.target.value = ''
  }

  // 执行测试变体（不传testCode，让后端从文件读取）
  const executeMutation = useMutation({
    mutationFn: async () => {
      if (!projectId || !selectedFile) throw new Error('缺少必要参数')
      // 先保存当前编辑的代码（如果有修改）
      if (isEditing && generatedCode) {
        try {
          await saveTestFileMutation.mutateAsync()
        } catch (error: any) {
          // 如果保存失败，仍然尝试执行（使用当前内存中的代码）
          console.warn('保存失败，将使用内存中的代码执行:', error)
          return unitTestsApi.execute(projectId, selectedFile, generatedCode)
        }
      }
      // 不传testCode，让后端从文件读取
      return unitTestsApi.execute(projectId, selectedFile)
    },
    onSuccess: (data) => {
      if (!selectedFile) return
      setTestResult(data.data)
      setLogs(data.data.logs)
      
      // 保存测试结果到文件状态，并更新项目统计
      setFileStates(prev => {
        // 更新文件状态
        const newFileState = {
          ...prev[selectedFile],
          testResult: data.data,
          logs: data.data.logs,
          generatedCode: prev[selectedFile]?.generatedCode || generatedCode
        }
        
        // 更新项目级别的统计（累加）
        // 使用文件stem（不含扩展名）作为统计键，避免.h和.cpp文件重复计算
        if (data.data?.summary) {
          const summary = data.data.summary
          
          // 获取文件stem（不含扩展名），例如 "example.h" -> "example"
          const getFileStem = (filePath: string) => {
            const pathParts = filePath.split(/[/\\]/)
            const fileName = pathParts[pathParts.length - 1]
            const lastDotIndex = fileName.lastIndexOf('.')
            return lastDotIndex > 0 ? fileName.substring(0, lastDotIndex) : fileName
          }
          
          const fileStem = getFileStem(selectedFile)
          
          // 获取这个stem之前的测试结果（如果有）
          setStemTestResults(prevStemResults => {
            const prevStemResult = prevStemResults[fileStem]
            const prevStemSummary = prevStemResult?.summary
            
            // 计算增量（新结果 - 旧结果）
            // 如果这是第一次测试这个stem的文件，增量就是新结果
            // 如果之前测试过相同stem的其他文件，增量就是新结果减去旧结果
            const deltaTotal = (summary.total || 0) - (prevStemSummary?.total || 0)
            const deltaPassed = (summary.passed || 0) - (prevStemSummary?.passed || 0)
            const deltaFailed = (summary.failed || 0) - (prevStemSummary?.failed || 0)
            const deltaAssertionsSuccesses = (summary.assertions?.successes || 0) - (prevStemSummary?.assertions?.successes || 0)
            const deltaAssertionsTotal = ((summary.assertions?.successes || 0) + (summary.assertions?.failures || 0)) - 
                                         ((prevStemSummary?.assertions?.successes || 0) + (prevStemSummary?.assertions?.failures || 0))
            
            // 更新项目统计
            setProjectStats(prevStats => ({
              total: prevStats.total + deltaTotal,
              passed: prevStats.passed + deltaPassed,
              failed: prevStats.failed + deltaFailed,
              assertionsSuccesses: prevStats.assertionsSuccesses + deltaAssertionsSuccesses,
              assertionsTotal: prevStats.assertionsTotal + deltaAssertionsTotal
            }))
            
            // 更新stem测试结果记录（使用最新的测试结果）
            return {
              ...prevStemResults,
              [fileStem]: data.data
            }
          })
        }
        
        return {
          ...prev,
          [selectedFile]: newFileState
        }
      })
    },
    onError: (error: any) => {
      console.error('执行失败:', error)
      const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || '未知错误'
      alert(`执行失败: ${errorMsg}`)
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
        
        <div className="flex items-center gap-4">
          {/* 项目级别测试统计 */}
          <Card className="border-blue-200 bg-blue-50">
            <CardContent className="p-4">
              <div className="flex items-center gap-6">
                <div className="text-center">
                  <div className="text-lg font-bold text-gray-900">{projectStats.total}</div>
                  <div className="text-xs text-gray-500">总用例</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-green-600">{projectStats.passed}</div>
                  <div className="text-xs text-gray-500">通过</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-red-600">{projectStats.failed}</div>
                  <div className="text-xs text-gray-500">失败</div>
                </div>
                {projectStats.assertionsTotal > 0 && (
                  <div className="text-center">
                    <div className="text-lg font-bold">
                      {projectStats.assertionsSuccesses} / {projectStats.assertionsTotal}
                    </div>
                    <div className="text-xs text-gray-500">断言通过/总数</div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
          
          <div className="flex items-center gap-2">
            {hasDocSummary && (
            <div className="text-sm text-green-600 flex items-center gap-1">
              <FileText className="h-4 w-4" />
              <span>已加载设计文档</span>
            </div>
          )}
          <label>
            <input
              type="file"
              accept=".docx"
              onChange={handleDocumentUpload}
              className="hidden"
              disabled={uploadDocumentMutation.isPending}
            />
            <Button
              variant="outline"
              size="sm"
              asChild
              disabled={uploadDocumentMutation.isPending}
            >
              <span>
                {uploadDocumentMutation.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Upload className="mr-2 h-4 w-4" />
                )}
                上传设计文档
              </span>
            </Button>
          </label>
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
          {/* 文档要点显示区域 */}
          {hasDocSummary && docSummary && (
            <Card className="border-blue-200 bg-blue-50/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <FileText className="h-4 w-4 text-blue-600" />
                    设计文档要点
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    {!isEditingDocSummary && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setIsEditingDocSummary(true)
                          setEditedDocSummary(docSummary)
                          setShowDocSummary(true)
                        }}
                      >
                        <Code className="mr-2 h-4 w-4" />
                        编辑
                      </Button>
                    )}
                    <button
                      onClick={() => setShowDocSummary(!showDocSummary)}
                      className="p-1 hover:bg-gray-100 rounded"
                    >
                      {showDocSummary ? (
                        <ChevronUp className="h-4 w-4 text-gray-500" />
                      ) : (
                        <ChevronDown className="h-4 w-4 text-gray-500" />
                      )}
                    </button>
                  </div>
                </div>
              </CardHeader>
              {showDocSummary && (
                <CardContent>
                  {isEditingDocSummary ? (
                    <div className="space-y-3">
                      <textarea
                        value={editedDocSummary}
                        onChange={(e) => setEditedDocSummary(e.target.value)}
                        className="w-full h-[300px] p-4 font-mono text-sm bg-white rounded-lg border border-blue-200 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                        style={{ fontFamily: 'Consolas, Monaco, "Courier New", monospace' }}
                        spellCheck={false}
                      />
                      <div className="flex gap-2 justify-end">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setIsEditingDocSummary(false)
                            setEditedDocSummary(docSummary || '')
                          }}
                        >
                          取消
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => saveDocSummaryMutation.mutate(editedDocSummary)}
                          disabled={saveDocSummaryMutation.isPending}
                        >
                          {saveDocSummaryMutation.isPending ? (
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          ) : (
                            <Save className="mr-2 h-4 w-4" />
                          )}
                          保存
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="prose prose-sm max-w-none">
                      <div className="whitespace-pre-wrap text-sm text-gray-700 bg-white p-4 rounded-lg border border-blue-100">
                        {docSummary}
                      </div>
                    </div>
                  )}
                </CardContent>
              )}
            </Card>
          )}

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
              {generatedCode && (
                <div className="flex gap-2 items-center">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => saveTestFileMutation.mutate()}
                    disabled={saveTestFileMutation.isPending || !generatedCode}
                  >
                    {saveTestFileMutation.isPending ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Save className="mr-2 h-4 w-4" />
                    )}
                    保存
                  </Button>
                  {isEditing && (
                    <span className="text-xs text-orange-500">* 已修改</span>
                  )}
                  {!isEditing && generatedCode && (
                    <span className="text-xs text-gray-400">已保存</span>
                  )}
                </div>
              )}
            </CardHeader>
            <CardContent>
              {generatedCode ? (
                <div className="relative">
                  <textarea
                    value={generatedCode}
                    onChange={(e) => {
                      if (!selectedFile) return
                      const newCode = e.target.value
                      setGeneratedCode(newCode)
                      setIsEditing(true)
                      
                      // 实时更新文件状态
                      setFileStates(prev => ({
                        ...prev,
                        [selectedFile]: {
                          ...prev[selectedFile],
                          generatedCode: newCode,
                          isEditing: true
                        }
                      }))
                    }}
                    className="w-full h-[500px] p-4 font-mono text-sm bg-gray-900 text-gray-100 rounded-lg border border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                    style={{ fontFamily: 'Consolas, Monaco, "Courier New", monospace' }}
                    spellCheck={false}
                  />
                </div>
              ) : (
                <div className="h-[300px] flex flex-col items-center justify-center text-gray-400 border-2 border-dashed rounded-lg">
                  <Beaker className="h-12 w-12 mb-2 opacity-20" />
                  <p>请先选择一个源文件并点击"生成用例"</p>
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

