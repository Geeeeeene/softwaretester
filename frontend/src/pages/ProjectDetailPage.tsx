import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { projectsApi } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ArrowLeft, Edit, Trash2, Play } from 'lucide-react'
import { formatDateTime } from '@/lib/utils'

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()

  const { data: project, isLoading, error } = useQuery({
    queryKey: ['project', id],
    queryFn: () => projectsApi.get(Number(id)).then(res => res.data),
    enabled: !!id,
  })

  if (isLoading) {
    return <div className="text-center py-12">加载中...</div>
  }

  if (error || !project) {
    return <div className="text-center py-12 text-red-500">项目不存在</div>
  }

  return (
    <div className="space-y-6">
      {/* 页头 */}
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <Button variant="ghost" className="mb-4" onClick={() => window.history.back()}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            返回
          </Button>
          <h1 className="text-3xl font-bold text-gray-900">{project.name}</h1>
          <p className="text-gray-600 mt-2">{project.description || '暂无描述'}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Edit className="mr-2 h-4 w-4" />
            编辑
          </Button>
          <Button variant="outline">
            <Play className="mr-2 h-4 w-4" />
            运行测试
          </Button>
          <Button variant="destructive">
            <Trash2 className="mr-2 h-4 w-4" />
            删除
          </Button>
        </div>
      </div>

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
      {(project.source_path || project.binary_path) && (
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

      {/* 统计信息（占位） */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>测试用例</CardTitle>
            <CardDescription>总数</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">0</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>执行记录</CardTitle>
            <CardDescription>总数</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">0</p>
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
    </div>
  )
}

