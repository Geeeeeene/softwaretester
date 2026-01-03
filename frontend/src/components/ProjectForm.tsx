import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { api, projectsApi, uploadApi, type ProjectCreate } from '@/lib/api'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'

interface ProjectFormProps {
  onSuccess?: (projectType?: string) => void
  onCancel?: () => void
}

export default function ProjectForm({ onSuccess, onCancel }: ProjectFormProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [projectType, setProjectType] = useState<string>('static')
  const [language, setLanguage] = useState('')
  const [framework, setFramework] = useState('')
  const [sourcePath, setSourcePath] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  
  // 静态分析特有状态
  const [staticTool, setStaticTool] = useState<string>('cppcheck')
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const projectTypes = [
    { value: 'ui', label: '系统测试', description: '用于系统自动化测试' },
    { value: 'unit', label: '单元测试', description: '用于单元测试生成和执行' },
    { value: 'integration', label: '集成测试', description: '用于集成测试' },
    { value: 'static', label: '静态分析', description: '上传源码包进行代码分析' },
  ]

  const staticTools = [
    { value: 'cppcheck', label: 'Cppcheck', description: 'C/C++ 代码静态分析工具' },
    { value: 'clazy', label: 'Clazy', description: 'Qt/C++ 静态分析工具' },
  ]

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      if (projectType === 'static' || projectType === 'unit' || projectType === 'integration') {
        // 静态分析、单元测试和集成测试现在统一走"一键上传 ZIP"流程
        if (!uploadFile) {
          throw new Error('请上传源代码压缩包')
        }
        
        let res;
        if (projectType === 'static') {
          res = await uploadApi.uploadStaticZip(
            uploadFile,
            name.trim(),
            description.trim() || undefined,
            staticTool
          )
        } else if (projectType === 'unit') {
          // 调用刚才新建的后端 unit-zip 接口
          const formData = new FormData()
          formData.append('file', uploadFile)
          formData.append('name', name.trim())
          if (description) formData.append('description', description.trim())
          res = await api.post('/upload/unit-zip', formData)
        } else if (projectType === 'integration') {
          // 集成测试项目：使用FormData方式创建项目并上传源代码
          const formData = new FormData()
          formData.append('source_file', uploadFile) // 使用source_file字段名，与后端匹配
          formData.append('name', name.trim())
          if (description) formData.append('description', description.trim())
          formData.append('project_type', projectType)
          formData.append('language', 'cpp') // 集成测试默认使用C++
          formData.append('extract', 'true')
          
          // 直接调用项目创建API，使用FormData方式
          const createRes = await api.post('/projects', formData)
          // 后端返回的是Project对象，使用id字段
          res = { data: { project_id: createRes.data.id } }
        }
        
        const { project_id } = res.data as any
        
        // 刷新项目列表缓存，确保新项目会被显示
        // 不等待refetch完成，避免阻塞
        console.log('[创建项目] 刷新项目列表缓存...')
        queryClient.invalidateQueries({ queryKey: ['projects'] })
        // 不等待refetch，让它在后台进行
        queryClient.refetchQueries({ queryKey: ['projects'] }).catch(err => {
          console.warn('[创建项目] 刷新项目列表失败（不影响创建）:', err)
        })
        
        if (onSuccess) onSuccess()
        navigate(`/projects/${project_id}`)
      } else if (projectType === 'ui') {
        // 系统测试项目流程
        if (!sourcePath.trim()) {
          throw new Error('系统测试项目需要指定应用程序路径')
        }
        
        const project: ProjectCreate = {
          name: name.trim(),
          description: description.trim() || undefined,
          project_type: projectType,
          source_path: sourcePath.trim(),
        }

        console.log('[创建项目] 开始创建项目...', project)
        const startTime = Date.now()
        const res = await projectsApi.create(project)
        const createTime = Date.now() - startTime
        console.log('[创建项目] ✅ 项目创建成功，耗时:', createTime, 'ms', res.data)
        
        // 在跳转前刷新项目列表缓存，确保新项目会被显示
        // 使用 invalidateQueries 来刷新所有项目列表查询（包括不同 project_type 的查询）
        // 不等待refetch完成，避免阻塞
        console.log('[创建项目] 刷新项目列表缓存...')
        queryClient.invalidateQueries({ queryKey: ['projects'] })
        // 不等待refetch，让它在后台进行
        queryClient.refetchQueries({ queryKey: ['projects'] }).catch(err => {
          console.warn('[创建项目] 刷新项目列表失败（不影响创建）:', err)
        })
        
        // 调用 onSuccess 回调（在跳转前调用，确保能执行）
        if (onSuccess) {
          onSuccess(projectType)
        }
        
        // 跳转到系统测试页面
        navigate(`/projects/${res.data.id}/system-test`)
      } else {
        // 其他项目类型保持普通创建流程
        const project: ProjectCreate = {
          name: name.trim(),
          description: description.trim() || undefined,
          project_type: projectType,
          language: language.trim() || undefined,
          framework: framework.trim() || undefined,
          source_path: sourcePath.trim() || undefined,
        }

        console.log('[创建项目] 开始创建项目...', project)
        const startTime = Date.now()
        const res = await projectsApi.create(project)
        const createTime = Date.now() - startTime
        console.log('[创建项目] ✅ 项目创建成功，耗时:', createTime, 'ms')
        
        // 刷新项目列表缓存，确保新项目会被显示
        // 不等待refetch完成，避免阻塞
        console.log('[创建项目] 刷新项目列表缓存...')
        queryClient.invalidateQueries({ queryKey: ['projects'] })
        // 不等待refetch，让它在后台进行
        queryClient.refetchQueries({ queryKey: ['projects'] }).catch(err => {
          console.warn('[创建项目] 刷新项目列表失败（不影响创建）:', err)
        })
        
        const { id: createdProjectId } = res.data as any
        if (onSuccess) {
          onSuccess(projectType)
        }
        navigate(`/projects/${createdProjectId}`)
      }
    } catch (error: any) {
      console.error('创建项目失败:', error)
      const errorMessage = error.response?.data?.detail || error.message || '创建项目失败'
      alert(errorMessage)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>创建新项目</CardTitle>
        <CardDescription>创建一个新的测试项目</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 基本信息 */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                项目名称 *
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="例如：我的测试项目"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                项目描述
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="项目的简要描述..."
              />
            </div>
          </div>

          {/* 项目类型 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              项目类型 *
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {projectTypes.map((type) => (
                <div
                  key={type.value}
                  onClick={() => setProjectType(type.value)}
                  className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                    projectType === type.value
                      ? 'border-primary bg-primary/5'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-start">
                    <input
                      type="radio"
                      name="projectType"
                      value={type.value}
                      checked={projectType === type.value}
                      onChange={() => setProjectType(type.value)}
                      className="mt-1 mr-3"
                    />
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">{type.label}</div>
                      <div className="text-sm text-gray-500 mt-1">{type.description}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 静态分析、单元测试或集成测试特有配置 */}
          {(projectType === 'static' || projectType === 'unit' || projectType === 'integration') && (
            <div className="space-y-4 border-t pt-4">
              <h3 className="text-sm font-medium text-gray-900">
                {projectType === 'static' ? '静态分析配置' : projectType === 'unit' ? '单元测试配置' : '集成测试配置'}
              </h3>
              
              {/* 文件上传 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  源代码压缩包 (.zip) *
                </label>
                <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md hover:border-primary transition-colors">
                  <div className="space-y-1 text-center">
                    <svg
                      className="mx-auto h-12 w-12 text-gray-400"
                      stroke="currentColor"
                      fill="none"
                      viewBox="0 0 48 48"
                      aria-hidden="true"
                    >
                      <path
                        d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                        strokeWidth={2}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                    <div className="flex text-sm text-gray-600">
                      <label
                        htmlFor="file-upload"
                        className="relative cursor-pointer bg-white rounded-md font-medium text-primary hover:text-primary-dark focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-primary"
                      >
                        <span>上传文件</span>
                        <input
                          id="file-upload"
                          name="file-upload"
                          type="file"
                          accept=".zip"
                          className="sr-only"
                          onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                        />
                      </label>
                      <p className="pl-1">或拖拽文件到这里</p>
                    </div>
                    <p className="text-xs text-gray-500">
                      {uploadFile ? `已选择: ${uploadFile.name}` : '仅支持 ZIP 格式，最大 100MB'}
                    </p>
                  </div>
                </div>
              </div>

              {/* 工具选择 */}
              {projectType === 'static' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    分析工具
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {staticTools.map((tool) => (
                      <div
                        key={tool.value}
                        onClick={() => setStaticTool(tool.value)}
                        className={`p-3 border rounded-md cursor-pointer flex items-center ${
                          staticTool === tool.value
                            ? 'border-primary bg-primary/5 ring-1 ring-primary'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <input
                          type="radio"
                          name="staticTool"
                          value={tool.value}
                          checked={staticTool === tool.value}
                          onChange={() => setStaticTool(tool.value)}
                          className="mr-3 text-primary focus:ring-primary"
                        />
                        <div>
                          <div className="text-sm font-medium text-gray-900">{tool.label}</div>
                          <div className="text-xs text-gray-500">{tool.description}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* UI测试配置 */}
          {projectType === 'ui' && (
            <div className="space-y-4 border-t pt-4">
              <h3 className="text-sm font-medium text-gray-900">系统测试配置</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  应用程序路径 *
                </label>
                <input
                  type="text"
                  value={sourcePath}
                  onChange={(e) => setSourcePath(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="例如：D:\路径\应用程序.exe 或 C:\Program Files\MyApp\app.exe"
                />
                <p className="text-xs text-gray-500 mt-1">
                  指定待测试应用程序的可执行文件（.exe）完整路径。系统将使用此路径启动应用程序进行UI自动化测试。
                  <br />
                  <span className="text-gray-400">提示：请确保路径指向实际存在的.exe文件，支持Windows绝对路径格式。</span>
                </p>
              </div>
            </div>
          )}

          {/* 其他类型保持原样（技术栈等） */}
          {projectType !== 'static' && projectType !== 'ui' && projectType !== 'unit' && projectType !== 'integration' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  编程语言
                </label>
                <input
                  type="text"
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="例如：C++, Python"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  框架
                </label>
                <input
                  type="text"
                  value={framework}
                  onChange={(e) => setFramework(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="例如：Qt, React"
                />
              </div>
            </div>
          )}
          
          {projectType !== 'static' && projectType !== 'ui' && projectType !== 'unit' && projectType !== 'integration' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                源代码路径
              </label>
              <input
                type="text"
                value={sourcePath}
                onChange={(e) => setSourcePath(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="例如：./src 或 /path/to/source"
              />
              <p className="text-xs text-gray-500 mt-1">可选：指定项目源代码的路径</p>
            </div>
          )}

          {/* 操作按钮 */}
          <div className="flex justify-end gap-2 pt-4">
            {onCancel && (
              <Button type="button" variant="outline" onClick={onCancel}>
                取消
              </Button>
            )}
            <Button type="submit" disabled={isSubmitting || !name.trim() || ((projectType === 'static' || projectType === 'unit' || projectType === 'integration') && !uploadFile) || (projectType === 'ui' && !sourcePath.trim())}>
              {isSubmitting ? '处理中...' : ((projectType === 'static' || projectType === 'unit' || projectType === 'integration') ? '上传并完成创建' : projectType === 'ui' ? '创建项目' : '创建项目')}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}


