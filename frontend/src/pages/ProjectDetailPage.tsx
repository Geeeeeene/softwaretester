import { useState } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { ArrowLeft, Edit, Trash2, AlertCircle, Loader2 } from 'lucide-react'
import { projectsApi, type Project } from '@/lib/api'
import type { AxiosResponse } from 'axios'
import { ProjectOverviewTab } from '@/components/project-detail/ProjectOverviewTab'
import { SourceBuildTab } from '@/components/project-detail/SourceBuildTab'
import { TestCasesTab } from '@/components/project-detail/TestCasesTab'
import { ExecutionTab } from '@/components/project-detail/ExecutionTab'
import { ReportsTab } from '@/components/project-detail/ReportsTab'

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const queryClient = useQueryClient()
  
  // 从URL获取当前Tab，默认为overview
  const currentTab = searchParams.get('tab') || 'overview'
  
  // 项目ID（如果是数字ID，说明是后端项目）
  const projectId = id && !id.startsWith('project_') ? parseInt(id, 10) : null

  // 调试信息
  console.log('ProjectDetailPage - id:', id, 'projectId:', projectId)

  // 获取项目数据
  const { data: project, isLoading, error } = useQuery({
    queryKey: ['project', projectId],
    queryFn: async () => {
      if (!projectId || isNaN(projectId)) {
        throw new Error('无效的项目ID')
      }
      console.log('正在获取项目数据，projectId:', projectId)
      const response = await projectsApi.get(projectId)
      console.log('项目数据获取成功:', response.data)
      return response.data
    },
    enabled: !!projectId && !isNaN(projectId),
  })
  
  console.log('ProjectDetailPage - isLoading:', isLoading, 'error:', error, 'project:', project)

  // 删除项目
  const deleteMutation = useMutation({
    mutationFn: async () => {
      if (!projectId) throw new Error('无效的项目ID')
      return projectsApi.delete(projectId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      navigate('/projects')
    },
    onError: (error: any) => {
      alert(`删除失败: ${error.response?.data?.detail || error.message || '未知错误'}`)
    },
  })

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)

  // Tab切换处理
  const handleTabChange = (value: string) => {
    setSearchParams({ tab: value })
  }

  // 导航到指定Tab（带参数）
  const handleNavigateToTab = (tab: string, params?: Record<string, any>) => {
    const newParams = new URLSearchParams()
    newParams.set('tab', tab)
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        newParams.set(key, value)
      })
    }
    setSearchParams(newParams)
  }

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <Loader2 className="h-8 w-8 mx-auto text-gray-400 animate-spin mb-4" />
        <p className="text-gray-500">加载中...</p>
      </div>
    )
  }

  if (error) {
    console.error('加载项目失败:', error)
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 mx-auto text-red-400 mb-4" />
        <p className="text-red-500 text-lg">项目加载失败</p>
        <p className="text-red-400 text-sm mt-2">
          {error instanceof Error ? error.message : '未知错误'}
        </p>
        <Button className="mt-4" onClick={() => navigate('/projects')}>
          返回项目列表
        </Button>
      </div>
    )
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

      {/* Tab导航 */}
      <Tabs value={currentTab} onValueChange={handleTabChange} className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">概览</TabsTrigger>
          <TabsTrigger value="source-build">源码与构建</TabsTrigger>
          <TabsTrigger value="test-cases">测试用例</TabsTrigger>
          <TabsTrigger value="execution">执行</TabsTrigger>
          <TabsTrigger value="reports">报告</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6">
          <ProjectOverviewTab project={project} onNavigateToTab={handleNavigateToTab} />
        </TabsContent>

        <TabsContent value="source-build" className="mt-6">
          <SourceBuildTab projectId={project.id} project={project} />
        </TabsContent>

        <TabsContent value="test-cases" className="mt-6">
          <TestCasesTab projectId={project.id} />
        </TabsContent>

        <TabsContent value="execution" className="mt-6">
          <ExecutionTab projectId={project.id} onNavigateToTab={handleNavigateToTab} />
        </TabsContent>

        <TabsContent value="reports" className="mt-6">
          <ReportsTab projectId={project.id} />
        </TabsContent>
      </Tabs>

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
            <Button
              variant="destructive"
              onClick={() => {
                deleteMutation.mutate()
                setDeleteDialogOpen(false)
              }}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  删除中...
                </>
              ) : (
                '删除'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
