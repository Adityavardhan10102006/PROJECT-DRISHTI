"""
backend/integration/adapters.py — Project DRISHTI
=================================================
Data Source Integration Layer & Institutional Adapter Architecture.

Enforces strict separation between:
  1. Synthetic / Curated Demonstration Data (Active in Prototype)
  2. Integration-Ready Institutional Stubs (Awaiting Authorized Government / Bank Access)

NEVER claims fake live connectivity to NCRP, NPCI, I4C, or Core Banking Systems.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List, Optional
import os
import json
import pandas as pd


class SourceStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    ACTIVE_PROTOTYPE = "ACTIVE_PROTOTYPE"
    INTEGRATION_READY = "INTEGRATION_READY"
    AWAITING_AUTH = "AWAITING_AUTHORIZED_FEED"
    NOT_CONNECTED = "NOT_CONNECTED"


class DataSourceType(str, Enum):
    SYNTHETIC_DEMO = "Synthetic Demonstration Dataset"
    CURATED_GEOSPATIAL = "Curated Geospatial Dataset"
    INSTITUTIONAL_FEED = "Authorized Institutional Feed"
    LOCAL_REGISTRY = "Local Relational Registry"


# ─────────────────────────────────────────────────────────
# ABSTRACT INTERFACES
# ─────────────────────────────────────────────────────────

class ComplaintSource(ABC):
    """Abstract interface for cybercrime complaint ingestion."""

    @abstractmethod
    def get_source_metadata(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def fetch_complaint(self, complaint_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def search_complaints(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        pass


class TransactionSource(ABC):
    """Abstract interface for financial transaction ledger ingestion."""

    @abstractmethod
    def get_source_metadata(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def fetch_transaction(self, tx_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_account_ledger(self, account_id: str) -> List[Dict[str, Any]]:
        pass


class ATMSource(ABC):
    """Abstract interface for ATM terminal network directory and withdrawal logs."""

    @abstractmethod
    def get_source_metadata(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_all_atms(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_atm_by_id(self, atm_id: str) -> Optional[Dict[str, Any]]:
        pass


class PoliceUnitSource(ABC):
    """Abstract interface for intercepting police unit locations and readiness."""

    @abstractmethod
    def get_source_metadata(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_available_units(self) -> List[Dict[str, Any]]:
        pass


# ─────────────────────────────────────────────────────────
# CONCRETE PROTOTYPE IMPLEMENTATIONS
# ─────────────────────────────────────────────────────────

class SyntheticComplaintSource(ComplaintSource):
    """Active prototype implementation reading from validated synthetic complaints."""

    def __init__(self, file_path: str = "data/complaints.csv"):
        self.file_path = file_path
        self._cache: Optional[pd.DataFrame] = None

    def _load_data(self) -> pd.DataFrame:
        if self._cache is None and os.path.exists(self.file_path):
            self._cache = pd.read_csv(self.file_path)
        return self._cache if self._cache is not None else pd.DataFrame()

    def get_source_metadata(self) -> Dict[str, Any]:
        df = self._load_data()
        return {
            "source_id": "SRC-COMPLAINTS-SYNTHETIC",
            "name": "Synthetic Cybercrime Complaints Corpus",
            "category": "Complaints Intake",
            "dataset_type": DataSourceType.SYNTHETIC_DEMO.value,
            "status": SourceStatus.AVAILABLE.value,
            "is_live": False,
            "records_count": len(df),
            "description": "5,200 synthetic cybercrime complaint narratives generated across 10 metro zones with Hinglish text.",
            "auth_required": False,
            "disclaimer": "Synthetic demonstration dataset. No personal citizen data is stored or processed.",
        }

    def fetch_complaint(self, complaint_id: str) -> Optional[Dict[str, Any]]:
        df = self._load_data()
        if df.empty or "complaint_id" not in df.columns:
            return None
        match = df[df["complaint_id"].astype(str) == str(complaint_id)]
        if not match.empty:
            return match.iloc[0].to_dict()
        return None

    def search_complaints(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        df = self._load_data()
        if df.empty:
            return []
        q = str(query).lower()
        mask = (
            df["complaint_id"].astype(str).str.lower().str.contains(q, na=False) |
            df["complaint_text"].astype(str).str.lower().str.contains(q, na=False) |
            df["fraud_type"].astype(str).str.lower().str.contains(q, na=False)
        )
        return df[mask].head(limit).to_dict(orient="records")


class SyntheticTransactionSource(TransactionSource):
    """Active prototype implementation reading from synthetic banking transaction chains."""

    def __init__(self, file_path: str = "data/transactions.csv"):
        self.file_path = file_path
        self._cache: Optional[pd.DataFrame] = None

    def _load_data(self) -> pd.DataFrame:
        if self._cache is None and os.path.exists(self.file_path):
            self._cache = pd.read_csv(self.file_path)
        return self._cache if self._cache is not None else pd.DataFrame()

    def get_source_metadata(self) -> Dict[str, Any]:
        df = self._load_data()
        return {
            "source_id": "SRC-TRANSACTIONS-SYNTHETIC",
            "name": "Synthetic Relational Transaction Ledger",
            "category": "Banking Ledger",
            "dataset_type": DataSourceType.SYNTHETIC_DEMO.value,
            "status": SourceStatus.AVAILABLE.value,
            "is_live": False,
            "records_count": len(df),
            "description": "22,100 synthetic transaction records with realistic velocity delays, layering, and mule reuse.",
            "auth_required": False,
            "disclaimer": "Synthetic modeled dataset generated under statistical controls. No live core banking systems connected.",
        }

    def fetch_transaction(self, tx_id: str) -> Optional[Dict[str, Any]]:
        df = self._load_data()
        if df.empty or "transaction_id" not in df.columns:
            return None
        match = df[df["transaction_id"].astype(str) == str(tx_id)]
        if not match.empty:
            return match.iloc[0].to_dict()
        return None

    def get_account_ledger(self, account_id: str) -> List[Dict[str, Any]]:
        df = self._load_data()
        if df.empty:
            return []
        acc_str = str(account_id)
        mask = (df["sender_account"].astype(str) == acc_str) | (df["receiver_account"].astype(str) == acc_str)
        return df[mask].to_dict(orient="records")


class CuratedATMSource(ATMSource):
    """Active prototype implementation reading curated Hyderabad ATM terminals."""

    def __init__(self, file_path: str = "data/hyderabad_atms.csv"):
        self.file_path = file_path
        self._cache: Optional[pd.DataFrame] = None

    def _load_data(self) -> pd.DataFrame:
        if self._cache is None and os.path.exists(self.file_path):
            self._cache = pd.read_csv(self.file_path)
        return self._cache if self._cache is not None else pd.DataFrame()

    def get_source_metadata(self) -> Dict[str, Any]:
        df = self._load_data()
        return {
            "source_id": "SRC-ATMS-CURATED",
            "name": "Curated Hyderabad ATM Network Directory",
            "category": "Geospatial Terminals",
            "dataset_type": DataSourceType.CURATED_GEOSPATIAL.value,
            "status": SourceStatus.AVAILABLE.value,
            "is_live": False,
            "records_count": len(df),
            "description": "520 validated ATM terminals with coordinates, bank identifiers, and 24x7 operating statuses across Hyderabad.",
            "auth_required": False,
            "disclaimer": "Curated geospatial dataset. ATM terminal feeds represent static catalog data for demonstration.",
        }

    def get_all_atms(self) -> List[Dict[str, Any]]:
        df = self._load_data()
        return df.to_dict(orient="records") if not df.empty else []

    def get_atm_by_id(self, atm_id: str) -> Optional[Dict[str, Any]]:
        df = self._load_data()
        if df.empty or "atm_id" not in df.columns:
            return None
        match = df[df["atm_id"].astype(str) == str(atm_id)]
        if not match.empty:
            return match.iloc[0].to_dict()
        return None


class StaticPoliceUnitSource(PoliceUnitSource):
    """Active prototype implementation for police intervention units."""

    def __init__(self, file_path: str = "data/police_units.json"):
        self.file_path = file_path
        self._units: Optional[List[Dict[str, Any]]] = None

    def _load_data(self) -> List[Dict[str, Any]]:
        if self._units is None and os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self._units = json.load(f)
            except Exception:
                self._units = []
        return self._units or []

    def get_source_metadata(self) -> Dict[str, Any]:
        units = self._load_data()
        return {
            "source_id": "SRC-POLICE-STATIC",
            "name": "Curated Response Units & Station Roster",
            "category": "Tactical Operations",
            "dataset_type": DataSourceType.CURATED_GEOSPATIAL.value,
            "status": SourceStatus.AVAILABLE.value,
            "is_live": False,
            "records_count": len(units),
            "description": "55 mapped Cyber Crime Police Stations and PCR patrol vehicles across Cyberabad, Hyderabad, and Rachakonda.",
            "auth_required": False,
            "disclaimer": "Curated demonstration stations. No live telemetry tracking of active patrol officers.",
        }

    def get_available_units(self) -> List[Dict[str, Any]]:
        return self._load_data()


# ─────────────────────────────────────────────────────────
# FUTURE INSTITUTIONAL ADAPTERS (INTEGRATION READY)
# ─────────────────────────────────────────────────────────

class NCRPComplaintAdapter(ComplaintSource):
    """Institutional adapter interface for National Cyber Crime Reporting Portal (NCRP / I4C)."""

    def get_source_metadata(self) -> Dict[str, Any]:
        return {
            "source_id": "SRC-NCRP-INSTITUTIONAL",
            "name": "National Cyber Crime Reporting Portal (NCRP / I4C)",
            "category": "Complaints Intake",
            "dataset_type": DataSourceType.INSTITUTIONAL_FEED.value,
            "status": SourceStatus.INTEGRATION_READY.value,
            "is_live": False,
            "records_count": 0,
            "description": "Direct API integration schema for MHA / I4C complaint dispatch.",
            "auth_required": True,
            "disclaimer": "Awaiting institutional API credentials and MHA authorization. Prototype uses synthetic data.",
        }

    def fetch_complaint(self, complaint_id: str) -> Optional[Dict[str, Any]]:
        return None

    def search_complaints(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        return []


class BankTransactionAdapter(TransactionSource):
    """Institutional adapter interface for NPCI / Core Banking SFMS feeds."""

    def get_source_metadata(self) -> Dict[str, Any]:
        return {
            "source_id": "SRC-NPCI-BANKING",
            "name": "NPCI / Bank Core Banking SFMS & UPI Feeds",
            "category": "Banking Ledger",
            "dataset_type": DataSourceType.INSTITUTIONAL_FEED.value,
            "status": SourceStatus.AWAITING_AUTH.value,
            "is_live": False,
            "records_count": 0,
            "description": "Secure webhook adapter for real-time inter-bank debit/credit notifications.",
            "auth_required": True,
            "disclaimer": "Requires RBI regulatory approval and participating bank SFMS endpoints. Prototype uses synthetic data.",
        }

    def fetch_transaction(self, tx_id: str) -> Optional[Dict[str, Any]]:
        return None

    def get_account_ledger(self, account_id: str) -> List[Dict[str, Any]]:
        return []


class ATMNetworkAdapter(ATMSource):
    """Institutional adapter interface for National Financial Switch (NFS) ATM networks."""

    def get_source_metadata(self) -> Dict[str, Any]:
        return {
            "source_id": "SRC-ATM-NFS",
            "name": "NFS / Bank ATM Telemetry & Cash-Out Feed",
            "category": "Geospatial Terminals",
            "dataset_type": DataSourceType.INSTITUTIONAL_FEED.value,
            "status": SourceStatus.INTEGRATION_READY.value,
            "is_live": False,
            "records_count": 0,
            "description": "Cash dispenser telemetry feed for instant ATM withdrawal notification.",
            "auth_required": True,
            "disclaimer": "Awaiting NFS gateway integration. Prototype uses curated demonstration dataset.",
        }

    def get_all_atms(self) -> List[Dict[str, Any]]:
        return []

    def get_atm_by_id(self, atm_id: str) -> Optional[Dict[str, Any]]:
        return None


class InstitutionalPoliceAdapter(PoliceUnitSource):
    """Institutional adapter interface for State Police CCTNS & Dial 112 CAD."""

    def get_source_metadata(self) -> Dict[str, Any]:
        return {
            "source_id": "SRC-POLICE-CAD-112",
            "name": "Emergency Response Support System (ERSS / Dial 112 CAD)",
            "category": "Tactical Operations",
            "dataset_type": DataSourceType.INSTITUTIONAL_FEED.value,
            "status": SourceStatus.INTEGRATION_READY.value,
            "is_live": False,
            "records_count": 0,
            "description": "Computer-Aided Dispatch (CAD) interface for real-time patrol unit coordinates.",
            "auth_required": True,
            "disclaimer": "Requires state police nodal authorization. Prototype uses curated static units.",
        }

    def get_available_units(self) -> List[Dict[str, Any]]:
        return []


# ─────────────────────────────────────────────────────────
# REGISTRY & ADAPTER FACTORY
# ─────────────────────────────────────────────────────────

class IntegrationRegistry:
    """Central registry providing unified access to data sources."""

    _instance = None

    def __init__(self):
        self.complaint_source: ComplaintSource = SyntheticComplaintSource()
        self.transaction_source: TransactionSource = SyntheticTransactionSource()
        self.atm_source: ATMSource = CuratedATMSource()
        self.police_unit_source: PoliceUnitSource = StaticPoliceUnitSource()

        self.institutional_adapters = [
            NCRPComplaintAdapter(),
            BankTransactionAdapter(),
            ATMNetworkAdapter(),
            InstitutionalPoliceAdapter(),
        ]

    @classmethod
    def get_instance(cls) -> "IntegrationRegistry":
        if cls._instance is None:
            cls._instance = IntegrationRegistry()
        return cls._instance

    def list_all_sources(self) -> List[Dict[str, Any]]:
        """Returns honest metadata for all active prototype and institutional sources."""
        sources = [
            self.complaint_source.get_source_metadata(),
            self.transaction_source.get_source_metadata(),
            self.atm_source.get_source_metadata(),
            self.police_unit_source.get_source_metadata(),
        ]
        for adapter in self.institutional_adapters:
            sources.append(adapter.get_source_metadata())
        return sources


def get_integration_registry() -> IntegrationRegistry:
    return IntegrationRegistry.get_instance()
