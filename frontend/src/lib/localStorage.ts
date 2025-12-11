/**
 * 前端本地存储服务
 * 用于存储项目数据，无需后端支持
 */

export interface LocalProject {
  id: string
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
  source_file?: {
    name: string
    size: number
    type: string
    data: string // base64编码的文件数据
  }
}

const STORAGE_KEY = 'homemade_tester_projects'
const MAX_STORAGE_SIZE = 5 * 1024 * 1024 // 5MB限制

/**
 * 获取所有项目
 */
export function getAllProjects(): LocalProject[] {
  try {
    const data = localStorage.getItem(STORAGE_KEY)
    if (!data) return []
    return JSON.parse(data)
  } catch (error) {
    console.error('读取项目数据失败:', error)
    return []
  }
}

/**
 * 保存所有项目
 */
export function saveAllProjects(projects: LocalProject[]): boolean {
  try {
    const data = JSON.stringify(projects)
    // 检查存储大小
    if (data.length > MAX_STORAGE_SIZE) {
      console.warn('存储数据过大，可能无法保存')
      return false
    }
    localStorage.setItem(STORAGE_KEY, data)
    return true
  } catch (error) {
    console.error('保存项目数据失败:', error)
    // 可能是存储空间不足
    if (error instanceof DOMException && error.name === 'QuotaExceededError') {
      alert('存储空间不足，请清理一些项目或使用浏览器扩展增加存储空间')
    }
    return false
  }
}

/**
 * 获取单个项目
 */
export function getProject(id: string): LocalProject | null {
  const projects = getAllProjects()
  return projects.find(p => p.id === id) || null
}

/**
 * 创建项目
 */
export function createProject(project: Omit<LocalProject, 'id' | 'created_at' | 'updated_at'>): LocalProject {
  try {
    const projects = getAllProjects()
    const newProject: LocalProject = {
      ...project,
      id: generateId(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      is_active: project.is_active ?? true,
    }
    projects.push(newProject)
    
    // 检查存储大小（如果文件太大，可能无法保存）
    const dataSize = JSON.stringify(projects).length
    if (dataSize > MAX_STORAGE_SIZE) {
      console.error('项目数据过大，无法保存。文件大小:', dataSize, '字节，限制:', MAX_STORAGE_SIZE, '字节')
      throw new Error('项目文件过大，无法保存。请减小文件大小或删除一些旧项目。')
    }
    
    const saved = saveAllProjects(projects)
    
    if (!saved) {
      console.error('保存项目失败，可能是存储空间不足')
      throw new Error('保存项目失败，可能是存储空间不足。请清理浏览器缓存或删除一些旧项目。')
    }
    
    // 不进行立即验证，因为 localStorage 写入是同步的
    // 如果 saveAllProjects 返回 true，说明已成功保存
    return newProject
  } catch (error: any) {
    console.error('创建项目时发生错误:', error)
    // 如果是已知错误，直接抛出
    if (error.message && (error.message.includes('过大') || error.message.includes('空间不足'))) {
      throw error
    }
    // 其他错误包装后抛出
    throw new Error(`创建项目失败: ${error.message || '未知错误'}`)
  }
}

/**
 * 更新项目
 */
export function updateProject(id: string, updates: Partial<LocalProject>): LocalProject | null {
  const projects = getAllProjects()
  const index = projects.findIndex(p => p.id === id)
  if (index === -1) return null
  
  projects[index] = {
    ...projects[index],
    ...updates,
    updated_at: new Date().toISOString(),
  }
  saveAllProjects(projects)
  return projects[index]
}

/**
 * 删除项目
 */
export function deleteProject(id: string): boolean {
  const projects = getAllProjects()
  const filtered = projects.filter(p => p.id !== id)
  if (filtered.length === projects.length) return false
  saveAllProjects(filtered)
  return true
}

/**
 * 将文件转换为base64
 */
export function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result as string
      // 移除data URL前缀，只保留base64数据
      const base64 = result.split(',')[1]
      resolve(base64)
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

/**
 * 从base64恢复文件
 */
export function base64ToFile(base64: string, filename: string, mimeType: string): File {
  const byteCharacters = atob(base64)
  const byteNumbers = new Array(byteCharacters.length)
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i)
  }
  const byteArray = new Uint8Array(byteNumbers)
  const blob = new Blob([byteArray], { type: mimeType })
  return new File([blob], filename, { type: mimeType })
}

/**
 * 生成唯一ID
 */
function generateId(): string {
  return `project_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

/**
 * 清空所有项目（用于测试）
 */
export function clearAllProjects(): void {
  localStorage.removeItem(STORAGE_KEY)
}

/**
 * 导出项目数据（用于备份）
 */
export function exportProjects(): string {
  return JSON.stringify(getAllProjects(), null, 2)
}

/**
 * 导入项目数据（用于恢复）
 */
export function importProjects(jsonData: string): boolean {
  try {
    const projects = JSON.parse(jsonData)
    if (!Array.isArray(projects)) {
      throw new Error('无效的项目数据格式')
    }
    saveAllProjects(projects)
    return true
  } catch (error) {
    console.error('导入项目数据失败:', error)
    return false
  }
}

