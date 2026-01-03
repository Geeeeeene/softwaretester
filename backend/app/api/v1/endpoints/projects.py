"""项目管理API"""
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Request, BackgroundTasks
from sqlalchemy.orm import Session
import shutil
import zipfile
from pathlib import Path
import uuid

from app.db.session import get_db
from app.db.models.project import Project
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse
)
from app.core.config import settings

router = APIRouter()


@router.get("", response_model=ProjectListResponse)
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    project_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """获取项目列表"""
    import logging
    import time
    logger = logging.getLogger(__name__)
    
    try:
        start_time = time.time()
        logger.info(f"[项目列表] 开始查询 - skip={skip}, limit={limit}, project_type={project_type}, is_active={is_active}")
        
        from sqlalchemy.orm import noload
        from sqlalchemy import text
        
        # 检查数据库连接
        try:
            db.execute(text("SELECT 1"))
            logger.debug("[项目列表] 数据库连接正常")
        except Exception as conn_err:
            logger.error(f"[项目列表] ❌ 数据库连接失败: {conn_err}")
            raise HTTPException(status_code=500, detail=f"数据库连接失败: {str(conn_err)}")
        
        # 使用noload避免加载关系，提高查询性能
        logger.info("[项目列表] 构建查询...")
        query = db.query(Project).options(
            noload(Project.test_cases),
            noload(Project.test_executions),
            noload(Project.static_analyses)
        )
        
        if project_type:
            query = query.filter(Project.project_type == project_type)
        if is_active is not None:
            query = query.filter(Project.is_active == is_active)
        
        # 先获取总数（使用子查询优化）
        logger.info("[项目列表] 获取总数...")
        count_start = time.time()
        try:
            total = query.count()
            count_time = time.time() - count_start
            logger.info(f"[项目列表] 总数查询完成: {total} 个项目，耗时: {count_time:.2f}秒")
            if count_time > 5:
                logger.warning(f"[项目列表] ⚠️ 总数查询耗时较长: {count_time:.2f}秒")
        except Exception as count_err:
            count_time = time.time() - count_start
            logger.error(f"[项目列表] ❌ 总数查询失败，耗时: {count_time:.2f}秒，错误: {count_err}")
            raise
        
        # 按创建时间倒序排序，确保新创建的项目在前面
        logger.info("[项目列表] 获取项目列表...")
        items_start = time.time()
        try:
            items = query.order_by(Project.created_at.desc()).offset(skip).limit(limit).all()
            items_time = time.time() - items_start
            logger.info(f"[项目列表] 列表查询完成: {len(items)} 个项目，耗时: {items_time:.2f}秒")
            if items_time > 5:
                logger.warning(f"[项目列表] ⚠️ 列表查询耗时较长: {items_time:.2f}秒")
        except Exception as items_err:
            items_time = time.time() - items_start
            logger.error(f"[项目列表] ❌ 列表查询失败，耗时: {items_time:.2f}秒，错误: {items_err}")
            raise
        
        total_time = time.time() - start_time
        logger.info(f"[项目列表] ✅ 查询成功，总耗时: {total_time:.2f}秒")
        
        if total_time > 10:
            logger.warning(f"[项目列表] ⚠️ 查询总耗时较长: {total_time:.2f}秒，建议检查数据库性能")
        
        return ProjectListResponse(total=total, items=items)
    except Exception as e:
        import traceback
        error_detail = f"查询项目列表失败: {str(e)}\n{traceback.format_exc()}"
        logger.error(f"[项目列表] ❌ {error_detail}")
        raise HTTPException(status_code=500, detail=f"查询项目列表失败: {str(e)}")


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """获取项目详情"""
    from sqlalchemy.orm import noload
    
    # 使用noload避免加载关系，提高查询性能
    project = db.query(Project).options(
        noload(Project.test_cases),
        noload(Project.test_executions),
        noload(Project.static_analyses)
    ).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    request: Request,
    db: Session = Depends(get_db)
):
    """创建项目（支持JSON和FormData两种方式）"""
    try:
        content_type = request.headers.get("content-type", "")
        
        # 检测是JSON还是FormData
        if "application/json" in content_type:
            # JSON方式创建项目
            body = await request.json()
            project_data = ProjectCreate(**body)
            
            base_name = project_data.name
            source_file = None
            extract = "true"
        else:
            # FormData方式创建项目（支持文件上传）
            form = await request.form()
            
            name = form.get("name")
            if not name:
                raise HTTPException(status_code=400, detail="name为必填项")
            
            base_name = name
            project_type = form.get("project_type")
            if not project_type:
                raise HTTPException(status_code=400, detail="project_type为必填项")
            
            # 获取上传的文件
            source_file = form.get("source_file")
            # FastAPI的FormData中，文件字段返回的是UploadFile类型
            # 需要检查是否为UploadFile实例
            from fastapi import UploadFile as FastAPIUploadFile
            if not isinstance(source_file, FastAPIUploadFile):
                source_file = None
            
            extract = form.get("extract", "true")
            if isinstance(extract, str):
                pass
            else:
                extract = "true"
        
        # 检查项目名称是否重复，如果重复则自动添加编号
        import logging
        import time
        logger = logging.getLogger(__name__)
        
        logger.info(f"[创建项目] 开始创建项目，名称: '{base_name}'")
        name_check_start = time.time()
        
        # 优化：先检查一次，如果不存在就直接使用，避免循环查询
        final_name = base_name
        counter = 1
        max_attempts = 100  # 防止无限循环
        
        # 检查是否有重复名称
        existing = db.query(Project).filter(Project.name == final_name).first()
        while existing and counter < max_attempts:
            counter += 1
            final_name = f"{base_name}_{counter}"
            logger.debug(f"[创建项目] 名称 '{base_name}' 重复，尝试 '{final_name}'")
            existing = db.query(Project).filter(Project.name == final_name).first()
        
        if counter >= max_attempts:
            logger.error(f"[创建项目] ❌ 尝试了 {max_attempts} 次仍未找到可用名称")
            raise HTTPException(status_code=400, detail=f"无法生成唯一项目名称，请手动指定")
        
        name_check_time = time.time() - name_check_start
        logger.info(f"[创建项目] 名称检查完成，耗时: {name_check_time:.2f}秒")
        
        # 如果名称被修改，记录日志
        if final_name != base_name:
            logger.info(f"[创建项目] ✅ 项目名称重复，自动重命名: '{base_name}' -> '{final_name}'")
        else:
            logger.info(f"[创建项目] ✅ 项目名称唯一，使用原始名称: '{final_name}'")
        
        # 创建项目对象
        if "application/json" in content_type:
            project = Project(
                name=final_name,
                description=project_data.description,
                project_type=project_data.project_type,
                language=project_data.language,
                framework=project_data.framework,
                source_path=project_data.source_path,
                build_path=project_data.build_path,
                binary_path=project_data.binary_path
            )
        else:
            project = Project(
                name=final_name,
                description=form.get("description") or None,
                project_type=project_type,
                language=form.get("language") or None,
                framework=form.get("framework") or None
            )
        
        logger.info(f"[创建项目] 创建项目对象...")
        db.add(project)
        
        flush_start = time.time()
        db.flush()  # 获取项目ID
        flush_time = time.time() - flush_start
        logger.info(f"[创建项目] flush完成，项目ID: {project.id}，耗时: {flush_time:.2f}秒")
        
        # 如果有上传文件，处理文件上传（仅FormData方式）
        # 检查source_file是否为UploadFile类型
        if source_file and hasattr(source_file, 'file') and hasattr(source_file, 'filename'):
            try:
                # 验证文件大小
                source_file.file.seek(0, 2)
                file_size = source_file.file.tell()
                source_file.file.seek(0)
                
                if file_size > settings.MAX_UPLOAD_SIZE:
                    db.rollback()
                    raise HTTPException(
                        status_code=413,
                        detail=f"文件过大，最大支持 {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
                    )
                
                # 创建项目上传目录
                project_upload_dir = Path(settings.UPLOAD_DIR) / str(project.id)
                project_upload_dir.mkdir(parents=True, exist_ok=True)
                
                file_ext = Path(source_file.filename or '').suffix.lower()
                
                # 如果是ZIP文件且需要解压（extract可能是字符串"true"或布尔值）
                should_extract = extract == "true" or extract is True
                if file_ext == '.zip' and should_extract:
                    # 保存ZIP文件到临时位置
                    temp_zip = project_upload_dir / f"{uuid.uuid4()}.zip"
                    with open(temp_zip, "wb") as buffer:
                        shutil.copyfileobj(source_file.file, buffer)
                    
                    # 解压ZIP文件
                    extract_dir = project_upload_dir / "source"
                    extract_dir.mkdir(parents=True, exist_ok=True)
                    
                    with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                    
                    # 删除临时ZIP文件
                    temp_zip.unlink()
                    
                    # 设置项目source_path（使用绝对路径，确保跨平台兼容）
                    project.source_path = str(extract_dir.resolve())
                    
                    # 创建构建目录
                    build_path = extract_dir / "build"
                    if not build_path.exists():
                        build_path.mkdir(parents=True, exist_ok=True)
                    
                    # 设置build_path
                    project.build_path = str(build_path.resolve())
                else:
                    # 普通文件上传
                    unique_filename = f"{uuid.uuid4()}{file_ext}"
                    file_path = project_upload_dir / unique_filename
                    
                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(source_file.file, buffer)
                    
                    # 使用绝对路径，确保跨平台兼容
                    project.source_path = str(file_path.resolve())
            
            except zipfile.BadZipFile:
                db.rollback()
                raise HTTPException(status_code=400, detail="无效的ZIP文件")
            except Exception as e:
                db.rollback()
                raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")
            finally:
                if source_file:
                    source_file.file.close()
        
        commit_start = time.time()
        db.commit()
        commit_time = time.time() - commit_start
        logger.info(f"[创建项目] commit完成，耗时: {commit_time:.2f}秒")
        
        refresh_start = time.time()
        db.refresh(project)
        refresh_time = time.time() - refresh_start
        logger.info(f"[创建项目] refresh完成，耗时: {refresh_time:.2f}秒")
        
        total_time = time.time() - name_check_start
        logger.info(f"[创建项目] ✅ 项目创建成功，总耗时: {total_time:.2f}秒，项目ID: {project.id}")
        
        return project
    except Exception as e:
        db.rollback()
        import traceback
        error_detail = f"创建项目失败: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ 创建项目错误: {error_detail}")
        raise HTTPException(status_code=500, detail=f"创建项目失败: {str(e)}")


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """更新项目"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    update_data = project_in.model_dump(exclude_unset=True)
    
    # 如果更新了名称，检查是否重复
    if 'name' in update_data and update_data['name'] != project.name:
        import logging
        logger = logging.getLogger(__name__)
        
        base_name = update_data['name']
        final_name = base_name
        counter = 1
        
        # 检查是否有重复名称（排除当前项目）
        while db.query(Project).filter(
            Project.name == final_name,
            Project.id != project_id
        ).first():
            counter += 1
            final_name = f"{base_name}_{counter}"
            logger.debug(f"更新项目名称 '{base_name}' 重复，尝试 '{final_name}'")
        
        # 如果名称被修改，记录日志
        if final_name != base_name:
            logger.info(f"✅ 更新项目名称重复，自动重命名: '{base_name}' -> '{final_name}' (project_id={project_id})")
        
        update_data['name'] = final_name
    
    for field, value in update_data.items():
        setattr(project, field, value)
    
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """删除项目"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 清理相关文件
    if project.source_path:
        try:
            path = Path(project.source_path)
            # 如果是 source 目录，删除整个父目录（项目上传目录）
            if path.name == "source":
                parent_dir = path.parent
                if parent_dir.exists() and "artifacts" in str(parent_dir):
                    shutil.rmtree(parent_dir)
            # 如果路径包含 projects/{uuid}，删除该目录
            elif "projects" in str(path):
                if path.exists():
                    shutil.rmtree(path)
            # 普通文件
            elif path.exists():
                if path.is_file():
                    path.unlink()
                else:
                    shutil.rmtree(path)
        except Exception as e:
            print(f"⚠️ 清理项目文件失败: {str(e)}")

    db.delete(project)
    db.commit()
    return None


