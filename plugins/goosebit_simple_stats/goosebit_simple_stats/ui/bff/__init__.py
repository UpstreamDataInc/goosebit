from fastapi import APIRouter, Depends

from goosebit.auth import validate_current_user

from . import stats

router = APIRouter(prefix="/bff", tags=["bff"], dependencies=[Depends(validate_current_user)])
router.include_router(stats.router)
