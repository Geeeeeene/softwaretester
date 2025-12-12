import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { ArrowLeft, Play, Loader2, AlertCircle } from 'lucide-react'
import { FileTree } from '@/components/static-analysis/FileTree'
import { CodeViewer } from '@/components/static-analysis/CodeViewer'
import { AnalysisResults } from '@/components/static-analysis/AnalysisResults'
import { staticAnalysisApi, projectsApi, type FileTreeNode, type FileContent, type StaticAnalysisResult } from '@/lib/api'

export default function StaticAnalysisPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  const projectId = id ? parseInt(id, 10) : null
  const [selectedFile, setSelectedFile] = useState<string | null>(null)

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

  // 获取文件树
  const { data: fileTreeData, isLoading: filesLoading } = useQuery({
    queryKey: ['static-analysis-files', projectId],
    queryFn: async () => {
      if (!projectId) throw new Error('无效的项目ID')
      const response = await staticAnalysisApi.getFiles(projectId)
      return response.data
    },
    enabled: !!projectId && !!project?.source_path,
  })

  // 获取文件内容
  const { data: fileContent, isLoading: contentLoading } = useQuery({
    queryKey: ['static-analysis-file-content', projectId, selectedFile],
    queryFn: async () => {
      if (!projectId || !selectedFile) throw new Error('缺少参数')
      const response = await staticAnalysisApi.getFileContent(projectId, selectedFile)
      return response.data
    },
    enabled: !!projectId && !!selectedFile,
  })

  // 获取分析状态
  const { data: analysisStatus, refetch: refetchStatus } = useQuery({
    queryKey: ['static-analysis-status', projectId],
    queryFn: async () => {
      if (!projectId) throw new Error('无效的项目ID')
      const response = await staticAnalysisApi.getStatus(projectId)
      return response.data
    },
    enabled: !!projectId,
    refetchInterval: 5000, // 每5秒刷新一次状态
  })

  // 获取分析结果
  const { data: analysisResults, refetch: refetchResults } = useQuery({
    queryKey: ['static-analysis-results', projectId],
    queryFn: async () => {
      if (!projectId) throw new Error('无效的项目ID')
      const timestamp = analysisStatus?.latest?.timestamp
      const response = await staticAnalysisApi.getResults(projectId, timestamp)
      return response.data
    },
    enabled: !!projectId && !!analysisStatus?.has_analysis,
  })

  // 启动分析
  const runAnalysisMutation = useMutation({
    mutationFn: async (useLlm: boolean = true) => {
      console.log('开始分析，useLlm:', useLlm, 'projectId:', projectId)
      if (!projectId) throw new Error('无效的项目ID')
      return staticAnalysisApi.run(projectId, useLlm, project?.language)
    },
    onSuccess: (data) => {
      console.log('分析启动成功:', data)
      // 显示成功提示
      alert('✅ 分析任务已提交，正在后台执行中...\n请稍候，系统会自动更新分析状态。')
      queryClient.invalidateQueries({ queryKey: ['static-analysis-status', projectId] })
      // 开始轮询状态
      setTimeout(() => {
        refetchStatus()
      }, 2000)
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || error.message || '未知错误'
      // 将换行符转换为空格，以便在alert中正确显示
      const formattedMessage = errorMessage.replace(/\n/g, ' ')
      console.error('分析失败:', error)
      alert(`启动分析失败: ${formattedMessage}`)
    },
  })

  // 处理问题点击
  const handleIssueClick = (filePath: string, lineNumber: number) => {
    setSelectedFile(filePath)
    // CodeViewer 会自动滚动到对应行
  }

  // 处理文件选择
  const handleFileSelect = (filePath: string) => {
    setSelectedFile(filePath)
  }

  // 收集当前文件的问题
  const currentFileIssues = selectedFile && analysisResults?.results
    ? Object.entries(analysisResults.results.file_results || {})
        .filter(([path]) => path === selectedFile)
        .flatMap(([, result]: [string, any]) => result.issues || [])
    : []

  if (!projectId) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 mx-auto text-red-400 mb-4" />
        <p className="text-red-500 text-lg">无效的项目ID</p>
        <Button className="mt-4" onClick={() => navigate('/projects')}>
          返回项目列表
        </Button>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <Loader2 className="h-8 w-8 mx-auto text-gray-400 animate-spin mb-4" />
        <p className="text-gray-500">加载中...</p>
      </div>
    )
  }

  if (!project.source_path) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 mx-auto text-red-400 mb-4" />
        <p className="text-red-500 text-lg">项目未上传源代码</p>
        <Button className="mt-4" onClick={() => navigate(`/projects/${projectId}`)}>
          返回项目详情
        </Button>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* 顶部工具栏 */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={() => navigate(`/projects/${projectId}`)}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              返回
            </Button>
            <div>
              <h1 className="text-xl font-bold text-gray-900">{project.name} - 静态分析</h1>
              <p className="text-sm text-gray-600 mt-1">
                {analysisStatus?.has_analysis
                  ? `已分析 ${analysisStatus.latest?.summary?.total_files || 0} 个文件，发现 ${analysisStatus.latest?.summary?.total_issues || 0} 个问题`
                  : '尚未进行静态分析'}
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            {!analysisStatus?.has_analysis ? (
              <>
                <Button
                  onClick={() => runAnalysisMutation.mutate(true)}
                  disabled={runAnalysisMutation.isPending}
                >
                  {runAnalysisMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      分析中...
                    </>
                  ) : (
                    <>
                      <Play className="mr-2 h-4 w-4" />
                      开始分析（含大模型）
                    </>
                  )}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    console.log('点击开始分析（仅工具）按钮')
                    runAnalysisMutation.mutate(false)
                  }}
                  disabled={runAnalysisMutation.isPending}
                >
                  <Play className="mr-2 h-4 w-4" />
                  开始分析（仅工具）
                </Button>
              </>
            ) : (
              <>
                <Button
                  onClick={() => {
                    console.log('点击重新分析（含大模型）按钮', {
                      isPending: runAnalysisMutation.isPending,
                      projectId,
                      hasAnalysis: analysisStatus?.has_analysis
                    })
                    runAnalysisMutation.mutate(true)
                  }}
                  disabled={runAnalysisMutation.isPending}
                  variant="outline"
                  style={{ cursor: runAnalysisMutation.isPending ? 'not-allowed' : 'pointer' }}
                >
                  {runAnalysisMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      重新分析中...
                    </>
                  ) : (
                    <>
                      <Play className="mr-2 h-4 w-4" />
                      重新分析（含大模型）
                    </>
                  )}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    console.log('点击重新分析（仅工具）按钮')
                    runAnalysisMutation.mutate(false)
                  }}
                  disabled={runAnalysisMutation.isPending}
                  style={{ cursor: runAnalysisMutation.isPending ? 'not-allowed' : 'pointer' }}
                >
                  <Play className="mr-2 h-4 w-4" />
                  重新分析（仅工具）
                </Button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* 三栏布局 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧：文件树 */}
        <div className="w-64 flex-shrink-0">
          {filesLoading ? (
            <div className="h-full flex items-center justify-center">
              <Loader2 className="h-6 w-6 text-gray-400 animate-spin" />
            </div>
          ) : (
            <FileTree
              tree={fileTreeData?.file_tree || []}
              selectedPath={selectedFile || undefined}
              onFileSelect={handleFileSelect}
            />
          )}
        </div>

        {/* 中间：代码预览 */}
        <div className="flex-1 flex-shrink-0">
          {contentLoading ? (
            <div className="h-full flex items-center justify-center">
              <Loader2 className="h-6 w-6 text-gray-400 animate-spin" />
            </div>
          ) : (
            <CodeViewer
              fileContent={fileContent}
              issues={currentFileIssues}
              onLineClick={(lineNumber) => {
                // 可以在这里添加额外的处理
              }}
            />
          )}
        </div>

        {/* 右侧：分析结果 */}
        <div className="w-96 flex-shrink-0">
          <AnalysisResults
            results={analysisResults}
            onIssueClick={handleIssueClick}
          />
        </div>
      </div>
    </div>
  )
}

