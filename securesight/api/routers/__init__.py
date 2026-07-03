from fastapi import APIRouter

from securesight.api.routers.auth import router as auth_router
from securesight.api.routers.users import router as users_router
from securesight.api.routers.hosts import router as hosts_router
from securesight.api.routers.metrics import router as metrics_router
from securesight.api.routers.alerts import router as alerts_router
from securesight.api.routers.anomaly import router as anomaly_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(hosts_router, prefix="/hosts", tags=["Hosts"])
api_router.include_router(metrics_router, prefix="/metrics", tags=["Metrics"])
api_router.include_router(alerts_router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(anomaly_router, prefix="/anomalies", tags=["Anomalies"])

__all__ = ["api_router"]
