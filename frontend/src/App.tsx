import { Routes, Route } from 'react-router-dom'
import Layout from '@/components/Layout'
import HomePage from '@/pages/HomePage'
import ProjectsPage from '@/pages/ProjectsPage'
import ProjectDetailPage from '@/pages/ProjectDetailPage'
import StaticAnalysisPage from '@/pages/StaticAnalysisPage'
import UITestPage from '@/pages/UITestPage'
import UITestResultPage from '@/pages/UITestResultPage'
import UITestCaseDetailPage from '@/pages/UITestCaseDetailPage'
import UnitTestPage from '@/pages/UnitTestPage'
import IntegrationTestPage from '@/pages/IntegrationTestPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="projects/:id" element={<ProjectDetailPage />} />
        <Route path="projects/:id/static-analysis" element={<StaticAnalysisPage />} />
        <Route path="projects/:id/system-test" element={<UITestPage />} />
        <Route path="projects/:id/system-test/cases/:testCaseId" element={<UITestCaseDetailPage />} />
        <Route path="projects/:id/system-test/results/:executionId" element={<UITestResultPage />} />
        <Route path="projects/:id/unit-test" element={<UnitTestPage />} />
        <Route path="projects/:id/integration-test" element={<IntegrationTestPage />} />
      </Route>
    </Routes>
  )
}

export default App