@router.post("/{project_id}/test/unit", response_model=dict, status_code=201)
def run_unit_test(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """对项目进行单元测试并生成报告（包含gcov+lcov和Dr.Memory）"""
    from app.db.models.test_execution import TestExecution
    from app.worker.tasks import run_utbot_project_test
    
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if not project.source_path:
        raise HTTPException(
            status_code=400,
            detail="项目未上传源代码，请先上传源代码文件"
        )
    
    # 创建执行记录
    execution = TestExecution(
        project_id=project_id,
        executor_type="unit",
        status="pending",
        total_tests=0
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    
    # 添加后台任务
    background_tasks.add_task(run_utbot_project_test, execution.id)
    
    return {
        "message": "单元测试任务已提交（gcov+lcov + Dr.Memory）",
        "execution_id": execution.id,
        "status": "pending",
        "project_id": project_id
    }


@router.post("/local/test/unit", response_model=dict, status_code=201)
async def run_local_unit_test(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """为本地项目（localStorage）执行单元测试"""
    from app.db.models.test_execution import TestExecution
    from app.worker.tasks_local import run_local_project_test
    import tempfile
    import zipfile
    import base64
    from pathlib import Path
    import json
    
    # 获取请求体
    try:
        project_data = await request.json()
    except:
        raise HTTPException(status_code=400, detail="无效的JSON数据")
    
    # 验证必需字段
    if not project_data.get("id") or not project_data.get("name"):
        raise HTTPException(status_code=400, detail="项目数据不完整")
    
    # 检查是否有源代码文件
    source_file = project_data.get("source_file")
    if not source_file:
        raise HTTPException(
            status_code=400,
            detail="项目未上传源代码，请先上传源代码文件"
        )
    
    # 创建临时目录并解压源代码
    temp_dir = tempfile.mkdtemp(prefix="homemade_tester_")
    source_path = Path(temp_dir) / "source"
    source_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # 解码base64文件数据
        file_data = base64.b64decode(source_file["data"])
        zip_path = source_path / source_file["name"]
        zip_path.write_bytes(file_data)
        
        # 解压ZIP文件
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(source_path)
        
        # 创建执行记录
        execution = TestExecution(
            project_id=0,  # 本地项目没有后端ID
            executor_type="unit",
            status="pending",
            total_tests=0
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        # 添加后台任务
        background_tasks.add_task(
            run_local_project_test,
            execution.id,
            str(source_path),
            str(Path(temp_dir) / "build")
        )
        
        return {
            "message": "单元测试任务已提交（gcov+lcov + Dr.Memory）",
            "execution_id": execution.id,
            "status": "pending",
            "temp_path": temp_dir
        }
        
    except Exception as e:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"处理源代码失败: {str(e)}")
