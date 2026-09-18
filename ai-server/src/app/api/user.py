"""
TODO 用户列表
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/txt")
def get_user():
    return "test"


@router.post("/user")
def set_user_group():
    """创建用户"""
    return False


@router.get("/group_list")
def get_group_list():
    """获取分组列表"""
