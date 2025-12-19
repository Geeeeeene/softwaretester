import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { projectsApi, type Project } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Plus, FolderOpen, Calendar, Code } from 'lucide-react'
import { formatDateTime } from '@/lib/utils'
import ProjectForm from '@/components/ProjectForm'

const PROJECT_TYPE_STORAGE_KEY = 'homemade_tester_project_type'

export default function ProjectsPage() {
  // 从 localStorage 读取上次选择的项目类型，如果没有则默认为 undefined（全部项目）
  const [projectType, setProjectType] = useState<string | undefined>(() => {
    const saved = localStorage.getItem(PROJECT_TYPE_STORAGE_KEY)
    return saved ? (saved === 'null' ? undefined : saved) : undefined
  })
  const [showCreateForm, setShowCreateForm] = useState(false)

  // 当 projectType 改变时，保存到 localStorage
  useEffect(() => {
    if (projectType === undefined) {
      localStorage.setItem(PROJECT_TYPE_STORAGE_KEY, 'null')
    } else {
      localStorage.setItem(PROJECT_TYPE_STORAGE_KEY, projectType)
    }
  }, [projectType])

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['projects', projectType],
    queryFn: () => projectsApi.list({ project_type: projectType }).then(res => res.data),
  })

  // 项目类型分类
  const projectTypes = [
    { value: undefined, label: '全部项目' },
    { value: 'ui', label: 'UI测试项目' },
    { value: 'unit', label: '单元测试项目' },
    { value: 'integration', label: '集成测试项目' },
    { value: 'static', label: '静态分析项目' },
  ]

  if (showCreateForm) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">创建新项目</h1>
          <Button variant="outline" onClick={() => setShowCreateForm(false)}>
            返回列表
          </Button>
        </div>
        <ProjectForm 
          onSuccess={(createdProjectType) => {
            setShowCreateForm(false)
            // 根据创建的项目类型，自动切换到对应的分类
            if (createdProjectType) {
              setProjectType(createdProjectType)
            }
            // 刷新项目列表
            refetch()
          }}
          onCancel={() => setShowCreateForm(false)}
        />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 页头 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">项目管理</h1>
          <p className="text-gray-600 mt-2">管理和查看所有测试项目</p>
        </div>
        <Button onClick={() => setShowCreateForm(true)}>
          <Plus className="mr-2 h-4 w-4" />
          创建项目
        </Button>
      </div>

      {/* 项目类型分类筛选 */}
      <div className="flex flex-wrap gap-2 border-b pb-4">
        {projectTypes.map((type) => (
          <button
            key={type.value || 'all'}
            onClick={() => setProjectType(type.value)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              projectType === type.value
                ? 'bg-primary text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
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

      {data && data.items.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <FolderOpen className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">暂无项目</p>
            <Button className="mt-4" onClick={() => setShowCreateForm(true)}>
              <Plus className="mr-2 h-4 w-4" />
              创建第一个项目
            </Button>
          </CardContent>
        </Card>
      )}

      {data && data.items.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {data.items.map((project: Project) => (
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
      {data && data.total > 20 && (
        <div className="flex justify-center gap-2">
          <Button variant="outline">上一页</Button>
          <Button variant="outline">下一页</Button>
        </div>
      )}
    </div>
  )
}

