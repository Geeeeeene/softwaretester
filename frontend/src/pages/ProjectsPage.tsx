import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Plus, FolderOpen, Calendar, Code, Upload, X, Search, CheckCircle2, XCircle, AlertCircle, Loader2 } from 'lucide-react'
import { formatDateTime } from '@/lib/utils'
import { projectsApi, executionsApi, type Project, type ProjectCreate } from '@/lib/api'
import type { AxiosResponse } from 'axios'
import { UploadDashboard } from '@/components/projects/UploadDashboard'
import { BatchUploadDialog } from '@/components/projects/BatchUploadDialog'

interface ProjectWithExecution extends Project {
  latestExecution?: {
    id: number
    status: string
    passed_tests: number
    failed_tests: number
    total_tests: number
  }
}

export default function ProjectsPage() {
  const [projectType, setProjectType] = useState<string | undefined>()
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [batchUploadDialogOpen, setBatchUploadDialogOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<'name' | 'created_at'>('created_at')
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // 获取项目列表
  const { data: projectsData, isLoading, error } = useQuery({
    queryKey: ['projects', projectType, sortBy],
    queryFn: async () => {
      const response = await projectsApi.list({
        project_type: projectType,
        skip: 0,
        limit: 100, // 暂时不实现分页，显示所有项目
      })
      return response.data
    },
  })

  // 获取每个项目的最新执行结果
  const projects = projectsData?.items || []
  const projectIds = projects.map(p => p.id)
  
  const { data: executionsMap } = useQuery({
    queryKey: ['executions', 'latest', projectIds],
    queryFn: async () => {
      const executions: Record<number, any> = {}
      // 为每个项目获取最新执行记录
      await Promise.all(
        projectIds.map(async (projectId) => {
          try {
            const response = await executionsApi.list({
              project_id: projectId,
              limit: 1,
            })
            if (response.data && response.data.length > 0) {
              executions[projectId] = response.data[0]
            }
          } catch (error) {
            console.error(`获取项目 ${projectId} 的执行记录失败:`, error)
          }
        })
      )
      return executions
    },
    enabled: projectIds.length > 0,
  })

  // 合并项目和执行结果
  const projectsWithExecution: ProjectWithExecution[] = projects.map(project => ({
    ...project,
    latestExecution: executionsMap?.[project.id],
  }))

  // 过滤和排序项目
  const filteredProjects = projectsWithExecution
    .filter(project => {
      if (searchQuery) {
        const query = searchQuery.toLowerCase()
        return (
          project.name.toLowerCase().includes(query) ||
          project.description?.toLowerCase().includes(query) ||
          project.language?.toLowerCase().includes(query)
        )
      }
      return true
    })
    .sort((a, b) => {
      if (sortBy === 'name') {
        return a.name.localeCompare(b.name)
      } else {
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      }
    })

  // 创建项目
  const createMutation = useMutation({
    mutationFn: async (data: ProjectCreate & { file?: File }) => {
      if (data.file) {
        const formData = new FormData()
        formData.append('name', data.name)
        formData.append('description', data.description || '')
        formData.append('project_type', data.project_type)
        formData.append('language', data.language || '')
        formData.append('framework', data.framework || '')
        formData.append('source_file', data.file)
        return projectsApi.createWithFile(formData)
      } else {
        return projectsApi.create(data)
      }
    },
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setCreateDialogOpen(false)
      resetForm()
      // 跳转到项目详情页
      navigate(`/projects/${response.data.id}`)
    },
    onError: (error: any) => {
      console.error('创建项目失败:', error)
      console.error('错误详情:', {
        message: error.message,
        response: error.response,
        status: error.response?.status,
        data: error.response?.data,
        request: error.config
      })
      const errorMessage = error.response?.data?.detail || error.message || '创建项目失败，请重试'
      alert(errorMessage)
    },
  })

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    project_type: 'unit',
    language: '',
    framework: '',
  })
  const [sourceFile, setSourceFile] = useState<File | null>(null)

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

  const handleCreateProject = async () => {
    if (!formData.name.trim()) {
      alert('请输入项目名称')
      return
    }
    if (!formData.project_type) {
      alert('请选择项目类型')
      return
    }

    createMutation.mutate({
      name: formData.name,
      description: formData.description || undefined,
      project_type: formData.project_type,
      language: formData.language || undefined,
      framework: formData.framework || undefined,
      file: sourceFile || undefined,
    })
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

  const getExecutionStatusIcon = (execution?: ProjectWithExecution['latestExecution']) => {
    if (!execution) return null
    
    if (execution.status === 'completed' && execution.failed_tests === 0) {
      return <CheckCircle2 className="h-4 w-4 text-green-500" />
    } else if (execution.status === 'completed' && execution.failed_tests > 0) {
      return <XCircle className="h-4 w-4 text-red-500" />
    } else if (execution.status === 'failed' || execution.status === 'error') {
      return <AlertCircle className="h-4 w-4 text-red-500" />
    } else if (execution.status === 'running') {
      return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
    }
    return null
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
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setBatchUploadDialogOpen(true)}>
            <Upload className="mr-2 h-4 w-4" />
            批量导入 ZIP
          </Button>
          <Button onClick={() => setCreateDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            创建项目
          </Button>
        </div>
      </div>

      {/* 上传管理区 */}
      <UploadDashboard />

      {/* 搜索和过滤器 */}
      <div className="flex gap-4 items-center">
        {/* 搜索框 */}
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="搜索项目名称、描述或语言..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* 排序 */}
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as 'name' | 'created_at')}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="created_at">按创建时间</option>
          <option value="name">按名称</option>
        </select>

        {/* 类型过滤器 */}
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
      </div>

      {/* 项目列表 */}
      {isLoading && (
        <div className="text-center py-12">
          <Loader2 className="h-8 w-8 mx-auto text-gray-400 animate-spin mb-4" />
          <p className="text-gray-500">加载中...</p>
        </div>
      )}

      {error && (
        <div className="text-center py-12">
          <AlertCircle className="h-12 w-12 mx-auto text-red-400 mb-4" />
          <p className="text-red-500">加载失败，请稍后重试</p>
        </div>
      )}

      {!isLoading && !error && filteredProjects.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <FolderOpen className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">
              {searchQuery ? '未找到匹配的项目' : '暂无项目'}
            </p>
            <Button className="mt-4" onClick={() => setCreateDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              创建第一个项目
            </Button>
          </CardContent>
        </Card>
      )}

      {!isLoading && !error && filteredProjects.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map((project) => (
            <Link key={project.id} to={`/projects/${project.id}`}>
              <Card className="h-full hover:shadow-lg transition-shadow cursor-pointer">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <CardTitle className="text-xl">{project.name}</CardTitle>
                    <div className="flex items-center gap-2">
                      {getExecutionStatusIcon(project.latestExecution)}
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        project.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {project.is_active ? '活跃' : '归档'}
                      </span>
                    </div>
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
                  {project.latestExecution && (
                    <div className="flex items-center text-sm text-gray-600">
                      <div className="flex items-center gap-2">
                        {getExecutionStatusIcon(project.latestExecution)}
                        <span>
                          最近执行: {project.latestExecution.passed_tests}/{project.latestExecution.total_tests} 通过
                        </span>
                      </div>
                    </div>
                  )}
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
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    创建中...
                  </>
                ) : (
                  '创建项目'
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* 批量上传对话框 */}
      <BatchUploadDialog
        open={batchUploadDialogOpen}
        onOpenChange={setBatchUploadDialogOpen}
      />
    </div>
  )
}
