import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams, useParams, useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Plus, TestTube, Search, Play } from 'lucide-react'
import { testCasesApi, executionsApi, type TestCase } from '@/lib/api'
import TestCaseForm from '@/components/TestCaseForm'

export default function TestCasesPage() {
  const [searchParams] = useSearchParams()
  const { id } = useParams<{ id?: string }>()
  const navigate = useNavigate()
  const projectId = id ? Number(id) : (searchParams.get('project_id') ? Number(searchParams.get('project_id')) : undefined)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingCase, setEditingCase] = useState<TestCase | null>(null)
  const [runningCaseId, setRunningCaseId] = useState<number | null>(null)
  const [searchTerm, setSearchTerm] = useState('')

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['test-cases', projectId],
    queryFn: () => testCasesApi.list({ project_id: projectId }).then(res => res.data),
  })

  const filteredCases = data?.items.filter(case_ => 
    !searchTerm || 
    case_.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    case_.description?.toLowerCase().includes(searchTerm.toLowerCase())
  ) || []

  if (showCreateForm && projectId) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">创建测试用例</h1>
          <Button variant="outline" onClick={() => setShowCreateForm(false)}>
            返回列表
          </Button>
        </div>
        <TestCaseForm 
          projectId={projectId}
          onSuccess={() => {
            setShowCreateForm(false)
            refetch()
          }}
          onCancel={() => setShowCreateForm(false)}
        />
      </div>
    )
  }

  if (editingCase && projectId) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">编辑测试用例</h1>
          <Button variant="outline" onClick={() => setEditingCase(null)}>
            返回列表
          </Button>
        </div>
        <TestCaseForm 
          projectId={projectId}
          testCase={editingCase}
          onSuccess={() => {
            setEditingCase(null)
            refetch()
          }}
          onCancel={() => setEditingCase(null)}
        />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">测试用例</h1>
          <p className="text-gray-600 mt-2">管理和编辑测试用例（Test IR格式）</p>
        </div>
        {projectId ? (
          <Button onClick={() => setShowCreateForm(true)}>
          <Plus className="mr-2 h-4 w-4" />
          创建用例
        </Button>
        ) : (
          <div className="text-sm text-gray-500">
            请先选择一个项目
          </div>
        )}
      </div>

      {/* 搜索和过滤 */}
      {data && data.items.length > 0 && (
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="搜索测试用例..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>
      )}

      {isLoading && (
        <div className="text-center py-12">
          <p className="text-gray-500">加载中...</p>
        </div>
      )}

      {error && (
        <Card>
          <CardContent className="text-center py-12">
            <p className="text-red-500">加载失败，请稍后重试</p>
          </CardContent>
        </Card>
      )}

      {!projectId && (
        <Card>
          <CardContent className="text-center py-12">
            <TestTube className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">请从项目页面选择项目以查看测试用例</p>
          </CardContent>
        </Card>
      )}

      {projectId && data && data.items.length === 0 && (
      <Card>
        <CardContent className="text-center py-12">
          <TestTube className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500 mb-4">暂无测试用例</p>
            <Button onClick={() => setShowCreateForm(true)}>
              <Plus className="mr-2 h-4 w-4" />
              创建第一个测试用例
            </Button>
          </CardContent>
        </Card>
      )}

      {data && filteredCases.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCases.map((testCase: TestCase) => {
            const tool = testCase.test_ir?.tool || 'unknown'
            const toolLabels: Record<string, string> = {
              clazy: 'Clazy',
              cppcheck: 'Cppcheck',
              unknown: '未知工具'
            }
            
            return (
              <Card key={testCase.id} className="h-full hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <CardTitle className="text-lg">{testCase.name}</CardTitle>
                    <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                      {toolLabels[tool] || tool}
                    </span>
                  </div>
                  <CardDescription className="line-clamp-2">
                    {testCase.description || '暂无描述'}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="text-sm text-gray-600">
                    <span className="font-medium">类型:</span> {testCase.test_type}
                  </div>
                  <div className="text-sm text-gray-600">
                    <span className="font-medium">优先级:</span> {testCase.priority}
                  </div>
                  {testCase.test_ir?.target_files?.length > 0 && (
                    <div className="text-sm text-gray-600">
                      <span className="font-medium">目标文件:</span> {testCase.test_ir.target_files.length} 个
                    </div>
                  )}
                  <div className="flex gap-2 pt-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="flex-1"
                      onClick={() => {
                        console.log('点击编辑，测试用例:', testCase);
                        if (!testCase.id) {
                          console.error('测试用例缺少ID:', testCase);
                          alert('错误：测试用例ID不存在');
                          return;
                        }
                        setEditingCase(testCase);
                      }}
                    >
                      编辑
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="flex-1"
                      disabled={runningCaseId === testCase.id}
                      onClick={async () => {
                        if (!projectId) {
                          alert('项目ID不存在');
                          return;
                        }

                        setRunningCaseId(testCase.id);
                        try {
                          // 获取工具类型
                          const executorType = testCase.test_ir?.tool || 'cppcheck';
                          
                          // 创建测试执行
                          const response = await executionsApi.create({
                            project_id: projectId,
                            executor_type: executorType,
                            test_case_ids: [testCase.id]
                          });

                          const execution = response.data;
                          alert(`✅ 测试执行已启动！\n执行ID: ${execution.id}\n状态: ${execution.status}\n工具: ${toolLabels[tool] || tool}\n\n将返回项目页面查看结果...`);
                          
                          // 跳转回项目详情页
                          navigate(`/projects/${projectId}`);
                        } catch (error: any) {
                          console.error('执行失败:', error);
                          const errorMsg = error.response?.data?.detail || error.message || '执行失败，请稍后重试';
                          alert('❌ 执行失败: ' + errorMsg);
                        } finally {
                          setRunningCaseId(null);
                        }
                      }}
                    >
                      {runningCaseId === testCase.id ? (
                        <>运行中...</>
                      ) : (
                        <>
                          <Play className="mr-1 h-3 w-3" />
                          运行
                        </>
                      )}
                    </Button>
                  </div>
        </CardContent>
      </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}

