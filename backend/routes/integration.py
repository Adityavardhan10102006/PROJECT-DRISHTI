"""
backend/routes/integration.py — Project DRISHTI
===============================================
REST API for Data Source Integration Architecture, Adapter Telemetry,
and Regulatory Provenance Transparency.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends
import os

from backend.auth.security import get_current_user
from backend.integration.adapters import get_integration_registry, IntegrationRegistry


router = APIRouter(prefix="/integration", tags=["Integration Architecture & Sources"])


@router.get(
    "/sources",
    response_model=List[Dict[str, Any]],
    summary="List data source adapters with honest connection states",
)
async def list_data_sources(
    current_user: dict = Depends(get_current_user),
    registry: IntegrationRegistry = Depends(get_integration_registry),
):
    """
    Returns registered data source adapters.
    Explicitly distinguishes Prototype Demonstrative data from future Institutional Feeds.
    Never claims fake live feeds to NCRP or core banking.
    """
    return registry.list_all_sources()


@router.get(
    "/provenance",
    response_model=Dict[str, Any],
    summary="Get regulatory dataset provenance and ethical boundaries",
)
async def get_dataset_provenance(
    current_user: dict = Depends(get_current_user),
):
    """Returns provenance documentation describing data generation methods and seed reproducibility."""
    prov_path = "data/provenance.md"
    content = ""
    if os.path.exists(prov_path):
        with open(prov_path, "r", encoding="utf-8") as f:
            content = f.read()

    return {
        "status": "success",
        "documentation": content,
        "framework": "RBI Master Directions on Cyber Security & DPDP Act 2023 Compliant",
        "random_seed": 42,
        "is_production_live": False,
        "badge": "Synthetic Demonstration & Curated Geospatial Prototype",
    }
