import { useParams, useNavigate, Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { ArrowLeft, Edit, Trash2, Play, Upload, X, TestTube, BarChart3, FileCode, Settings, AlertCircle } from 'lucide-react'
import { formatDateTime } from '@/lib/utils'
import { useState, useRef, useEffect } from 'react'
import { getProject, type LocalProject, deleteProject } from '@/lib/localStorage'

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [project, setProject] = useState<LocalProject | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false)
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [testCaseDialogOpen, setTestCaseDialogOpen] = useState(false)
  const [executeDialogOpen, setExecuteDialogOpen] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // 加载项目数据
  useEffect(() => {
    if (id) {
      const loadedProject = getProject(id)
      if (loadedProject) {
        setProject(loadedProject)
      }
      setIsLoading(false)
    }
  }, [id])

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

  const handleUpload = () => {
    if (!uploadFile) {
      alert('请选择文件')
      return
    }
    // TODO: 实现文件上传逻辑
    alert('文件上传功能开发中...')
    setUploadDialogOpen(false)
    setUploadFile(null)
  }

  const handleDelete = () => {
    if (id && deleteProject(id)) {
      alert('项目已删除')
      navigate('/projects')
    } else {
      alert('删除失败')
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

  const handleExecuteTest = () => {
    // TODO: 实现测试执行逻辑
    alert('测试执行功能开发中...')
    setExecuteDialogOpen(false)
  }

  // 根据项目类型获取分析选项
  const getAnalysisOptions = () => {
    if (!project) return []
    
    const options = []
    
    switch (project.project_type) {
      case 'unit':
        options.push(
          { icon: TestTube, label: '创建单元测试', action: () => setTestCaseDialogOpen(true), color: 'blue' },
          { icon: BarChart3, label: '代码覆盖率分析', action: () => navigate(`/results?project=${id}`), color: 'green' },
          { icon: Play, label: '执行单元测试', action: () => setExecuteDialogOpen(true), color: 'purple' }
        )
        break
      case 'static':
        options.push(
          { icon: FileCode, label: '静态代码分析', action: () => setExecuteDialogOpen(true), color: 'orange' },
          { icon: BarChart3, label: '查看分析报告', action: () => navigate(`/results?project=${id}`), color: 'blue' }
        )
        break
      case 'ui':
        options.push(
          { icon: TestTube, label: '创建UI测试', action: () => setTestCaseDialogOpen(true), color: 'purple' },
          { icon: Play, label: '执行UI测试', action: () => setExecuteDialogOpen(true), color: 'green' },
          { icon: BarChart3, label: '查看测试结果', action: () => navigate(`/results?project=${id}`), color: 'blue' }
        )
        break
      case 'integration':
        options.push(
          { icon: TestTube, label: '创建集成测试', action: () => setTestCaseDialogOpen(true), color: 'blue' },
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
          <Button variant="outline" onClick={() => setUploadDialogOpen(true)}>
            <Upload className="mr-2 h-4 w-4" />
            上传源代码
          </Button>
          <Button variant="outline">
            <Edit className="mr-2 h-4 w-4" />
            编辑
          </Button>
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

      {/* 文件路径 */}
      {(project.source_path || project.build_path || project.binary_path) && (
        <Card>
          <CardHeader>
            <CardTitle>文件路径</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {project.source_path && (
              <div>
                <p className="text-sm text-gray-500">源代码路径</p>
                <p className="text-base font-mono bg-gray-50 p-2 rounded">
                  {project.source_path}
                </p>
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
            <Link to="/results" className="text-blue-600 hover:underline text-sm mt-2 inline-block">
              查看执行记录
            </Link>
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
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                选择文件
              </label>
              <div className="flex items-center gap-2">
                <label className="flex-1 cursor-pointer">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".zip,.tar,.tar.gz"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                  <div className="flex items-center justify-center px-4 py-2 border-2 border-dashed border-gray-300 rounded-md hover:border-blue-500 transition-colors">
                    <Upload className="h-5 w-5 mr-2 text-gray-400" />
                    <span className="text-sm text-gray-600">
                      {uploadFile ? uploadFile.name : '点击选择文件（支持ZIP格式）'}
                    </span>
                  </div>
                </label>
                {uploadFile && (
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
              <p className="mt-1 text-xs text-gray-500">
                支持ZIP格式，上传后会自动解压到项目目录
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setUploadDialogOpen(false)
                setUploadFile(null)
              }}
            >
              取消
            </Button>
            <Button onClick={handleUpload} disabled={!uploadFile}>
              上传
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
                <option value="ui">UI测试</option>
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
      <Dialog open={executeDialogOpen} onOpenChange={setExecuteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>执行测试</DialogTitle>
            <DialogDescription>
              选择要执行的测试用例并开始测试
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-800">
                测试执行功能正在开发中。完成后将支持：
              </p>
              <ul className="list-disc list-inside mt-2 text-sm text-blue-700">
                <li>选择测试用例</li>
                <li>配置执行参数</li>
                <li>查看实时执行进度</li>
                <li>查看测试结果和报告</li>
              </ul>
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setExecuteDialogOpen(false)}
            >
              关闭
            </Button>
            <Button onClick={handleExecuteTest}>
              开始执行
            </Button>
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
