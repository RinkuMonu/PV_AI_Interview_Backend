from fastapi import APIRouter, Depends

from app.services.dashboard_service import DashboardService
from app.services.analytics_repository import AnalyticsRepository

router = APIRouter()

def get_dashboard_service() -> DashboardService:
    repo = AnalyticsRepository()
    return DashboardService(repository=repo)

@router.get("/overview")
async def get_overview(service: DashboardService = Depends(get_dashboard_service)):
    """
    Returns high-level statistics: total requests, tokens, costs, average latencies, etc.
    """
    return await service.get_overview()

@router.get("/dashboard")
async def get_dashboard(service: DashboardService = Depends(get_dashboard_service)):
    """
    Combined metrics endpoint for UI dashboards.
    """
    overview = await service.get_overview()
    return {
        "overview": overview
    }

# Additional endpoints (e.g. /interviews, /tokens, /cost) would be implemented here 
# delegating to specialized methods in DashboardService.
