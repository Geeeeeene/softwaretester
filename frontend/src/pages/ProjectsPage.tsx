import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Plus, FolderOpen, Calendar, Code, Upload, X } from 'lucide-react'
import { formatDateTime } from '@/lib/utils'
import { 
  getAllProjects, 
  createProject, 
  fileToBase64,
  type LocalProject 
} from '@/lib/localStorage'

export default function ProjectsPage() {
  const [projectType, setProjectType] = useState<string | undefined>()
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [projects, setProjects] = useState<LocalProject[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    project_type: 'unit',
    language: '',
    framework: '',
  })
  const [sourceFile, setSourceFile] = useState<File | null>(null)
  const navigate = useNavigate()

  // 加载项目列表
  useEffect(() => {
    loadProjects()
  }, [projectType])

  const loadProjects = () => {
    setIsLoading(true)
    setError(null)
    try {
      let allProjects = getAllProjects()
      
      // 按项目类型过滤
      if (projectType) {
        allProjects = allProjects.filter(p => p.project_type === projectType)
      }
      
      setProjects(allProjects)
    } catch (error) {
      console.error('加载项目失败:', error)
      setError('加载项目失败，请稍后重试')
    } finally {
      setIsLoading(false)
    }
  }

  // 创建项目
  const handleCreateProject = async () => {
    if (!formData.name.trim()) {
      alert('请输入项目名称')
      return
    }
    if (!formData.project_type) {
      alert('请选择项目类型')
      return
    }

    setIsCreating(true)
    try {
      let sourceFileData = undefined
      
      // 如果有文件，转换为base64
      if (sourceFile) {
        try {
          const base64Data = await fileToBase64(sourceFile)
          sourceFileData = {
            name: sourceFile.name,
            size: sourceFile.size,
            type: sourceFile.type,
            data: base64Data,
          }
        } catch (error) {
          console.error('文件转换失败:', error)
          alert('文件处理失败，请重试')
          setIsCreating(false)
          return
        }
      }

      // 创建项目
      const newProject = createProject({
        name: formData.name,
        description: formData.description || undefined,
        project_type: formData.project_type,
        language: formData.language || undefined,
        framework: formData.framework || undefined,
        is_active: true,
        source_file: sourceFileData,
      })

      // 刷新列表
      loadProjects()
      
      // 关闭对话框并重置表单
      setCreateDialogOpen(false)
      resetForm()
      
      // 跳转到项目详情页
      navigate(`/projects/${newProject.id}`)
    } catch (error) {
      console.error('创建项目失败:', error)
      alert('创建项目失败，请重试')
    } finally {
      setIsCreating(false)
    }
  }

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      project_type: 'unit',
      language: '',
      framework: '',
    })
    setSourceFile(null)
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSourceFile(file)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    handleCreateProject()
  }

  const projectTypes = [
    { value: undefined, label: '全部' },
    { value: 'ui', label: 'UI测试' },
    { value: 'unit', label: '单元测试' },
    { value: 'integration', label: '集成测试' },
    { value: 'static', label: '静态分析' },
  ]

  return (
    <div className="space-y-6">
      {/* 页头 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">项目管理</h1>
          <p className="text-gray-600 mt-2">管理测试项目和配置</p>
        </div>
        <Button onClick={() => setCreateDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          创建项目
        </Button>
      </div>

      {/* 过滤器 */}
      <div className="flex gap-2">
        {projectTypes.map((type) => (
          <button
            key={type.label}
            onClick={() => setProjectType(type.value)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              projectType === type.value
                ? 'bg-primary text-white'
                : 'bg-white text-gray-700 hover:bg-gray-100 border'
            }`}
          >
            {type.label}
          </button>
        ))}
      </div>

      {/* 项目列表 */}
      {isLoading && (
        <div className="text-center py-12">
          <p className="text-gray-500">加载中...</p>
        </div>
      )}

      {error && (
        <div className="text-center py-12">
          <p className="text-red-500">加载失败，请稍后重试</p>
        </div>
      )}

      {!isLoading && projects.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <FolderOpen className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">暂无项目</p>
            <Button className="mt-4" onClick={() => setCreateDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              创建第一个项目
            </Button>
          </CardContent>
        </Card>
      )}

      {!isLoading && projects.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <Link key={project.id} to={`/projects/${project.id}`}>
              <Card className="h-full hover:shadow-lg transition-shadow cursor-pointer">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <CardTitle className="text-xl">{project.name}</CardTitle>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      project.is_active
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {project.is_active ? '活跃' : '归档'}
                    </span>
                  </div>
                  <CardDescription className="line-clamp-2">
                    {project.description || '暂无描述'}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex items-center text-sm text-gray-600">
                    <Code className="h-4 w-4 mr-2" />
                    <span className="capitalize">{project.project_type}</span>
                    {project.language && (
                      <span className="ml-2 text-gray-400">• {project.language}</span>
                    )}
                  </div>
                  <div className="flex items-center text-sm text-gray-600">
                    <Calendar className="h-4 w-4 mr-2" />
                    {formatDateTime(project.created_at)}
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}

      {/* 分页（简化版） */}
      {projects.length > 20 && (
        <div className="flex justify-center gap-2">
          <Button variant="outline">上一页</Button>
          <Button variant="outline">下一页</Button>
        </div>
      )}

      {/* 创建项目对话框 */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>创建新项目</DialogTitle>
            <DialogDescription>
              创建一个新的测试项目，可以上传源代码文件（支持ZIP格式）
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="space-y-4">
              {/* 项目名称 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  项目名称 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="例如：我的C++项目"
                  required
                />
              </div>

              {/* 项目描述 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  项目描述
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder="项目的简要描述..."
                />
              </div>

              {/* 项目类型 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  项目类型 <span className="text-red-500">*</span>
                </label>
                <select
                  value={formData.project_type}
                  onChange={(e) => setFormData({ ...formData, project_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="ui">UI测试</option>
                  <option value="unit">单元测试</option>
                  <option value="integration">集成测试</option>
                  <option value="static">静态分析</option>
                </select>
              </div>

              {/* 编程语言 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  编程语言
                </label>
                <input
                  type="text"
                  value={formData.language}
                  onChange={(e) => setFormData({ ...formData, language: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="例如：cpp, python, java"
                />
              </div>

              {/* 框架 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  框架
                </label>
                <input
                  type="text"
                  value={formData.framework}
                  onChange={(e) => setFormData({ ...formData, framework: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="例如：Qt, GTK, Web"
                />
              </div>

              {/* 源代码文件上传 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  源代码文件（可选）
                </label>
                <div className="mt-1 flex items-center gap-2">
                  <label className="flex-1 cursor-pointer">
                    <input
                      type="file"
                      accept=".zip,.tar,.tar.gz"
                      onChange={handleFileChange}
                      className="hidden"
                    />
                    <div className="flex items-center justify-center px-4 py-2 border-2 border-dashed border-gray-300 rounded-md hover:border-blue-500 transition-colors">
                      <Upload className="h-5 w-5 mr-2 text-gray-400" />
                      <span className="text-sm text-gray-600">
                        {sourceFile ? sourceFile.name : '点击选择文件（支持ZIP格式）'}
                      </span>
                    </div>
                  </label>
                  {sourceFile && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => setSourceFile(null)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  支持ZIP格式，上传后会自动解压
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setCreateDialogOpen(false)
                  resetForm()
                }}
              >
                取消
              </Button>
              <Button type="submit" disabled={isCreating}>
                {isCreating ? '创建中...' : '创建项目'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}

