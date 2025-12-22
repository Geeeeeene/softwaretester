import { useState, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Upload, FileCode, Loader2, CheckCircle2, X } from 'lucide-react'
import { uploadApi, projectsApi } from '@/lib/api'
import { useQueryClient } from '@tanstack/react-query'

interface SourceBuildTabProps {
  projectId: number
  project: {
    source_path?: string
    build_path?: string
    binary_path?: string
    project_type?: string
  }
}

export function SourceBuildTab({ projectId, project }: SourceBuildTabProps) {
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const queryClient = useQueryClient()

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setUploadFile(file)
    }
  }

  const handleUpload = async () => {
    if (!uploadFile) {
      alert('请选择文件')
      return
    }

    try {
      setIsUploading(true)
      setUploadProgress(0)

      // 检查文件大小
      const maxSize = 100 * 1024 * 1024 // 100MB
      if (uploadFile.size > maxSize) {
        alert(`文件过大，最大支持 ${maxSize / 1024 / 1024}MB`)
        setIsUploading(false)
        return
      }

      // 上传文件
      await uploadApi.uploadProjectSource(projectId, uploadFile, true)

      setUploadProgress(100)
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
      
      alert('文件上传成功！')
      setUploadFile(null)
      setIsUploading(false)
      setUploadProgress(0)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (error: any) {
      console.error('文件上传失败:', error)
      alert(`文件上传失败: ${error.response?.data?.detail || error.message || '未知错误'}`)
      setIsUploading(false)
      setUploadProgress(0)
    }
  }

  return (
    <div className="space-y-6">
      {/* 上传源代码区 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            上传源代码
          </CardTitle>
          <CardDescription>
            上传项目源代码文件（支持ZIP格式，会自动解压）
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <label className="flex-1 cursor-pointer">
              <input
                ref={fileInputRef}
                type="file"
                accept=".zip,.tar,.tar.gz,.cpp,.c,.h,.hpp"
                onChange={handleFileChange}
                className="hidden"
                disabled={isUploading}
              />
              <div className={`flex items-center justify-center px-4 py-2 border-2 border-dashed rounded-md transition-colors ${
                isUploading 
                  ? 'border-gray-200 bg-gray-50 cursor-not-allowed' 
                  : 'border-gray-300 hover:border-blue-500 cursor-pointer'
              }`}>
                {isUploading ? (
                  <Loader2 className="h-5 w-5 mr-2 text-blue-500 animate-spin" />
                ) : (
                  <Upload className="h-5 w-5 mr-2 text-gray-400" />
                )}
                <span className="text-sm text-gray-600">
                  {isUploading 
                    ? '上传中...' 
                    : uploadFile 
                    ? uploadFile.name 
                    : '点击选择文件（支持ZIP、TAR或C++源文件）'}
                </span>
              </div>
            </label>
            {uploadFile && !isUploading && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setUploadFile(null)
                  if (fileInputRef.current) {
                    fileInputRef.current.value = ''
                  }
                }}
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>

          {isUploading && uploadProgress > 0 && (
            <div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs text-gray-600">上传进度</span>
                <span className="text-xs text-gray-600">{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          <Button
            onClick={handleUpload}
            disabled={!uploadFile || isUploading}
            className="w-full"
          >
            {isUploading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                上传中...
              </>
            ) : (
              '上传'
            )}
          </Button>
        </CardContent>
      </Card>

      {/* 文件路径展示 */}
      {(project.source_path || project.build_path || project.binary_path) && (
        <Card>
          <CardHeader>
            <CardTitle>文件路径</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {project.source_path && (
              <div>
                <p className="text-sm text-gray-500">
                  {project.project_type === 'ui' ? '应用程序路径' : '源代码路径'}
                </p>
                <p className="text-base font-mono bg-gray-50 p-2 rounded">
                  {project.source_path}
                </p>
                {project.project_type === 'ui' && (
                  <p className="text-xs text-gray-400 mt-1">指向待测试应用程序的可执行文件（.exe）</p>
                )}
              </div>
            )}
            {project.build_path && (
              <div>
                <p className="text-sm text-gray-500">构建路径</p>
                <p className="text-base font-mono bg-gray-50 p-2 rounded">
                  {project.build_path}
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

      {/* 构建状态区 */}
      <Card>
        <CardHeader>
          <CardTitle>构建状态</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500">
            构建功能开发中...
          </div>
        </CardContent>
      </Card>
    </div>
  )
}



