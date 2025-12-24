import axios from 'axios'

// 优先使用环境变量，如果没有则使用相对路径（通过 Vite 代理）
// 注意：baseURL 应该包含 /api/v1，因为所有 API 路径都以 /api/v1 开头
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 如果是FormData，移除Content-Type让浏览器自动设置（包含boundary）
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }
    
    // 可以在这里添加认证token
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 统一错误处理
    if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
      console.error('网络错误：无法连接到后端服务器，请确保后端正在运行')
      console.error('后端地址:', API_BASE_URL)
    } else if (error.response?.status === 401) {
      // 处理未授权
      console.error('未授权，请登录')
    } else if (error.response?.status === 404) {
      // 404 错误通常是正常的（如测试文件不存在），只在非测试文件相关的请求时记录
      const url = error.config?.url || ''
      if (!url.includes('/test-file')) {
        console.error('资源不存在:', url)
      }
      // 对于测试文件不存在的 404，静默处理，不输出错误
    } else if (error.response?.status >= 500) {
      console.error('服务器错误')
    }
    return Promise.reject(error)
  }
)

// ============ 项目API ============

export interface Project {
  id: number
  name: string
  description?: string
  project_type: string
  language?: string
  framework?: string
  source_path?: string
  build_path?: string
  binary_path?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ProjectCreate {
  name: string
  description?: string
  project_type: string
  language?: string
  framework?: string
  source_path?: string
  build_path?: string
  binary_path?: string
}

export const projectsApi = {
  list: (params?: { skip?: number; limit?: number; project_type?: string }) =>
    api.get<{ total: number; items: Project[] }>('/projects', { params }),
  
  get: (id: number) =>
    api.get<Project>(`/projects/${id}`),
  
  create: (data: ProjectCreate) =>
    api.post<Project>('/projects', data),
  
  // 创建项目（支持文件上传）
  createWithFile: (formData: FormData) =>
    api.post<Project>('/projects', formData, {
      // 不要手动设置Content-Type，让axios自动处理FormData的boundary
    }),
  
  update: (id: number, data: Partial<ProjectCreate>) =>
    api.put<Project>(`/api/v1/projects/${id}`, data),
  
  delete: (id: number) =>
    api.delete(`/projects/${id}`),
}

// ============ 测试用例API ============

export interface TestCase {
  id: number
  project_id: number
  name: string
  description?: string
  test_type: string
  test_ir: Record<string, any>
  priority: string
  tags: string[]
  created_at: string
  updated_at: string
}

export interface TestCaseCreate {
  project_id: number
  name: string
  description?: string
  test_type: string
  test_ir: Record<string, any>
  priority?: string
  tags?: string[]
}

export const testCasesApi = {
  list: (params?: { 
    project_id?: number
    test_type?: string
    priority?: string
    skip?: number
    limit?: number
  }) =>
    api.get<{ total: number; items: TestCase[] }>('/test-cases', { params }),
  
  get: (id: number) =>
    api.get<TestCase>(`/test-cases/${id}`),
  
  create: (data: TestCaseCreate) =>
    api.post<TestCase>('/test-cases', data),
  
  update: (id: number, data: Partial<TestCaseCreate>) =>
    api.put<TestCase>(`/test-cases/${id}`, data),
  
  delete: (id: number) =>
    api.delete(`/test-cases/${id}`),
}

// ============ 测试执行API ============

export interface TestResult {
  id: number
  test_case_id?: number
  status: string
  duration_seconds?: number
  error_message?: string
  log_path?: string
  extra_data?: {
    issues?: Array<{
      file: string
      line?: number
      column?: number
      severity: string
      message: string
      id?: string
      tool: string
    }>
    [key: string]: any
  }
}

export interface TestExecution {
  id: number
  project_id: number
  executor_type: string
  status: string
  total_tests: number
  passed_tests: number
  failed_tests: number
  skipped_tests: number
  duration_seconds?: number
  error_message?: string
  created_at: string
  started_at?: string
  completed_at?: string
  // 新增字段
  coverage_data?: {
    percentage?: number
    lines_covered?: number
    lines_total?: number
    branches_covered?: number
    branches_total?: number
    functions_covered?: number
    functions_total?: number
  }
  result?: {
    issues?: Array<{
      id: string
      type: string
      severity: string
      message: string
      stack_trace?: Array<{
        frame: number
        function: string
        file: string
        line?: number
      }>
    }>
    total_issues?: number
    error_count?: number
    warning_count?: number
  }
  logs?: string
  artifacts?: Array<{
    type: string
    path: string
  }>
  test_results?: TestResult[]
}

export interface ExecutionCreate {
  project_id: number
  executor_type: string
  test_case_ids: number[]
}

export const executionsApi = {
  list: (params?: { 
    project_id?: number
    status?: string
    skip?: number
    limit?: number
  }) =>
    api.get<TestExecution[]>('/executions', { params }),
  
  get: (id: number) =>
    api.get<TestExecution>(`/executions/${id}`),
  
  create: (data: ExecutionCreate) =>
    api.post<TestExecution>('/executions', data),
  
  // 执行单元测试（UTBot + gcov + lcov + Dr.Memory）
  runUnitTest: (projectId: number) =>
    api.post<{
      message: string
      execution_id: number
      status: string
      project_id: number
    }>(`/projects/${projectId}/test/utbot`),
  
  // 执行本地项目的单元测试（支持localStorage项目）
  runLocalUnitTest: (projectData: {
    id: string
    name: string
    source_file?: {
      name: string
      size: number
      type: string
      data: string
    }
  }) =>
    api.post<{
      message: string
      execution_id: number
      status: string
      temp_path?: string
    }>('/projects/local/test/utbot', projectData),
}

// ============ 工具状态API ============

export interface ToolStatus {
  available: boolean
  path?: string
  message: string
  install_hint?: string
  version?: string
}

export interface ToolsStatusResponse {
  utbot: ToolStatus
  gcov: ToolStatus
  lcov: ToolStatus
  drmemory: ToolStatus
  genhtml?: ToolStatus
}

export const toolsApi = {
  getStatus: () =>
    api.get<ToolsStatusResponse>('/tools/status'),
  
  getToolStatus: (toolName: string) =>
    api.get<ToolStatus>(`/tools/status/${toolName}`),
}

// ============ 静态分析API ============

export interface StaticAnalysisStatus {
  has_analysis: boolean
  latest?: {
    timestamp: number
    created_at: string
    metadata: Record<string, any>
    summary: {
      total_files: number
      total_issues: number
      severity_count: {
        HIGH: number
        MEDIUM: number
        LOW: number
      }
    }
  }
  total_count: number
}

export interface StaticAnalysisResult {
  project_id: number
  timestamp: number
  created_at: string
  metadata: Record<string, any>
  results: {
    project_path: string
    language?: string
    files_analyzed: number
    total_issues: number
    file_results: Record<string, any>
    summary: {
      total_files: number
      total_issues: number
      severity_count: {
        HIGH: number
        MEDIUM: number
        LOW: number
      }
    }
  }
}

export interface FileTreeNode {
  name: string
  path: string
  type: 'file' | 'directory'
  children?: FileTreeNode[]
  size?: number
}

export interface FileContent {
  path: string
  content: string
  encoding: string
  detected_encoding?: string
  confidence?: number
  size: number
  lines: string[]
}

export const staticAnalysisApi = {
  // 启动静态分析
  run: (projectId: number, useLlm: boolean = true, language?: string) =>
    api.post<{
      message: string
      project_id: number
      status: string
    }>(`/projects/${projectId}/static-analysis/run`, {
      use_llm: useLlm,
      language,
    }),
  
  // 获取分析状态
  getStatus: (projectId: number) =>
    api.get<StaticAnalysisStatus>(`/projects/${projectId}/static-analysis/status`),
  
  // 获取分析结果
  getResults: (projectId: number, timestamp?: number) =>
    api.get<StaticAnalysisResult>(`/projects/${projectId}/static-analysis/results`, {
      params: timestamp ? { timestamp } : undefined,
    }),
  
  // 获取项目文件树
  getFiles: (projectId: number) =>
    api.get<{ project_id: number; file_tree: FileTreeNode[] }>(`/projects/${projectId}/static-analysis/files`),
  
  // 获取文件内容
  getFileContent: (projectId: number, filePath: string) =>
    api.get<FileContent>(`/projects/${projectId}/static-analysis/file-content`, {
      params: { file_path: filePath },
    }),
}

// ============ 单元测试API ============

export const unitTestsApi = {
  // 获取项目文件列表
  getFiles: (projectId: number) =>
    api.get<{ project_id: number; files: any[] }>(`/unit-tests/${projectId}/files`),
  
  // 生成测试代码
  generate: (projectId: number, filePath: string, additionalInfo?: string) =>
    api.post<{ project_id: number; file_path: string; test_code: string; test_file_path?: string }>(
      `/unit-tests/${projectId}/generate`,
      { file_path: filePath, additional_info: additionalInfo }
    ),
  
  // 获取测试文件内容
  getTestFile: (projectId: number, filePath: string) =>
    api.get<{ project_id: number; file_path: string; test_file_path: string; test_code: string }>(
      `/unit-tests/${projectId}/test-file`,
      { params: { file_path: filePath } }
    ),
  
  // 更新测试文件内容
  updateTestFile: (projectId: number, filePath: string, testCode: string) =>
    api.put<{ project_id: number; file_path: string; test_file_path: string; message: string }>(
      `/unit-tests/${projectId}/test-file`,
      { file_path: filePath, test_code: testCode }
    ),
  
  // 执行测试（testCode可选，如果不提供则从文件读取）
  execute: (projectId: number, filePath: string, testCode?: string) => {
    const body: any = { file_path: filePath }
    // 只有当 testCode 有值时才添加到请求体中
    if (testCode !== undefined && testCode !== null && testCode !== '') {
      body.test_code = testCode
    }
    console.log('执行测试请求:', { projectId, filePath, hasTestCode: testCode !== undefined, body })
    return api.post<{ success: boolean; logs: string; summary: any; raw_output: string }>(
      `/unit-tests/${projectId}/execute`,
      body
    )
  },
  
  // 上传设计文档
  uploadDocument: (projectId: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<{ project_id: number; filename: string; summary: string; message: string }>(
      `/unit-tests/${projectId}/upload-document`,
      formData
    )
  },
  
  // 获取文档要点
  getDocumentSummary: (projectId: number) =>
    api.get<{ project_id: number; summary: string | null; has_summary: boolean; message?: string }>(
      `/unit-tests/${projectId}/document-summary`
    ),
  
  // 更新文档要点
  updateDocumentSummary: (projectId: number, summary: string) =>
    api.put<{ project_id: number; summary: string; has_summary: boolean; message: string }>(
      `/unit-tests/${projectId}/document-summary`,
      { summary }
    ),
}

// ============ 上传API ============

export const uploadApi = {
  // 上传项目源代码
  uploadProjectSource: (projectId: number, file: File, extract: boolean = true) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('extract', extract.toString())
    return api.post<{
      message: string
      filename: string
      path?: string
      extracted_path?: string
      size: number
      extracted: boolean
    }>(`/upload/project/${projectId}/source`, formData)
  },
  
  uploadStaticZip: (file: File, name?: string, description?: string, tool?: string) => {
    const form = new FormData()
    form.append('file', file)
    if (name) form.append('name', name)
    if (description) form.append('description', description)
    if (tool) form.append('tool', tool)
    return api.post('/upload/static-zip', form)
  },
}
