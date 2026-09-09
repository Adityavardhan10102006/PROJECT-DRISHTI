"""
tests/test_oop_architecture.py — Project DRISHTI
=================================================
Comprehensive Test Suite for Object-Oriented Architecture:
  1. Core Domain Models (Encapsulation, Validation, Domain Rules)
     - Complaint
     - Transaction
     - MoneyTrail (Composition over Transactions)
     - ATM
     - PoliceUnit
     - IntelligenceCase & FiveDIntelligence
  2. Polymorphism & Model Abstraction
     - BasePredictor ABC
     - PredictionStrategy (ML vs Heuristic Fallback)
     - ATMScoringStrategy (Distance, Risk, Composite)
     - PredictorFactory
  3. Repositories (Data Access Abstraction)
     - TransactionDataSource (CSV vs Database)
     - TransactionRepository
     - UserRepository
  4. Services & Dependency Injection
     - PasswordHasher & SessionManager
     - AuthenticationService
     - ATMPredictor & FeasibilityCalculator
     - DrishtiIntelligenceService (End-to-End Orchestrator Facade)
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

# Domain models
from backend.domain.complaint import Complaint
from backend.domain.transaction import Transaction
from backend.domain.money_trail import MoneyTrail
from backend.domain.atm import ATM
from backend.domain.police_unit import PoliceUnit
from backend.domain.prediction import (
    PredictionResult,
    RiskPrediction,
    AmountPrediction,
    TimePrediction,
)
from backend.domain.intelligence_case import FiveDIntelligence, IntelligenceCase

# ML & Strategies
from backend.ml.base_predictor import BasePredictor, PredictorFactory
from backend.strategies.prediction_strategy import (
    PredictionStrategy,
    MLPredictionStrategy,
    HeuristicPredictionStrategy,
)
from backend.strategies.atm_scoring_strategy import (
    ATMScoringStrategy,
    DistanceScoringStrategy,
    RiskScoringStrategy,
    CompositeATMScoringStrategy,
)
from backend.ml.risk_predictor import CaseRiskPredictor, RiskExplainer
from backend.ml.amount_predictor import CashoutAmountPredictor
from backend.ml.time_predictor import TimeWindowPredictor

# Repositories & Services
from backend.repositories.transaction_repository import (
    TransactionDataSource,
    CSVTransactionDataSource,
    DatabaseTransactionDataSource,
    TransactionRepository,
)
from backend.repositories.user_repository import UserRepository
from backend.services.authentication_service import (
    PasswordHasher,
    SessionManager,
    AuthenticationService,
)
from backend.services.atm_service import ATMPredictor
from backend.services.feasibility_service import FeasibilityCalculator
from backend.services.drishti_service import DrishtiIntelligenceService


# =====================================================================
# 1. CORE DOMAIN MODELS — ENCAPSULATION & VALIDATION
# =====================================================================

class TestDomainComplaint:
    """Tests Complaint domain object encapsulation and validation."""

    def test_complaint_creation_and_properties(self):
        now = datetime.now(timezone.utc)
        c = Complaint(
            case_id="CASE-101",
            fraud_type="upi_fraud",
            amount=75000.0,
            timestamp=now,
            victim_lat=17.4435,
            victim_lon=78.3772,
            complaint_text="Lost money to fake lottery",
            bank_account="ACC-998877",
            city="Hyderabad",
        )
        assert c.case_id == "CASE-101"
        assert c.is_high_value(50000.0) is True
        assert c.is_high_value(100000.0) is False
        assert c.get_location() == (17.4435, 78.3772)
        assert c.has_coordinates() is True

        d = c.to_dict()
        assert d["case_id"] == "CASE-101"
        assert d["amount"] == 75000.0
        assert d["city"] == "Hyderabad"

    def test_complaint_validation_negative_amount(self):
        with pytest.raises(ValueError, match="cannot be negative"):
            Complaint(case_id="C-1", fraud_type="phishing", amount=-500.0)

    def test_complaint_validation_invalid_coordinates(self):
        with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
            Complaint(case_id="C-1", fraud_type="phishing", amount=100.0, victim_lat=150.0, victim_lon=78.0)


class TestDomainTransaction:
    """Tests Transaction domain object encapsulation."""

    def test_transaction_methods(self):
        t1 = Transaction(
            transaction_id="TXN-001",
            source_account="ACC-A",
            destination_account="ACC-B",
            amount=60000.0,
            timestamp=datetime(2026, 9, 9, 10, 0, tzinfo=timezone.utc),
            transaction_type="UPI",
            hop_number=1,
            commission_amount=1500.0,
        )
        t2 = Transaction(
            transaction_id="TXN-002",
            source_account="ACC-B",
            destination_account="ACC-C",
            amount=58500.0,
            timestamp=datetime(2026, 9, 9, 10, 5, tzinfo=timezone.utc),
            transaction_type="IMPS",
            hop_number=2,
            commission_amount=1000.0,
        )
        assert t1.is_high_value(50000.0) is True
        assert t1.is_suspicious() is True  # high value & commission
        assert t2.is_rapid(t1, max_minutes=10) is True
        assert t2.get_transfer_delay(t1) == 5.0

    def test_transaction_negative_amount_fails(self):
        with pytest.raises(ValueError, match="amount cannot be negative"):
            Transaction(
                transaction_id="TXN-X",
                source_account="ACC-A",
                destination_account="ACC-B",
                amount=-10.0,
            )


class TestDomainMoneyTrailComposition:
    """Tests MoneyTrail composite domain object."""

    def test_money_trail_composition_and_metrics(self):
        now = datetime.now(timezone.utc)
        txns = [
            Transaction("T1", "SRC", "MULE-1", 100000.0, now, hop_number=1, commission_amount=2000.0),
            Transaction("T2", "MULE-1", "MULE-2", 98000.0, now + timedelta(minutes=6), hop_number=2, commission_amount=1500.0),
            Transaction("T3", "MULE-2", "CASHOUT", 96500.0, now + timedelta(minutes=14), hop_number=3, commission_amount=0.0),
        ]
        trail = MoneyTrail(
            transactions=txns,
            starting_account="SRC",
            initial_amount=100000.0,
            final_cashout_amount=96500.0,
        )

        # Encapsulation & Composition
        assert trail.hop_count() == 3
        assert trail.total_amount() == 294500.0
        assert trail.total_commission() == 3500.0
        assert trail.detect_rapid_movement(max_hop_minutes=10) is True
        assert trail.detect_layering() is True

        # Graph generation
        graph_dict = trail.get_graph()
        assert len(graph_dict["nodes"]) == 4
        assert len(graph_dict["edges"]) == 3


class TestDomainATMAndPolice:
    """Tests ATM and PoliceUnit domain models."""

    def test_atm_distance(self):
        atm = ATM(
            atm_id="ATM-HYD-01",
            bank="State Bank of India",
            latitude=17.4400,
            longitude=78.3800,
            location_name="HITEC City ATM",
            is_24x7=True,
            cash_capacity="high",
        )
        dist = atm.distance_to(17.4450, 78.3850)
        assert 0.5 < dist < 1.5
        assert atm.is_open_now(hour=23) is True

    def test_police_unit_eta(self):
        unit = PoliceUnit(
            unit_id="UNIT-01",
            unit_name="Blue Colts Patrol 1",
            latitude=17.4300,
            longitude=78.3700,
            speed_kmh=40.0,
        )
        dist = unit.distance_to(17.4400, 78.3800)
        eta = unit.estimate_eta_minutes(dist)
        assert eta > 0.0
        assert unit.can_intercept(distance_km=dist, time_window_minutes=30.0) is True


# =====================================================================
# 2. POLYMORPHISM & MODEL ABSTRACTION
# =====================================================================

class TestPolymorphismAndPredictors:
    """Tests BasePredictor, PredictorFactory, and PredictionStrategy polymorphism."""

    def test_predictor_factory(self):
        risk_p = PredictorFactory.create_predictor("risk")
        assert isinstance(risk_p, BasePredictor)
        assert isinstance(risk_p, CaseRiskPredictor)

        amount_p = PredictorFactory.create_predictor("amount")
        assert isinstance(amount_p, BasePredictor)
        assert isinstance(amount_p, CashoutAmountPredictor)

        time_p = PredictorFactory.create_predictor("time")
        assert isinstance(time_p, BasePredictor)
        assert isinstance(time_p, TimeWindowPredictor)

    def test_prediction_strategy_polymorphism(self):
        """Demonstrates interchangeable ML and Heuristic prediction strategies."""
        # Heuristic Strategy
        heuristic_strat: PredictionStrategy = HeuristicPredictionStrategy(default_prediction=42.0)
        res_h = heuristic_strat.predict({"amount": 50000.0})
        assert res_h.model_source == "heuristic_fallback"
        assert res_h.prediction == 42.0

        # ML Strategy wrapping mock model
        mock_model = MagicMock()
        mock_model.predict.return_value = [78.5]
        ml_strat: PredictionStrategy = MLPredictionStrategy(
            model=mock_model,
            feature_names=["f1", "f2"],
            model_name="test_regressor",
        )
        res_ml = ml_strat.predict({"f1": 1.0, "f2": 2.0})
        assert res_ml.model_source == "trained_ml"
        assert res_ml.prediction == 78.5

    def test_atm_scoring_strategy_polymorphism(self):
        """Demonstrates polymorphism in ATM candidate scoring."""
        atm = ATM("A1", "HDFC", 17.4400, 78.3800, "Branch ATM")
        ctx = {"victim_lat": 17.4450, "victim_lon": 78.3850, "case_risk_score": 75.0}

        dist_strat = DistanceScoringStrategy(max_distance_km=10.0)
        score_dist = dist_strat.score(atm, ctx)
        assert 0.0 <= score_dist <= 1.0

        risk_strat = RiskScoringStrategy()
        score_risk = risk_strat.score(atm, ctx)
        assert score_risk == 0.75

        # Composite strategy combines both
        composite = CompositeATMScoringStrategy(strategies=[
            (dist_strat, 0.6),
            (risk_strat, 0.4),
        ])
        comp_score = composite.score(atm, ctx)
        assert 0.0 <= comp_score <= 1.0


# =====================================================================
# 3. REPOSITORY PATTERN
# =====================================================================

class TestRepositories:
    """Tests TransactionRepository and UserRepository abstractions."""

    def test_transaction_repository_csv_source(self):
        repo = TransactionRepository()
        assert repo.total_count() > 0
        # Lookup known transaction from synthetic dataset
        txns = repo.find_all(limit=10)
        assert len(txns) == 10
        assert isinstance(txns[0], Transaction)

        # Lookup by source account
        first_src = txns[0].source_account
        found = repo.find_by_source_account(first_src)
        assert len(found) >= 1
        assert found[0].source_account == first_src

    def test_transaction_repository_database_source_fallback(self):
        db_source = DatabaseTransactionDataSource(session_factory=None)
        repo = TransactionRepository(data_source=db_source)
        # Should gracefully return empty when DB session is not configured
        assert repo.find_by_transaction_id("TXN-NONEXIST") is None

    def test_user_repository(self):
        repo = UserRepository()
        admin = repo.find_by_username("admin")
        assert admin is not None
        assert admin.username == "admin"
        assert admin.role == "admin"

        # Safe dictionary representation does not expose hash
        safe = admin.to_safe_dict()
        assert "password_hash" not in safe
        assert safe["username"] == "admin"


# =====================================================================
# 4. SERVICES & DEPENDENCY INJECTION
# =====================================================================

class TestAuthenticationService:
    """Tests AuthenticationService facade with PasswordHasher & SessionManager."""

    def test_password_hasher_and_session_manager(self):
        hasher = PasswordHasher(rounds=4)
        hashed = hasher.hash("Secret@123")
        assert hasher.verify("Secret@123", hashed) is True
        assert hasher.verify("WrongPass", hashed) is False

        mgr = SessionManager(secret_key="test-secret-key-12345678901234567890", expiry_minutes=15)
        token = mgr.create_access_token({"sub": "analyst1", "role": "analyst"})
        decoded = mgr.decode_token(token)
        assert decoded["sub"] == "analyst1"
        assert decoded["role"] == "analyst"

    def test_auth_service_dependency_injection(self):
        mock_user_repo = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "mockuser"
        mock_user.role = "investigator"
        mock_user.password_hash = "mockhash"
        mock_user.to_safe_dict.return_value = {"username": "mockuser", "role": "investigator"}
        mock_user_repo.find_by_username_or_email.return_value = mock_user
        mock_user_repo.update_last_login.return_value = mock_user.to_safe_dict()

        mock_hasher = MagicMock()
        mock_hasher.verify.return_value = True

        service = AuthenticationService(
            user_repo=mock_user_repo,
            hasher=mock_hasher,
        )

        success, token_data, err, code = service.authenticate("mockuser", "password")
        assert success is True
        assert code == 200
        assert "access_token" in token_data
        assert token_data["user"]["username"] == "mockuser"


# =====================================================================
# 5. END-TO-END OOP DEMONSTRATION TEST
# =====================================================================

class TestEndToEndOOPDemonstration:
    """
    Demonstrates Section 30: Complaint -> DrishtiIntelligenceService -> IntelligenceCase
    Shows how multiple domain entities, ML predictors, and calculators collaborate.
    """

    def test_drishti_service_analyze_e2e(self):
        complaint = Complaint(
            case_id="DRISHTI-DEMO-001",
            fraud_type="upi_fraud",
            amount=85000.0,
            timestamp=datetime(2026, 9, 9, 10, 0, tzinfo=timezone.utc),
            victim_lat=17.4435,
            victim_lon=78.3772,
            complaint_text="Defrauded of Rs 85,000 via malicious UPI link.",
            bank_account="ACC-DEMO-100",
            city="Hyderabad",
        )

        service = DrishtiIntelligenceService()
        case: IntelligenceCase = service.analyze(complaint)

        # Verify Central IntelligenceCase composition
        assert isinstance(case, IntelligenceCase)
        assert case.complaint.case_id == "DRISHTI-DEMO-001"
        assert case.risk_score >= 0.0
        assert isinstance(case.risk_prediction, RiskPrediction)
        assert isinstance(case.amount_prediction, AmountPrediction)
        assert isinstance(case.time_prediction, TimePrediction)
        assert isinstance(case.money_trail, MoneyTrail)
        assert isinstance(case.five_d, FiveDIntelligence)
        assert len(case.top_k_atms) > 0

        # Serialization to dictionary
        case_dict = case.to_dict()
        assert "complaint" in case_dict
        assert "risk_prediction" in case_dict
        assert "amount_prediction" in case_dict
        assert "time_prediction" in case_dict
        assert "money_trail" in case_dict
        assert "five_d" in case_dict
        assert case_dict["five_d"]["where"] is not None
        assert case_dict["five_d"]["when"] is not None
        assert case_dict["five_d"]["amount"] is not None
        assert case_dict["five_d"]["why"] is not None
        assert case_dict["five_d"]["action"] is not None
