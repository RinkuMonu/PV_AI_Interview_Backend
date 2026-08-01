from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.services.provider_registry import provider_registry
from app.services.model_registry import model_registry
from app.services.health_monitor import health_monitor
from app.services.ai_router import AIRouter
from app.schemas.routing import RoutingRequest

router = APIRouter()
ai_router_instance = AIRouter()

@router.get("/providers")
async def get_providers():
    providers = provider_registry.list_providers()
    return {"providers": providers}

@router.get("/models")
async def get_models():
    models = model_registry.list_models()
    return {"models": [m.model_dump() for m in models]}

@router.get("/health")
async def get_health():
    health_data = {}
    for p in provider_registry.list_providers():
        health_data[p] = health_monitor.get_status(p).model_dump()
    return health_data

@router.get("/routes")
async def get_routes():
    # Admin endpoint to see active routing policies (strategies available)
    return {"policies": ["lowest_cost", "lowest_latency", "balanced", "highest_quality"]}

@router.post("/simulate")
async def simulate_route(request: RoutingRequest):
    # Simulates what the router WOULD do without executing
    all_models = model_registry.list_models()
    valid_models = ai_router_instance.capability_matcher.match(request, all_models)
    ranked = ai_router_instance.routing_engine.sort_models(request, valid_models, policy="balanced")
    
    return {
        "ranked_route_plan": [m.model_name for m in ranked],
        "primary_provider": ranked[0].provider if ranked else None,
        "fallbacks": [m.provider for m in ranked[1:]] if len(ranked) > 1 else []
    }
