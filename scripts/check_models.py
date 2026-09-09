"""
scripts/check_models.py — Lightweight Pre-Flight ML Model Preparation Check
==========================================================================
Verifies that required ML models, schemas, and metadata are present and loadable
WITHOUT executing expensive offline training during application startup.

Returns exit code 0 on success, 1 on missing/corrupted artifacts.
"""

import os
import sys
import json

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Reconfigure stdout to UTF-8 on Windows if supported
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

OK_SYM = "[OK]"
ERR_SYM = "[ERROR]"


def check_models(verbose: bool = True) -> bool:
    if verbose:
        print("[DRISHTI] Checking ML models & artifacts...")

    errors = []

    # 1. Location Model Check
    loc_model_path = os.path.join(ROOT_DIR, "models", "location_classifier.joblib")
    loc_cal_path = os.path.join(ROOT_DIR, "models", "location_calibrator.joblib")
    if not os.path.exists(loc_model_path) or not os.path.exists(loc_cal_path):
        errors.append(("Location model", "models/location_classifier.joblib or calibrator missing."))
    else:
        try:
            import joblib
            clf = joblib.load(loc_model_path)
            cal = joblib.load(loc_cal_path)
            if verbose:
                print(f"{OK_SYM} Location model (XGBoost + Isotonic Calibrator)")
        except Exception as e:
            errors.append(("Location model", f"Failed to load: {e}"))

    # 2. Time Model Check
    time_model_path = os.path.join(ROOT_DIR, "models", "time_predictor.json")
    if not os.path.exists(time_model_path):
        errors.append(("Time model", "models/time_predictor.json missing."))
    else:
        try:
            import xgboost as xgb
            booster = xgb.Booster()
            booster.load_model(time_model_path)
            if verbose:
                print(f"{OK_SYM} Time model (XGBoost Regressor)")
        except Exception as e:
            errors.append(("Time model", f"Failed to load: {e}"))

    # 3. Amount Model Check
    amount_model_path = os.path.join(ROOT_DIR, "models", "amount_predictor.joblib")
    if not os.path.exists(amount_model_path):
        errors.append(("Amount model", "models/amount_predictor.joblib missing."))
    else:
        try:
            import joblib
            amt_model = joblib.load(amount_model_path)
            if verbose:
                print(f"{OK_SYM} Amount model (GradientBoosting Cash-Out Regressor)")
        except Exception as e:
            errors.append(("Amount model", f"Failed to load: {e}"))

    # 4. Risk Model Check
    risk_model_path = os.path.join(ROOT_DIR, "models", "risk_classifier.joblib")
    if not os.path.exists(risk_model_path):
        errors.append(("Risk model", "models/risk_classifier.joblib missing."))
    else:
        try:
            import joblib
            risk_model = joblib.load(risk_model_path)
            if verbose:
                print(f"{OK_SYM} Risk model (RandomForest Classifier)")
        except Exception as e:
            errors.append(("Risk model", f"Failed to load: {e}"))

    # 5. Feature Schema Check
    schema_path = os.path.join(ROOT_DIR, "models", "feature_schema.json")
    if not os.path.exists(schema_path):
        errors.append(("Feature schema", "models/feature_schema.json missing."))
    else:
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)
            if "models" in schema or "location_features" in schema:
                model_count = len(schema.get("models", {}))
                feat_count = len(schema.get("models", {}).get("location_model", {}).get("feature_names", []))
                if verbose:
                    print(f"{OK_SYM} Feature schema (v{schema.get('schema_version', '1.0')}, {model_count} models, {feat_count} location features)")
            else:
                errors.append(("Feature schema", "Invalid schema structure: neither 'models' nor 'location_features' found"))
        except Exception as e:
            errors.append(("Feature schema", f"Failed to parse: {e}"))

    # 6. Model Metadata Check
    meta_files = [
        ("Location metadata", "models/location_meta.json"),
        ("Time metadata", "models/time_meta.json"),
        ("Amount metadata", "models/amount_meta.json"),
        ("Risk metadata", "models/risk_meta.json"),
    ]
    meta_ok = True
    for name, mpath in meta_files:
        full_mpath = os.path.join(ROOT_DIR, mpath)
        if not os.path.exists(full_mpath):
            errors.append((name, f"{mpath} missing."))
            meta_ok = False
        else:
            try:
                with open(full_mpath, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                ver = meta.get("version") or meta.get("model_version")
                if not ver:
                    errors.append((name, f"Missing version/model_version in {mpath}"))
                    meta_ok = False
            except Exception as e:
                errors.append((name, f"Corrupted metadata in {mpath}: {e}"))
                meta_ok = False
    if meta_ok and verbose:
        print(f"{OK_SYM} Model metadata (Location, Time, Amount, Risk)")

    # 7. Metrics & Environment
    for name, apath in [("Evaluation metrics", "models/metrics.json"), ("Environment config", "models/environment.json")]:
        full_apath = os.path.join(ROOT_DIR, apath)
        if not os.path.exists(full_apath):
            errors.append((name, f"{apath} missing."))
        elif verbose:
            print(f"{OK_SYM} {name}")

    if errors:
        print("\n" + "=" * 60)
        for item, err in errors:
            print(f"{ERR_SYM} {item}: {err}")
        print("=" * 60)
        print("[DRISHTI] Run offline model training to generate missing artifacts:")
        print("    python -m backend.ml.train_all\n")
        return False

    if verbose:
        print("\n[OK] All ML models and artifacts are ready.")
    return True


if __name__ == "__main__":
    success = check_models(verbose=True)
    sys.exit(0 if success else 1)
