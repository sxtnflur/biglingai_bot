from .chatting import router as chatting_router
from .start import router as start_router
from .mistakes import router as mistakes_router
from .sub import router as sub_router
from .ref import router as ref_router
from .utils import router as utils_router

__routers__ = (
    start_router, chatting_router, mistakes_router,
    sub_router, ref_router, utils_router
)