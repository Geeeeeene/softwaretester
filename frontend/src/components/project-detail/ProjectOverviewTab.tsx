import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { TestTube, BarChart3, Play, Upload, FileCode, CheckCircle2, XCircle, AlertCircle, Loader2 } from 'lucide-react'
import type { Project } from '@/lib/api'
import { ToolStatusIndicator } from '@/components/ToolStatusIndicator'

interface ProjectOverviewTabProps {
  project: Project
  onNavigateToTab: (tab: string) => void
}

export function ProjectOverviewTab({ project, onNavigateToTab }: ProjectOverviewTabProps) {
  return (
    <div className="space-y-6">
      {/* 项目信息卡片 */}
      <Card>
        <CardHeader>
          <CardTitle>项目信息</CardTitle>
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
            <p className="text-sm text-gray-500">源码状态</p>
            <p className="text-base font-medium">
              {project.source_path ? (
                <span className="text-green-600 flex items-center gap-1">
                  <CheckCircle2 className="h-4 w-4" />
                  已上传
                </span>
              ) : (
                <span className="text-gray-400">未上传</span>
              )}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">构建状态</p>
            <p className="text-base font-medium text-gray-400">待构建</p>
          </div>
        </CardContent>
      </Card>

      {/* 关键质量指标 */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle>关键质量指标</CardTitle>
            <ToolStatusIndicator />
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-500">用例总数</p>
              <p className="text-2xl font-bold">0</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">最近通过率</p>
              <p className="text-2xl font-bold">--%</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">覆盖率</p>
              <p className="text-2xl font-bold">--%</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">内存问题</p>
              <p className="text-2xl font-bold">0</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 快捷入口 */}
      <Card>
        <CardHeader>
          <CardTitle>快捷操作</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button
              variant="outline"
              className="h-auto p-4 flex flex-col items-center gap-2"
              onClick={() => onNavigateToTab('source-build')}
            >
              <Upload className="h-6 w-6" />
              <span className="font-medium">上传源代码</span>
            </Button>
            <Button
              variant="outline"
              className="h-auto p-4 flex flex-col items-center gap-2"
              onClick={() => onNavigateToTab('test-cases')}
            >
              <TestTube className="h-6 w-6" />
              <span className="font-medium">创建测试用例</span>
            </Button>
            <Button
              variant="outline"
              className="h-auto p-4 flex flex-col items-center gap-2"
              onClick={() => onNavigateToTab('execution')}
            >
              <Play className="h-6 w-6" />
              <span className="font-medium">执行测试</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 最近活动 */}
      <Card>
        <CardHeader>
          <CardTitle>最近活动</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500">
            暂无活动记录
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

