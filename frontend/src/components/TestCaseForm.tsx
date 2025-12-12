import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { testCasesApi, type TestCaseCreate, type TestCase } from '@/lib/api'

interface TestCaseFormProps {
  projectId: number
  testCase?: TestCase | null
  onSuccess?: () => void
  onCancel?: () => void
}

export default function TestCaseForm({ projectId, testCase, onSuccess, onCancel }: TestCaseFormProps) {
  const isEditMode = !!testCase
  const [tool, setTool] = useState<string>('cppcheck')
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [targetFiles, setTargetFiles] = useState<string[]>([''])
  const [targetDirs, setTargetDirs] = useState<string[]>([''])
  const [checks, setChecks] = useState<string>('level1')
  const [enable, setEnable] = useState<string>('all')
  const [isSubmitting, setIsSubmitting] = useState(false)

  // 如果是编辑模式，加载现有数据
  useEffect(() => {
    if (testCase) {
      console.log('加载测试用例数据:', testCase)
      setName(testCase.name || '')
      setDescription(testCase.description || '')
      const testIR = testCase.test_ir || {}
      setTool(testIR.tool || 'cppcheck')
      setTargetFiles(testIR.target_files && testIR.target_files.length > 0 ? testIR.target_files : [''])
      setTargetDirs(testIR.target_directories && testIR.target_directories.length > 0 ? testIR.target_directories : [''])
      setChecks(testIR.checks?.[0] || 'level1')
      setEnable(testIR.enable || 'all')
    }
  }, [testCase])

  const staticAnalysisTools = [
    { value: 'clazy', label: 'Clazy - Qt 静态分析', description: '用于 Qt 代码的静态分析工具' },
    { value: 'cppcheck', label: 'Cppcheck - C/C++ 静态分析', description: '用于 C/C++ 代码的静态分析工具' },
  ]

  const handleAddFile = () => {
    setTargetFiles([...targetFiles, ''])
  }

  const handleRemoveFile = (index: number) => {
    setTargetFiles(targetFiles.filter((_, i) => i !== index))
  }

  const handleFileChange = (index: number, value: string) => {
    const newFiles = [...targetFiles]
    newFiles[index] = value
    setTargetFiles(newFiles)
  }

  const handleAddDir = () => {
    setTargetDirs([...targetDirs, ''])
  }

  const handleRemoveDir = (index: number) => {
    setTargetDirs(targetDirs.filter((_, i) => i !== index))
  }

  const handleDirChange = (index: number, value: string) => {
    const newDirs = [...targetDirs]
    newDirs[index] = value
    setTargetDirs(newDirs)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      // 构建 Test IR
      const testIR: any = {
        type: 'static',
        tool: tool,
        name: name,
        description: description || undefined,
        target_files: targetFiles.filter(f => f.trim()),
        target_directories: targetDirs.filter(d => d.trim()),
        rules: [],
        exclude_patterns: [],
        tags: [],
      }

      // 根据工具添加特定配置
      if (tool === 'clazy') {
        testIR.checks = [checks]
      } else if (tool === 'cppcheck') {
        testIR.enable = enable
      }

      const testCase: TestCaseCreate = {
        project_id: projectId,
        name: name,
        description: description || undefined,
        test_type: 'static',
        test_ir: testIR,
        priority: 'medium',
        tags: [],
      }

      if (isEditMode && testCase?.id) {
        // 更新现有测试用例
        console.log('更新测试用例:', testCase.id, { name, description, test_ir: testIR })
        await testCasesApi.update(testCase.id, {
          name: name,
          description: description || undefined,
          test_ir: testIR,
          priority: 'medium',
          tags: [],
        })
      } else {
        // 创建新测试用例
        console.log('创建测试用例:', testCase)
        await testCasesApi.create(testCase)
      }
      
      if (onSuccess) {
        onSuccess()
      }
      
      // 如果不是编辑模式，重置表单
      if (!isEditMode) {
        setName('')
        setDescription('')
        setTargetFiles([''])
        setTargetDirs([''])
      }
    } catch (error) {
      console.error('创建测试用例失败:', error)
      alert('创建测试用例失败，请检查输入')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{isEditMode ? '编辑测试用例' : '创建测试用例'}</CardTitle>
        <CardDescription>{isEditMode ? '编辑静态分析测试用例' : '创建静态分析测试用例'}</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 基本信息 */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                测试用例名称 *
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="例如：代码质量检查"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                描述
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="测试用例描述..."
              />
            </div>
          </div>

          {/* 工具选择 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              静态分析工具 *
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {staticAnalysisTools.map((t) => (
                <div
                  key={t.value}
                  onClick={() => setTool(t.value)}
                  className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                    tool === t.value
                      ? 'border-primary bg-primary/5'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-start">
                    <input
                      type="radio"
                      name="tool"
                      value={t.value}
                      checked={tool === t.value}
                      onChange={() => setTool(t.value)}
                      className="mt-1 mr-3"
                    />
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">{t.label}</div>
                      <div className="text-sm text-gray-500 mt-1">{t.description}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 目标文件 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              目标文件
            </label>
            <div className="space-y-2">
              {targetFiles.map((file, index) => (
                <div key={index} className="flex gap-2">
                  <input
                    type="text"
                    value={file}
                    onChange={(e) => handleFileChange(index, e.target.value)}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="例如：src/main.cpp 或 src/**/*.cpp"
                  />
                  {targetFiles.length > 1 && (
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => handleRemoveFile(index)}
                    >
                      删除
                    </Button>
                  )}
                </div>
              ))}
              <Button
                type="button"
                variant="outline"
                onClick={handleAddFile}
                className="w-full"
              >
                + 添加文件
              </Button>
            </div>
          </div>

          {/* 目标目录 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              目标目录
            </label>
            <div className="space-y-2">
              {targetDirs.map((dir, index) => (
                <div key={index} className="flex gap-2">
                  <input
                    type="text"
                    value={dir}
                    onChange={(e) => handleDirChange(index, e.target.value)}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="例如：src/core"
                  />
                  {targetDirs.length > 1 && (
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => handleRemoveDir(index)}
                    >
                      删除
                    </Button>
                  )}
                </div>
              ))}
              <Button
                type="button"
                variant="outline"
                onClick={handleAddDir}
                className="w-full"
              >
                + 添加目录
              </Button>
            </div>
          </div>

          {/* 工具特定配置 */}
          {tool === 'clazy' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Clazy 检查级别
              </label>
              <select
                value={checks}
                onChange={(e) => setChecks(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="level0">Level 0 - 最稳定，几乎无误报</option>
                <option value="level1">Level 1 - 默认级别，误报很少</option>
                <option value="level2">Level 2 - 包含一些有争议的检查</option>
              </select>
            </div>
          )}

          {tool === 'cppcheck' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Cppcheck 检查类型
              </label>
              <select
                value={enable}
                onChange={(e) => setEnable(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="all">全部检查</option>
                <option value="error">仅错误</option>
                <option value="warning">警告和错误</option>
                <option value="style">风格问题</option>
                <option value="performance">性能问题</option>
                <option value="portability">可移植性问题</option>
              </select>
            </div>
          )}

          {/* 操作按钮 */}
          <div className="flex justify-end gap-2 pt-4">
            {onCancel && (
              <Button type="button" variant="outline" onClick={onCancel}>
                取消
              </Button>
            )}
            <Button type="submit" disabled={isSubmitting || !name.trim()}>
              {isSubmitting ? (isEditMode ? '保存中...' : '创建中...') : (isEditMode ? '保存更改' : '创建测试用例')}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}

