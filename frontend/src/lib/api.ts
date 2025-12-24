import axios from 'axios'

// 优先使用环境变量，如果没有则使用相对路径（通过 Vite 代理）
// 注意：baseURL 应该包含 /api/v1，因为所有 API 路径都以 /api/v1 开头
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 300000, // 5分钟超时（AI生成需要较长时间）
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
  (response) => {
    // 记录成功的请求
    console.log(`[API] ✅ ${response.config.method?.toUpperCase()} ${response.config.url} - ${response.status}`)
    return response
  },
  (error) => {
    // 统一错误处理
    const url = error.config?.url || 'unknown'
    const method = error.config?.method?.toUpperCase() || 'UNKNOWN'
    
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      console.error(`[API] ⏱️ 请求超时: ${method} ${url}`)
      console.error('请求超时：后端响应时间过长，请检查后端服务状态')
    } else if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
      console.error(`[API] 🌐 网络错误: ${method} ${url}`)
      console.error('网络错误：无法连接到后端服务器，请确保后端正在运行')
      console.error('后端地址:', API_BASE_URL)
    } else if (error.response?.status === 401) {
      console.error(`[API] 🔒 未授权: ${method} ${url}`)
      // 处理未授权
      console.error('未授权，请登录')
    } else if (error.response?.status === 404) {
      // 404 错误通常是正常的（如测试文件不存在），只在非测试文件相关的请求时记录
      const requestUrl = error.config?.url || url
      if (!requestUrl.includes('/test-file')) {
        console.error(`[API] ❌ 资源不存在: ${method} ${requestUrl}`)
        console.error('资源不存在')
      }
      // 对于测试文件不存在的 404，静默处理，不输出错误
    } else if (error.response?.status >= 500) {
      console.error(`[API] 💥 服务器错误: ${method} ${url} - ${error.response.status}`)
      console.error('服务器错误:', error.response?.data)
    } else {
      console.error(`[API] ❌ 请求失败: ${method} ${url}`, error)
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
  // 获取项目文件列表（文件树结构）
  getFiles: (projectId: number) =>
    api.get<{ project_id: number; file_tree: FileTreeNode[] }>(`/unit-tests/${projectId}/files`),
  
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

// ============ 集成测试API ============

export interface IntegrationTestIR {
  type: 'integration'
  name: string
  description?: string
  flow: Array<{
    name: string
    url: string
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
    headers?: Record<string, string>
    body?: Record<string, any>
  }>
  validations: Array<{
    type: 'equals' | 'not_equals' | 'contains' | 'throws' | 'custom'
    expected: any
    actual?: string
    message?: string
  }>
  required_services?: string[]
  tags?: string[]
  priority?: 'low' | 'medium' | 'high' | 'critical'
}

export const integrationTestsApi = {
  // 获取源文件列表（文件树结构）
  getFiles: (projectId: number) =>
    api.get<{ project_id: number; file_tree: FileTreeNode[] }>(
      `/integration-tests/${projectId}/files`
    ),
  
  // 生成集成测试用例（AI分析代码，与单元测试API结构一致）
  generate: (projectId: number, filePath: string, additionalInfo?: string) =>
    api.post<{ project_id: number; file_path: string; test_code: string }>(
      `/integration-tests/${projectId}/generate`,
      { file_path: filePath, additional_info: additionalInfo }
    ),
  
  // 执行集成测试（与单元测试API结构一致）
  execute: (projectId: number, filePath: string, testCode: string) =>
    api.post<{ success: boolean; logs: string; summary: any; raw_output: string }>(
      `/integration-tests/${projectId}/execute`,
      { file_path: filePath, test_code: testCode }
    ),
  
  // 分析整个项目并生成测试用例
  generateProject: (projectId: number, additionalInfo?: string) =>
    api.post<{
      project_id: number;
      file_path: string | null;
      test_code: string;
      project_files_count: number;
    }>(
      `/integration-tests/${projectId}/generate-project`,
      { additional_info: additionalInfo }
    ),
  
  // 使用AI执行测试用例
  executeWithAI: (projectId: number, testCode: string) =>
    api.post<{
      success: boolean;
      logs: string;
      summary: any;
      ai_analysis?: string;
    }>(
      `/integration-tests/${projectId}/execute-ai`,
      { file_path: "", test_code: testCode }
    ),
  
  // 生成并执行集成测试（一步完成，保留兼容性）
  generateAndExecute: (projectId: number, filePath?: string, additionalInfo?: string) =>
    api.post<{
      project_id: number;
      file_path: string | null;
      test_code: string;
      execution_result: any;
      success: boolean;
      logs: string;
      summary: any;
      ai_analysis?: string;
      project_files_count?: number;
    }>(
      `/integration-tests/${projectId}/generate-and-execute`,
      { file_path: filePath, additional_info: additionalInfo }
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

// ============ UI测试API ============

export interface UITestCaseGenerateRequest {
  name: string
  description: string
}

export interface UITestCaseGenerateResponse {
  name: string
  description: string
  robot_script: string
  test_ir: Record<string, any>
}

export interface UITestExecuteRequest {
  name: string
  description: string
  robot_script: string
}

export interface UITestExecuteResponse {
  execution_id: number
  status: string
  message: string
}

export interface UITestResult {
  execution_id: number
  status: string
  passed: boolean
  logs?: string
  error_message?: string
  artifacts: Array<{
    type: string
    path: string
    name?: string
  }>
  duration_seconds?: number
  created_at: string
  completed_at?: string
}

export interface UITestExecutionListResponse {
  total: number
  items: TestExecution[]
  statistics: {
    total_executions: number
    completed_executions: number
    passed_executions: number
    pass_rate: number
  }
}

export const uiTestApi = {
  // 使用AI生成UI测试用例（设置更长的超时时间，因为AI生成需要较长时间）
  generateTestCase: (projectId: number, request: UITestCaseGenerateRequest) =>
    api.post<UITestCaseGenerateResponse>(`/projects/${projectId}/ui-test/generate`, request, {
      timeout: 300000, // 5分钟超时（AI生成可能需要较长时间）
    }),
  
  // 执行UI测试
  executeTest: (projectId: number, request: UITestExecuteRequest) =>
    api.post<UITestExecuteResponse>(`/projects/${projectId}/ui-test/execute`, request),
  
  // 获取UI测试结果
  getTestResult: (projectId: number, executionId: number) =>
    api.get<UITestResult>(`/projects/${projectId}/ui-test/results/${executionId}`),
  
  // 获取UI测试执行历史
  listExecutions: (projectId: number, skip: number = 0, limit: number = 20) =>
    api.get<UITestExecutionListResponse>(`/projects/${projectId}/ui-test/executions`, {
      params: { skip, limit }
    }),
  
  // 删除UI测试执行记录
  deleteExecution: (projectId: number, executionId: number) =>
    api.delete(`/projects/${projectId}/ui-test/executions/${executionId}`),
  
  // 获取UI测试报告文件内容
  getReport: (projectId: number, executionId: number, reportType: 'log' | 'report' | 'output' = 'log') =>
    api.get<{ content: string; type: string; path: string }>(`/projects/${projectId}/ui-test/report/${executionId}`, {
      params: { report_type: reportType }
    }),
}
