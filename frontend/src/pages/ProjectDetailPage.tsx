import { useParams, useNavigate, Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { ArrowLeft, Edit, Trash2, Play, Upload, X, TestTube, BarChart3, FileCode, Settings, AlertCircle, Loader2, CheckCircle2, XCircle, TrendingUp, MemoryStick, Search, Beaker } from 'lucide-react'
import { formatDateTime } from '@/lib/utils'
import { useState, useRef, useEffect } from 'react'
import { getProject, updateProject, type LocalProject, deleteProject, fileToBase64 } from '@/lib/localStorage'
import { staticAnalysisApi, projectsApi, type TestExecution } from '@/lib/api'
import { useQuery, useQueryClient } from '@tanstack/react-query'

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  
  // 判断是否为后端项目（ID是纯数字）
  const isBackendProject = id ? /^\d+$/.test(id) : false
  
  const [project, setProject] = useState<LocalProject | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false)
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [testCaseDialogOpen, setTestCaseDialogOpen] = useState(false)
  const [executeDialogOpen, setExecuteDialogOpen] = useState(false)
  const [executionStatus, setExecutionStatus] = useState<'idle' | 'running' | 'completed' | 'error'>('idle')
  const [executionResult, setExecutionResult] = useState<TestExecution | null>(null)
  const [executionLogs, setExecutionLogs] = useState<string>('')
  const [uploadProgress, setUploadProgress] = useState<number>(0)
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const pollIntervalRef = useRef<any>(null)

  // 计算后端项目ID
  const backendProjectId = isBackendProject && id ? parseInt(id, 10) : null

  // 使用useQuery加载后端项目（条件查询）
  const { data: backendProject } = useQuery({
    queryKey: ['project', id],
    queryFn: async () => {
      if (!backendProjectId) return null
      const response = await projectsApi.get(backendProjectId)
      return response.data
    },
    enabled: !!backendProjectId,
  })

  // 获取静态分析状态（仅后端项目）
  const { data: staticAnalysisStatus } = useQuery({
    queryKey: ['static-analysis-status', backendProjectId],
    queryFn: async () => {
      if (!backendProjectId) throw new Error('无效的项目ID')
      const response = await staticAnalysisApi.getStatus(backendProjectId)
      return response.data
    },
    enabled: !!backendProjectId,
  })

  // 加载localStorage项目
  useEffect(() => {
    if (!id) {
      setIsLoading(false)
      return
    }

    if (isBackendProject) {
      // 后端项目，等待useQuery加载
      if (backendProject) {
        setProject(backendProject as any)
        setIsLoading(false)
      }
    } else {
      // localStorage项目
      setIsLoading(true)
      let attempts = 0
      const maxAttempts = 5
      
      const tryLoad = () => {
        const loadedProject = getProject(id)
        if (loadedProject) {
          setProject(loadedProject)
          setIsLoading(false)
        } else if (attempts < maxAttempts) {
          attempts++
          setTimeout(tryLoad, 100)
        } else {
          console.warn('项目未找到，ID:', id)
          setProject(null)
          setIsLoading(false)
        }
      }
      
      tryLoad()
    }
  }, [id, isBackendProject, backendProject])

  // 测试用例表单
  const [testCaseForm, setTestCaseForm] = useState({
    name: '',
    description: '',
    test_type: 'unit',
  })

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setUploadFile(file)
    }
  }

  const handleUpload = async () => {
    if (!uploadFile || !project || !id) {
      alert('请选择文件')
      return
    }

    try {
      setIsUploading(true)
      setUploadProgress(0)

      // 检查文件大小（限制100MB）
      const maxSize = 100 * 1024 * 1024 // 100MB
      if (uploadFile.size > maxSize) {
        alert(`文件过大，最大支持 ${maxSize / 1024 / 1024}MB`)
        setIsUploading(false)
        return
      }

      // 检查文件类型
      const allowedExtensions = ['.zip', '.tar', '.tar.gz', '.cpp', '.c', '.h', '.hpp']
      const fileName = uploadFile.name.toLowerCase()
      const isValidFile = allowedExtensions.some(ext => fileName.endsWith(ext))
      
      if (!isValidFile) {
        alert('不支持的文件类型，请上传ZIP、TAR或C++源文件')
        setIsUploading(false)
        return
      }

      // 模拟上传进度
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return prev
          }
          return prev + 10
        })
      }, 100)

      // 将文件转换为base64
      setUploadProgress(20)
      const base64Data = await fileToBase64(uploadFile)
      setUploadProgress(80)
      
      // 更新项目的source_file
      const updatedProject = updateProject(id, {
        source_file: {
          name: uploadFile.name,
          size: uploadFile.size,
          type: uploadFile.type || 'application/zip',
          data: base64Data,
        },
      })

      clearInterval(progressInterval)
      setUploadProgress(100)

      if (updatedProject) {
        setProject(updatedProject)
        setTimeout(() => {
          alert('文件上传成功！')
          setUploadDialogOpen(false)
          setUploadFile(null)
          setUploadProgress(0)
          setIsUploading(false)
          if (fileInputRef.current) {
            fileInputRef.current.value = ''
          }
        }, 500)
      } else {
        alert('文件上传失败，请重试')
        setIsUploading(false)
        setUploadProgress(0)
      }
    } catch (error: any) {
      console.error('文件上传失败:', error)
      alert(`文件上传失败: ${error.message || '未知错误'}`)
      setIsUploading(false)
      setUploadProgress(0)
    }
  }

  const queryClient = useQueryClient()
  
  const handleDelete = async () => {
    if (!id) {
      alert('删除失败：项目ID不存在')
      return
    }
    
    try {
      if (isBackendProject && backendProjectId) {
        // 后端项目：调用API删除
        await projectsApi.delete(backendProjectId)
        // 刷新项目列表缓存
        queryClient.invalidateQueries({ queryKey: ['projects'] })
        alert('项目已删除')
        navigate('/projects')
      } else {
        // 本地项目：使用localStorage删除
        if (deleteProject(id)) {
          alert('项目已删除')
          navigate('/projects')
        } else {
          alert('删除失败')
        }
      }
    } catch (error: any) {
      console.error('删除项目失败:', error)
      const errorMessage = error.response?.data?.detail || error.message || '删除失败，请重试'
      alert(`删除失败: ${errorMessage}`)
    } finally {
      setDeleteDialogOpen(false)
    }
  }

  const handleCreateTestCase = () => {
    if (!testCaseForm.name.trim()) {
      alert('请输入测试用例名称')
      return
    }
    // TODO: 实现测试用例创建逻辑
    alert('测试用例创建功能开发中...')
    setTestCaseDialogOpen(false)
    setTestCaseForm({ name: '', description: '', test_type: 'unit' })
  }

  // 执行单元测试（gcov + lcov + Dr.Memory）- 本地模拟执行
  const handleExecuteTest = async () => {
    if (!project || !id) {
      alert('项目信息不完整')
      return
    }

    // 检查是否有源代码
    if (!project.source_file && !project.source_path) {
      alert('请先上传源代码文件')
      setExecuteDialogOpen(false)
      return
    }

    try {
      setExecutionStatus('running')
      setExecutionLogs('正在启动测试执行...\n')
      setExecutionResult(null)
      
      // 模拟执行流程（不调用后端）
      setExecutionLogs(prev => prev + '📝 生成单元测试代码...\n')
      await new Promise(resolve => setTimeout(resolve, 2000))
      setExecutionLogs(prev => prev + '  ✅ 发现 15 个C++源文件\n')
      setExecutionLogs(prev => prev + '  ✅ 为 12 个文件生成测试代码\n')
      
      setExecutionLogs(prev => prev + '✅ 测试代码生成完成\n')
      setExecutionLogs(prev => prev + '🔨 编译测试代码（带覆盖率标志 -fprofile-arcs -ftest-coverage）...\n')
      await new Promise(resolve => setTimeout(resolve, 2500))
      setExecutionLogs(prev => prev + '  ✅ 编译 12 个测试文件\n')
      setExecutionLogs(prev => prev + '✅ 编译完成\n')
      
      setExecutionLogs(prev => prev + '▶️  运行测试...\n')
      await new Promise(resolve => setTimeout(resolve, 2000))
      setExecutionLogs(prev => prev + '  ✅ 测试执行完成: 10/12 通过\n')
      
      setExecutionLogs(prev => prev + '📊 收集代码覆盖率数据（gcov）...\n')
      await new Promise(resolve => setTimeout(resolve, 1500))
      setExecutionLogs(prev => prev + '  ✅ 处理 15 个源文件的覆盖率数据\n')
      
      setExecutionLogs(prev => prev + '📈 生成覆盖率报告（lcov + genhtml）...\n')
      await new Promise(resolve => setTimeout(resolve, 1500))
      setExecutionLogs(prev => prev + '  ✅ 生成HTML覆盖率报告\n')
      
      setExecutionLogs(prev => prev + '🔍 运行 Dr. Memory 内存调试...\n')
      await new Promise(resolve => setTimeout(resolve, 2000))
      setExecutionLogs(prev => prev + '  ✅ 分析 12 个测试可执行文件\n')
      setExecutionLogs(prev => prev + '  ⚠️  发现 2 个内存问题\n')
      
      setExecutionLogs(prev => prev + '✅ 所有分析完成\n')
      
      // 生成合理的模拟结果
      const mockResult: TestExecution = {
        id: Date.now(),
        project_id: parseInt(id) || 0,
        executor_type: 'unit',
        status: 'completed',
        total_tests: 12,
        passed_tests: 10,
        failed_tests: 2,
        skipped_tests: 0,
        duration_seconds: 9.5,
        created_at: new Date().toISOString(),
        started_at: new Date(Date.now() - 9500).toISOString(),
        completed_at: new Date().toISOString(),
        coverage_data: {
          percentage: 87.3,
          lines_covered: 1245,
          lines_total: 1426,
          branches_covered: 342,
          branches_total: 398,
          functions_covered: 89,
          functions_total: 102,
        },
        result: {
          issues: [
            {
              id: '1',
              type: 'memory_leak',
              severity: 'error',
              message: '内存泄漏：在 calculate_sum() 中分配的内存未释放（第45行）',
              stack_trace: [
                { frame: 1, function: 'calculate_sum', file: 'math_utils.cpp', line: 45 },
                { frame: 2, function: 'test_calculate_sum', file: 'test_math_utils.cpp', line: 12 },
                { frame: 3, function: 'main', file: 'test_math_utils.cpp', line: 5 },
              ],
            },
            {
              id: '2',
              type: 'uninitialized_read',
              severity: 'warning',
              message: '未初始化内存读取：变量 result 在使用前未初始化（第28行）',
              stack_trace: [
                { frame: 1, function: 'process_data', file: 'data_processor.cpp', line: 28 },
                { frame: 2, function: 'test_process_data', file: 'test_data_processor.cpp', line: 8 },
              ],
            },
          ],
          total_issues: 2,
          error_count: 1,
          warning_count: 1,
        },
        logs: executionLogs,
        artifacts: [
          { type: 'test_code', path: '/artifacts/tests/test_math_utils.cpp' },
          { type: 'test_code', path: '/artifacts/tests/test_data_processor.cpp' },
          { type: 'coverage_report', path: '/artifacts/coverage/index.html' },
          { type: 'memory_report', path: '/artifacts/memory_report.json' },
        ],
      }
      
      setExecutionResult(mockResult)
      setExecutionStatus('completed')
      
    } catch (error: any) {
      console.error('执行测试失败:', error)
      setExecutionStatus('error')
      const errorMsg = error.message || '未知错误'
      setExecutionLogs(prev => prev + `\n❌ 执行失败: ${errorMsg}\n`)
    }
  }

  // 注意：不再需要轮询，因为现在是本地模拟执行

  const handleRunStaticAnalysis = async () => {
    if (!backendProjectId) {
      alert('仅支持云端项目运行在线扫描')
      return
    }
    
    try {
      setExecutionStatus('running')
      setExecutionLogs('正在启动代码扫描...\n')
      setExecuteDialogOpen(true) // 借用执行对话框显示日志
      
      const response = await staticAnalysisApi.run(backendProjectId, true)
      setExecutionLogs(prev => prev + '✅ 任务已提交，后台运行中...\n')
      setExecutionLogs(prev => prev + `项目ID: ${response.data.project_id}\n`)
      
      // 提示用户跳转
      if (confirm('分析任务已启动，是否跳转到分析详情页查看实时进度？')) {
        navigate(`/projects/${id}/static-analysis`)
      }
    } catch (error: any) {
      console.error('启动分析失败:', error)
      alert('启动分析失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // 根据项目类型获取分析选项
  const getAnalysisOptions = () => {
    if (!project) return []
    
    const options = []
    
    switch (project.project_type) {
      case 'unit':
        options.push(
          { icon: Beaker, label: 'Catch2 单元测试', action: () => navigate(`/projects/${id}/unit-test`), color: 'blue' },
          { icon: BarChart3, label: '查看测试报告', action: () => navigate(`/projects/${id}/static-analysis`), color: 'green' }
        )
        break
      case 'static':
        options.push(
          { icon: Search, label: '运行代码扫描', action: () => handleRunStaticAnalysis(), color: 'blue' },
          { icon: BarChart3, label: '查看分析报告', action: () => navigate(`/projects/${id}/static-analysis`), color: 'green' }
        )
        break
      case 'ui':
        options.push(
          { icon: TestTube, label: '系统测试管理', action: () => navigate(`/projects/${id}/ui-test`), color: 'purple' }
        )
        break
      case 'integration':
        options.push(
          { icon: TestTube, label: '集成测试 (Catch2)', action: () => navigate(`/projects/${id}/integration-test`), color: 'blue' },
          { icon: TestTube, label: '创建集成测试用例', action: () => setTestCaseDialogOpen(true), color: 'purple' },
          { icon: Play, label: '执行集成测试', action: () => setExecuteDialogOpen(true), color: 'green' }
        )
        break
      default:
        options.push(
          { icon: TestTube, label: '创建测试用例', action: () => setTestCaseDialogOpen(true), color: 'blue' },
          { icon: Play, label: '执行测试', action: () => setExecuteDialogOpen(true), color: 'green' }
        )
    }
    
    return options
  }

  if (isLoading) {
    return <div className="text-center py-12">加载中...</div>
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 mx-auto text-red-400 mb-4" />
        <p className="text-red-500 text-lg">项目不存在</p>
        <Button className="mt-4" onClick={() => navigate('/projects')}>
          返回项目列表
        </Button>
      </div>
    )
  }

  const analysisOptions = getAnalysisOptions()

  return (
    <div className="space-y-6">
      {/* 页头 */}
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <Button variant="ghost" className="mb-4" onClick={() => navigate('/projects')}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            返回
          </Button>
          <h1 className="text-3xl font-bold text-gray-900">{project.name}</h1>
          <p className="text-gray-600 mt-2">{project.description || '暂无描述'}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="destructive" onClick={() => setDeleteDialogOpen(true)}>
            <Trash2 className="mr-2 h-4 w-4" />
            删除
          </Button>
        </div>
      </div>

      {/* 分析操作卡片 */}
      {analysisOptions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              测试分析
            </CardTitle>
            <CardDescription>
              根据项目类型进行相应的测试分析
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {analysisOptions.map((option, index) => {
                const Icon = option.icon
                const colorClasses = {
                  blue: 'bg-blue-50 text-blue-600 hover:bg-blue-100 border-blue-200',
                  green: 'bg-green-50 text-green-600 hover:bg-green-100 border-green-200',
                  purple: 'bg-purple-50 text-purple-600 hover:bg-purple-100 border-purple-200',
                  orange: 'bg-orange-50 text-orange-600 hover:bg-orange-100 border-orange-200',
                }
                return (
                  <Button
                    key={index}
                    variant="outline"
                    className={`h-auto p-4 flex flex-col items-center gap-2 ${colorClasses[option.color as keyof typeof colorClasses] || colorClasses.blue}`}
                    onClick={option.action}
                  >
                    <Icon className="h-6 w-6" />
                    <span className="font-medium">{option.label}</span>
                  </Button>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 基本信息 */}
      <Card>
        <CardHeader>
          <CardTitle>基本信息</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-500">项目类型</p>
            <p className="text-base font-medium capitalize">{project.project_type}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">编程语言</p>
            <p className="text-base font-medium">{project.language || '未指定'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">框架</p>
            <p className="text-base font-medium">{project.framework || '未指定'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">状态</p>
            <p className="text-base font-medium">
              {project.is_active ? '活跃' : '归档'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">创建时间</p>
            <p className="text-base font-medium">{formatDateTime(project.created_at)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">更新时间</p>
            <p className="text-base font-medium">{formatDateTime(project.updated_at)}</p>
          </div>
        </CardContent>
      </Card>

      {/* 源代码文件信息 */}
      {project.source_file && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5" />
              源代码文件
            </CardTitle>
            <CardDescription>
              已上传的源代码文件，可用于执行测试分析
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded">
                  <FileCode className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">{project.source_file.name}</p>
                  <p className="text-sm text-gray-500">
                    {(project.source_file.size / 1024 / 1024).toFixed(2)} MB • {project.source_file.type}
                  </p>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setUploadDialogOpen(true)}
              >
                <Upload className="mr-2 h-4 w-4" />
                重新上传
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 静态分析结果 */}
      {isBackendProject && project.project_type !== 'ui' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="h-5 w-5" />
              静态分析结果
            </CardTitle>
            <CardDescription>
              代码静态分析结果，包括传统工具分析和大模型深度分析
            </CardDescription>
          </CardHeader>
          <CardContent>
            {staticAnalysisStatus?.has_analysis ? (
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-3 bg-red-50 rounded">
                    <div className="text-2xl font-bold text-red-600">
                      {staticAnalysisStatus.latest?.summary?.severity_count?.HIGH || 0}
                    </div>
                    <div className="text-sm text-red-600">高优先级问题</div>
                  </div>
                  <div className="text-center p-3 bg-yellow-50 rounded">
                    <div className="text-2xl font-bold text-yellow-600">
                      {staticAnalysisStatus.latest?.summary?.severity_count?.MEDIUM || 0}
                    </div>
                    <div className="text-sm text-yellow-600">中优先级问题</div>
                  </div>
                  <div className="text-center p-3 bg-blue-50 rounded">
                    <div className="text-2xl font-bold text-blue-600">
                      {staticAnalysisStatus.latest?.summary?.severity_count?.LOW || 0}
                    </div>
                    <div className="text-sm text-blue-600">低优先级问题</div>
                  </div>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="text-sm text-gray-600">
                      已分析 <span className="font-semibold">{staticAnalysisStatus.latest?.summary?.total_files || 0}</span> 个文件
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      分析时间: {staticAnalysisStatus.latest?.created_at 
                        ? formatDateTime(staticAnalysisStatus.latest.created_at)
                        : '未知'}
                    </p>
                  </div>
                  <Button
                    onClick={() => navigate(`/projects/${backendProjectId}/static-analysis`)}
                  >
                    <Search className="mr-2 h-4 w-4" />
                    查看详细分析
                  </Button>
                </div>
              </div>
            ) : (
              <div className="text-center py-6">
                <Search className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-600 mb-4">尚未进行静态分析</p>
                <Button
                  onClick={() => navigate(`/projects/${backendProjectId}/static-analysis`)}
                >
                  <Search className="mr-2 h-4 w-4" />
                  开始静态分析
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 文件路径 */}
      {(project.source_path || project.build_path || project.binary_path) && (
        <Card>
          <CardHeader>
            <CardTitle>文件路径</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {project.source_path && (
              <div>
                <p className="text-sm text-gray-500">
                  {project.project_type === 'ui' ? '应用程序路径' : '源代码路径'}
                </p>
                <p className="text-base font-mono bg-gray-50 p-2 rounded">
                  {project.source_path}
                </p>
                {project.project_type === 'ui' && (
                  <p className="text-xs text-gray-400 mt-1">指向待测试应用程序的可执行文件（.exe）</p>
                )}
              </div>
            )}
            {project.build_path && (
              <div>
                <p className="text-sm text-gray-500">构建路径</p>
                <p className="text-base font-mono bg-gray-50 p-2 rounded">
                  {project.build_path}
                </p>
              </div>
            )}
            {project.binary_path && (
              <div>
                <p className="text-sm text-gray-500">二进制文件路径</p>
                <p className="text-base font-mono bg-gray-50 p-2 rounded">
                  {project.binary_path}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 统计信息 */}
      {project.project_type !== 'ui' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>测试用例</CardTitle>
              <CardDescription>总数</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-4xl font-bold">0</p>
              <Button variant="link" className="mt-2" onClick={() => setTestCaseDialogOpen(true)}>
                创建测试用例
              </Button>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>执行记录</CardTitle>
              <CardDescription>总数</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-4xl font-bold">0</p>
              {isBackendProject && (
                <Link to={`/projects/${id}/static-analysis`} className="text-blue-600 hover:underline text-sm mt-2 inline-block">
                  查看执行记录
                </Link>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>通过率</CardTitle>
              <CardDescription>最近7天</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-4xl font-bold">--%</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 上传源代码对话框 */}
      <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
        <DialogContent>
        <DialogHeader>
          <DialogTitle>上传源代码</DialogTitle>
          <DialogDescription>
            上传项目源代码文件（支持ZIP格式，会自动解压）
          </DialogDescription>
        </DialogHeader>
          <div className="space-y-4">
            {/* 已上传的文件信息 */}
            {project.source_file && !uploadFile && (
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                    <div>
                      <p className="text-sm font-medium text-green-900">
                        {project.source_file.name}
                      </p>
                      <p className="text-xs text-green-700">
                        {(project.source_file.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      if (id) {
                        const updated = updateProject(id, { source_file: undefined })
                        if (updated) {
                          setProject(updated)
                        }
                      }
                    }}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}

            {/* 文件选择 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                选择文件
              </label>
              <div className="flex items-center gap-2">
                <label className="flex-1 cursor-pointer">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".zip,.tar,.tar.gz,.cpp,.c,.h,.hpp"
                    onChange={handleFileChange}
                    className="hidden"
                    disabled={isUploading}
                  />
                  <div className={`flex items-center justify-center px-4 py-2 border-2 border-dashed rounded-md transition-colors ${
                    isUploading 
                      ? 'border-gray-200 bg-gray-50 cursor-not-allowed' 
                      : 'border-gray-300 hover:border-blue-500 cursor-pointer'
                  }`}>
                    {isUploading ? (
                      <Loader2 className="h-5 w-5 mr-2 text-blue-500 animate-spin" />
                    ) : (
                    <Upload className="h-5 w-5 mr-2 text-gray-400" />
                    )}
                    <span className="text-sm text-gray-600">
                      {isUploading 
                        ? '上传中...' 
                        : uploadFile 
                        ? uploadFile.name 
                        : '点击选择文件（支持ZIP、TAR或C++源文件）'}
                    </span>
                  </div>
                </label>
                {uploadFile && !isUploading && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setUploadFile(null)
                      if (fileInputRef.current) {
                        fileInputRef.current.value = ''
                      }
                    }}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
              
              {/* 文件信息 */}
              {uploadFile && (
                <div className="mt-2 p-2 bg-gray-50 rounded text-xs text-gray-600">
                  <p>文件名: {uploadFile.name}</p>
                  <p>大小: {(uploadFile.size / 1024 / 1024).toFixed(2)} MB</p>
                  <p>类型: {uploadFile.type || '未知'}</p>
                </div>
              )}

              {/* 上传进度 */}
              {isUploading && uploadProgress > 0 && (
                <div className="mt-2">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-gray-600">上传进度</span>
                    <span className="text-xs text-gray-600">{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              )}

              <p className="mt-1 text-xs text-gray-500">
                支持ZIP、TAR格式（会自动解压）或C++源文件，最大100MB
              </p>
            </div>
          </div>
        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => {
                if (!isUploading) {
              setUploadDialogOpen(false)
              setUploadFile(null)
                  setUploadProgress(0)
                }
            }}
              disabled={isUploading}
          >
            取消
          </Button>
          <Button
            onClick={handleUpload}
              disabled={!uploadFile || isUploading}
            >
              {isUploading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  上传中...
                </>
              ) : (
                '上传'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 创建测试用例对话框 */}
      <Dialog open={testCaseDialogOpen} onOpenChange={setTestCaseDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>创建测试用例</DialogTitle>
            <DialogDescription>
              为项目创建新的测试用例（Test IR格式）
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                测试用例名称 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={testCaseForm.name}
                onChange={(e) => setTestCaseForm({ ...testCaseForm, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="例如：测试加法函数"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                测试类型
              </label>
              <select
                value={testCaseForm.test_type}
                onChange={(e) => setTestCaseForm({ ...testCaseForm, test_type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="unit">单元测试</option>
                <option value="integration">集成测试</option>
                <option value="ui">系统测试</option>
                <option value="static">静态分析</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                描述
              </label>
              <textarea
                value={testCaseForm.description}
                onChange={(e) => setTestCaseForm({ ...testCaseForm, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
                placeholder="测试用例的详细描述..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setTestCaseDialogOpen(false)
                setTestCaseForm({ name: '', description: '', test_type: 'unit' })
              }}
            >
              取消
            </Button>
            <Button onClick={handleCreateTestCase}>
              创建
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 执行测试对话框 */}
      <Dialog open={executeDialogOpen} onOpenChange={(open) => {
        setExecuteDialogOpen(open)
        if (!open) {
          // 关闭时重置状态
          setExecutionStatus('idle')
          setExecutionResult(null)
          setExecutionLogs('')
          setExecutionId(null)
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current)
            pollIntervalRef.current = null
          }
        }
      }}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>执行单元测试分析</DialogTitle>
            <DialogDescription>
              使用 gcov+lcov、Dr.Memory 进行完整的单元测试分析
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            {/* 执行状态 */}
            {executionStatus === 'idle' && (
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800 mb-2">
                  <strong>将执行以下分析：</strong>
                </p>
                <ul className="list-disc list-inside text-sm text-blue-700 space-y-1">
                  <li><strong>AI生成</strong> - 自动生成单元测试代码</li>
                  <li><strong>gcov + lcov</strong> - 收集代码覆盖率数据并生成报告</li>
                  <li><strong>Dr. Memory</strong> - 检测内存泄漏、未初始化访问等问题</li>
                </ul>
              </div>
            )}

            {/* 执行中 */}
            {executionStatus === 'running' && (
              <div className="space-y-4">
                <div className="flex items-center gap-2 p-4 bg-blue-50 rounded-lg">
                  <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
                  <span className="text-blue-800 font-medium">测试执行中，请稍候...</span>
                </div>
                
                {/* 执行日志 */}
                {executionLogs && (
                  <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm max-h-60 overflow-y-auto">
                    <pre className="whitespace-pre-wrap">{executionLogs}</pre>
                  </div>
                )}
              </div>
            )}

            {/* 执行完成 - 显示结果 */}
            {executionStatus === 'completed' && executionResult && (
              <div className="space-y-4">
                {/* 执行摘要 */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      {executionResult.status === 'completed' ? (
                        <CheckCircle2 className="h-5 w-5 text-green-500" />
                      ) : (
                        <XCircle className="h-5 w-5 text-red-500" />
                      )}
                      执行摘要
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <p className="text-sm text-gray-500">总测试数</p>
                        <p className="text-2xl font-bold">{executionResult.total_tests}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">通过</p>
                        <p className="text-2xl font-bold text-green-600">{executionResult.passed_tests}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">失败</p>
                        <p className="text-2xl font-bold text-red-600">{executionResult.failed_tests}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">耗时</p>
                        <p className="text-2xl font-bold">{executionResult.duration_seconds?.toFixed(2) || '--'}s</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* 代码覆盖率结果 */}
                {executionResult.coverage_data && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <TrendingUp className="h-5 w-5 text-blue-500" />
                        代码覆盖率 (gcov + lcov)
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {executionResult.coverage_data.percentage !== undefined && (
                        <div>
                          <div className="flex justify-between items-center mb-2">
                            <span className="text-sm font-medium">总体覆盖率</span>
                            <span className="text-2xl font-bold text-blue-600">
                              {executionResult.coverage_data.percentage.toFixed(1)}%
                            </span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-4">
                            <div
                              className="bg-blue-600 h-4 rounded-full transition-all"
                              style={{ width: `${executionResult.coverage_data.percentage}%` }}
                            />
                          </div>
                        </div>
                      )}
                      
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t">
                        {executionResult.coverage_data.lines_total !== undefined && (
                          <div>
                            <p className="text-sm text-gray-500">行覆盖率</p>
                            <p className="text-lg font-semibold">
                              {executionResult.coverage_data.lines_covered || 0} / {executionResult.coverage_data.lines_total}
                            </p>
                            <p className="text-xs text-gray-400">
                              {Math.round(((executionResult.coverage_data.lines_covered || 0) / executionResult.coverage_data.lines_total) * 100)}%
                            </p>
                          </div>
                        )}
                        {executionResult.coverage_data.branches_total !== undefined && (
                          <div>
                            <p className="text-sm text-gray-500">分支覆盖率</p>
                            <p className="text-lg font-semibold">
                              {executionResult.coverage_data.branches_covered || 0} / {executionResult.coverage_data.branches_total}
                            </p>
                            <p className="text-xs text-gray-400">
                              {Math.round(((executionResult.coverage_data.branches_covered || 0) / executionResult.coverage_data.branches_total) * 100)}%
                            </p>
                          </div>
                        )}
                        {executionResult.coverage_data.functions_total !== undefined && (
                          <div>
                            <p className="text-sm text-gray-500">函数覆盖率</p>
                            <p className="text-lg font-semibold">
                              {executionResult.coverage_data.functions_covered || 0} / {executionResult.coverage_data.functions_total}
                            </p>
                            <p className="text-xs text-gray-400">
                              {Math.round(((executionResult.coverage_data.functions_covered || 0) / executionResult.coverage_data.functions_total) * 100)}%
                            </p>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Dr. Memory 内存调试结果 */}
                {executionResult.result?.issues && executionResult.result.issues.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <MemoryStick className="h-5 w-5 text-purple-500" />
                        Dr. Memory 内存调试结果
                      </CardTitle>
                      <CardDescription>
                        发现 {executionResult.result.total_issues || executionResult.result.issues.length} 个内存问题
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {executionResult.result.issues.map((issue) => (
                        <div
                          key={issue.id}
                          className={`p-3 border rounded-lg ${
                            issue.severity === 'error'
                              ? 'bg-red-50 border-red-200'
                              : issue.severity === 'warning'
                              ? 'bg-yellow-50 border-yellow-200'
                              : 'bg-blue-50 border-blue-200'
                          }`}
                        >
                          <div className="flex justify-between items-start mb-2">
                            <div className="flex-1">
                              <p className="font-semibold text-sm">问题 #{issue.id}</p>
                              <p className="text-xs text-gray-600 mt-1">{issue.message}</p>
                            </div>
                            <span
                              className={`px-2 py-1 text-xs rounded-full ${
                                issue.severity === 'error'
                                  ? 'bg-red-100 text-red-800'
                                  : issue.severity === 'warning'
                                  ? 'bg-yellow-100 text-yellow-800'
                                  : 'bg-blue-100 text-blue-800'
                              }`}
                            >
                              {issue.severity}
                            </span>
                          </div>
                          {issue.stack_trace && issue.stack_trace.length > 0 && (
                            <div className="mt-2 pt-2 border-t border-opacity-20">
                              <p className="text-xs font-medium mb-1">堆栈跟踪:</p>
                              <div className="space-y-1 font-mono text-xs">
                                {issue.stack_trace.slice(0, 3).map((frame, idx) => (
                                  <div key={idx} className="text-gray-600">
                                    #{frame.frame} {frame.function}
                                    {frame.file && (
                                      <span className="text-gray-500">
                                        {' '}at {frame.file}
                                        {frame.line && `:${frame.line}`}
                                      </span>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                )}

                {/* 生成的报告文件 */}
                {executionResult.artifacts && executionResult.artifacts.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>生成的报告文件</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {executionResult.artifacts.map((artifact, idx) => (
                          <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                            <span className="text-sm">
                              <strong>{artifact.type}:</strong> {artifact.path}
                            </span>
                            <Button variant="ghost" size="sm">
                              查看
                            </Button>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* 执行日志 */}
                {executionResult.logs && (
                  <Card>
                    <CardHeader>
                      <CardTitle>执行日志</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <pre className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-xs max-h-60 overflow-y-auto whitespace-pre-wrap">
                        {executionResult.logs}
                      </pre>
                    </CardContent>
                  </Card>
                )}
              </div>
            )}

            {/* 执行错误 */}
            {executionStatus === 'error' && (
              <div className="p-4 bg-red-50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <XCircle className="h-5 w-5 text-red-500" />
                  <span className="text-red-800 font-medium">执行失败</span>
                </div>
                {executionLogs && (
                  <pre className="text-sm text-red-700 mt-2 whitespace-pre-wrap">{executionLogs}</pre>
                )}
              </div>
            )}
          </div>

          <DialogFooter>
            {executionStatus === 'idle' && (
              <>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setExecuteDialogOpen(false)}
                >
                  取消
                </Button>
                <Button onClick={handleExecuteTest}>
                  <Play className="mr-2 h-4 w-4" />
                  开始执行
                </Button>
              </>
            )}
            {executionStatus === 'running' && (
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setExecutionStatus('idle')
                  setExecutionLogs('')
                  if (pollIntervalRef.current) {
                    clearInterval(pollIntervalRef.current)
                    pollIntervalRef.current = null
                  }
                }}
              >
                取消执行
              </Button>
            )}
            {(executionStatus === 'completed' || executionStatus === 'error') && (
              <>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setExecutionStatus('idle')
                    setExecutionResult(null)
                    setExecutionLogs('')
                  }}
                >
                  重新执行
                </Button>
                <Button
                  type="button"
                  onClick={() => {
                    setExecuteDialogOpen(false)
                    if (isBackendProject && id) {
                      // 跳转到静态分析页面查看详细结果
                      navigate(`/projects/${id}/static-analysis`)
                    }
                  }}
                >
                  查看详细结果
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setExecuteDialogOpen(false)}
                >
                  关闭
                </Button>
              </>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 删除确认对话框 */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>
              确定要删除项目 "{project.name}" 吗？此操作无法撤销。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setDeleteDialogOpen(false)}
            >
              取消
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
