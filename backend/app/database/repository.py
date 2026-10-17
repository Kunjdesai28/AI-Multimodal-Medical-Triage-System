"""
Multi-Tenant Repository Architecture for TRIAGEAI.

1. Master Database (triageai_master):
   - institutions collection: Registry of hospitals, clinics, and emergency centers.

2. Dedicated Tenant Database (triageai_clinic_<institution_id>):
   - patients collection: Active patient directory
   - assessments collection: Full multimodal assessments
   - triage_results collection: Prioritization outcomes & KTAS levels
   - risk_timeline collection: Dynamic trajectory time-series
   - users collection: Staff & administrator user accounts
"""
import os
import re
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from .connection import DatabaseManager


class MasterRepository:
    """Manages the central hospital & clinic registry in triageai_master."""

    def __init__(self):
        self.db_mgr = DatabaseManager.get_db()
        self.local_institutions_file = os.path.join(self.db_mgr.local_master_dir, "institutions.json")
        self._init_local_storage()

    def _init_local_storage(self):
        if not os.path.exists(self.local_institutions_file):
            with open(self.local_institutions_file, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _read_local_institutions(self) -> List[Dict[str, Any]]:
        try:
            with open(self.local_institutions_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _write_local_institutions(self, items: List[Dict[str, Any]]):
        with open(self.local_institutions_file, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)

    @staticmethod
    def sanitize_institution(doc: Dict[str, Any]) -> Dict[str, Any]:
        """Strips passwordHash and sensitive internals before returning."""
        res = dict(doc)
        res.pop("passwordHash", None)
        res.pop("passwordHashLower", None)
        res.pop("password", None)
        if "_id" in res:
            res["_id"] = str(res["_id"])
        if "id" not in res and "_id" in res:
            res["id"] = res["_id"]
        return res

    def find_institution_by_id(self, inst_id: str) -> Optional[Dict[str, Any]]:
        """Finds institution specifically by institutionId or username (case-insensitive)."""
        if not inst_id:
            return None
        clean = inst_id.strip().lower()
        master_db = self.db_mgr.get_master_db()
        if master_db is not None:
            regex_pat = f"^{re.escape(clean)}$"
            doc = master_db.institutions.find_one({
                "$or": [
                    {"institutionId": {"$regex": regex_pat, "$options": "i"}},
                    {"username": {"$regex": regex_pat, "$options": "i"}}
                ]
            })
            if doc:
                doc["_id"] = str(doc["_id"])
                return doc
        else:
            items = self._read_local_institutions()
            for it in items:
                fields = [it.get("institutionId", ""), it.get("username", "")]
                if any(f and f.strip().lower() == clean for f in fields):
                    return it
        return None

    def find_institution_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Finds institution specifically by officialEmail or administratorEmail (case-insensitive)."""
        if not email:
            return None
        clean = email.strip().lower()
        master_db = self.db_mgr.get_master_db()
        if master_db is not None:
            regex_pat = f"^{re.escape(clean)}$"
            doc = master_db.institutions.find_one({
                "$or": [
                    {"officialEmail": {"$regex": regex_pat, "$options": "i"}},
                    {"administratorEmail": {"$regex": regex_pat, "$options": "i"}}
                ]
            })
            if doc:
                doc["_id"] = str(doc["_id"])
                return doc
        else:
            items = self._read_local_institutions()
            for it in items:
                fields = [it.get("officialEmail", ""), it.get("administratorEmail", "")]
                if any(f and f.strip().lower() == clean for f in fields):
                    return it
        return None

    def get_institution_by_identifier(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Finds institution by institutionId, username, officialEmail, administratorEmail,
        hospitalName, institutionName, or contactNumber.
        Case-insensitive match, trimmed, and phone-number tolerant.
        """
        if not identifier:
            return None
        ident_clean = identifier.strip().lower()
        ident_digits = re.sub(r'\D', '', identifier.strip())

        master_db = self.db_mgr.get_master_db()
        if master_db is not None:
            regex_pat = f"^{re.escape(ident_clean)}$"
            queries = [
                {"institutionId": {"$regex": regex_pat, "$options": "i"}},
                {"username": {"$regex": regex_pat, "$options": "i"}},
                {"officialEmail": {"$regex": regex_pat, "$options": "i"}},
                {"administratorEmail": {"$regex": regex_pat, "$options": "i"}},
                {"hospitalName": {"$regex": regex_pat, "$options": "i"}},
                {"institutionName": {"$regex": regex_pat, "$options": "i"}}
            ]
            if ident_digits and len(ident_digits) >= 10:
                queries.append({"contactNumber": {"$regex": re.escape(ident_digits[-10:])}})
                queries.append({"officialPhone": {"$regex": re.escape(ident_digits[-10:])}})

            doc = master_db.institutions.find_one({"$or": queries})
            if doc:
                doc["_id"] = str(doc["_id"])
                return doc
        else:
            items = self._read_local_institutions()
            for it in items:
                fields = [
                    it.get("institutionId", ""),
                    it.get("username", ""),
                    it.get("officialEmail", ""),
                    it.get("administratorEmail", ""),
                    it.get("hospitalName", ""),
                    it.get("institutionName", "")
                ]
                if any(f and f.strip().lower() == ident_clean for f in fields):
                    return it
                if ident_digits and len(ident_digits) >= 10:
                    phones = [
                        re.sub(r'\D', '', it.get("contactNumber", "") or ""),
                        re.sub(r'\D', '', it.get("officialPhone", "") or "")
                    ]
                    last10 = ident_digits[-10:]
                    if any(p and (p == ident_digits or p.endswith(last10) or last10 in p) for p in phones):
                        return it
        return None

    def find_institution_for_google_user(self, google_email: str) -> Optional[Dict[str, Any]]:
        """
        Finds institution where administratorEmail or officialEmail matches the Google account.
        """
        if not google_email:
            return None
        clean_email = google_email.strip().lower()

        # Check master DB
        master_inst = self.get_institution_by_identifier(clean_email)
        if master_inst:
            return master_inst

        # Also check if user exists in any tenant database's users collection
        if self.db_mgr.is_mongo and self.db_mgr.mongo_client is not None:
            db_names = self.db_mgr.mongo_client.list_database_names()
            for dbn in db_names:
                if dbn.startswith("triageai_clinic_"):
                    tdb = self.db_mgr.get_tenant_db(dbn)
                    user_doc = tdb.users.find_one({"email": {"$regex": f"^{re.escape(clean_email)}$", "$options": "i"}})
                    if user_doc:
                        inst_id = user_doc.get("institutionId")
                        if inst_id:
                            return self.get_institution_by_identifier(inst_id)

        return None

    def create_institution(self, inst_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        ATOMIC REGISTRATION & DATABASE INITIALIZATION:
        1. Validate uniqueness in triageai_master.
        2. Generate safe databaseName: triageai_clinic_<institutionId>.
        3. Create initial Administrator user.
        4. Initialize dedicated tenant database and 5 collections.
        5. Store master institution record in triageai_master.institutions.
        6. Rollback if any step fails.
        """
        inst_id = inst_data.get("institutionId", "").strip()
        email = inst_data.get("officialEmail", "").strip().lower()
        admin_email = inst_data.get("administratorEmail", "").strip().lower()

        # Step 1: Uniqueness checks
        if self.find_institution_by_id(inst_id):
            raise ValueError(f"Institution ID or Username '{inst_id}' is already registered.")

        if self.find_institution_by_email(email):
            raise ValueError(f"Official Email '{email}' is already registered.")

        # Step 2 & 3: Generate safe tenant database name
        database_name = DatabaseManager.sanitize_db_name(inst_id)

        # Step 4: Prepare Administrator user record
        now_iso = datetime.now().isoformat()
        admin_user_id = f"USR-ADMIN-{uuid.uuid4().hex[:6].upper()}"
        admin_user = {
            "userId": admin_user_id,
            "institutionId": inst_id,
            "name": inst_data.get("administratorName", "Administrator"),
            "email": admin_email or email,
            "designation": inst_data.get("administratorDesignation", "Hospital Administrator"),
            "phone": inst_data.get("administratorPhone", ""),
            "role": "Institution Administrator",
            "authProvider": "google" if inst_data.get("googleAuthEnabled") else "local",
            "createdAt": now_iso
        }

        # Step 5: Initialize dedicated tenant database
        try:
            self.db_mgr.initialize_tenant_database(database_name, admin_user)
        except Exception as e:
            raise RuntimeError(f"Failed to create tenant database '{database_name}': {str(e)}")

        # Step 6: Store in master database
        record = dict(inst_data)
        if "id" not in record and "_id" not in record:
            record["id"] = f"INST-{uuid.uuid4().hex[:8].upper()}"
        record["databaseName"] = database_name
        record["createdAt"] = record.get("createdAt", now_iso)
        record["updatedAt"] = now_iso
        record["accountStatus"] = record.get("accountStatus", "active")
        record["googleAuthEnabled"] = bool(inst_data.get("googleAuthEnabled", False))

        master_db = self.db_mgr.get_master_db()
        try:
            if master_db is not None:
                master_db.institutions.insert_one(record)
                record["_id"] = str(record.get("_id", record["id"]))
            else:
                items = self._read_local_institutions()
                items.append(record)
                self._write_local_institutions(items)
        except Exception as e:
            # Rollback: Drop tenant DB if master insertion failed
            self.db_mgr.drop_tenant_database(database_name)
            raise RuntimeError(f"Master registry write failed ({str(e)}). Tenant database rolled back.")

        return self.sanitize_institution(record)

    def update_institution(self, institution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Updates an existing institution record in master database or local storage."""
        inst_id = institution_data.get("institutionId", "").strip()
        email = institution_data.get("officialEmail", "").strip().lower()
        now_iso = datetime.now().isoformat()
        institution_data["updatedAt"] = now_iso

        master_db = self.db_mgr.get_master_db()
        if master_db is not None:
            master_db.institutions.update_one(
                {"$or": [{"institutionId": inst_id}, {"officialEmail": email}]},
                {"$set": institution_data},
                upsert=True
            )
        else:
            items = self._read_local_institutions()
            updated = False
            for i, it in enumerate(items):
                if (it.get("institutionId", "").strip().lower() == inst_id.lower() or 
                    it.get("officialEmail", "").strip().lower() == email):
                    items[i] = {**it, **institution_data}
                    updated = True
                    break
            if not updated:
                items.append(institution_data)
            self._write_local_institutions(items)

        return self.sanitize_institution(institution_data)


class TenantRepository:
    """Manages patient, assessment, and triage operations inside a dedicated tenant database."""

    def __init__(self, database_name: str):
        self.database_name = database_name
        self.db_mgr = DatabaseManager.get_db()
        self.db = self.db_mgr.get_tenant_db(database_name)
        self.local_tenant_dir = os.path.join(self.db_mgr.local_tenants_dir, database_name)
        os.makedirs(self.local_tenant_dir, exist_ok=True)
        self._init_local_files()

    def _init_local_files(self):
        for coll in ["patients", "assessments", "triage_results", "risk_timeline", "users"]:
            fpath = os.path.join(self.local_tenant_dir, f"{coll}.json")
            if not os.path.exists(fpath):
                with open(fpath, "w", encoding="utf-8") as f:
                    json.dump([] if coll != "risk_timeline" else {}, f)

    def _read_local_coll(self, coll: str) -> Any:
        fpath = os.path.join(self.local_tenant_dir, f"{coll}.json")
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return [] if coll != "risk_timeline" else {}

    def _write_local_coll(self, coll: str, data: Any):
        fpath = os.path.join(self.local_tenant_dir, f"{coll}.json")
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_next_patient_id(self) -> str:
        """
        Generates the next sequential Patient ID starting automatically from PAT-01 (e.g. PAT-01, PAT-02, ...).
        Inspects existing patients and assessments strictly in this tenant's database to guarantee continuity.
        """
        existing_ids = set()
        if self.db is not None:
            try:
                for doc in self.db.patients.find({}, {"patientId": 1, "patient_id": 1}):
                    pid = doc.get("patientId") or doc.get("patient_id")
                    if pid:
                        existing_ids.add(str(pid).strip().lower())
                for doc in self.db.assessments.find({}, {"patientId": 1, "patient_id": 1}):
                    pid = doc.get("patientId") or doc.get("patient_id")
                    if pid:
                        existing_ids.add(str(pid).strip().lower())
            except Exception as e:
                print(f"[TenantRepository] Error reading patient IDs: {e}")
        else:
            for p in self._read_local_coll("patients"):
                pid = p.get("patientId") or p.get("patient_id")
                if pid:
                    existing_ids.add(str(pid).strip().lower())
            for a in self._read_local_coll("assessments"):
                pid = a.get("patientId") or a.get("patient_id")
                if pid:
                    existing_ids.add(str(pid).strip().lower())

        # Extract sequence numbers from IDs matching PAT-XX (ignoring random legacy 4-digit numbers >= 500)
        seq_nums = []
        for raw_id in existing_ids:
            m = re.match(r"^pat-(\d+)$", raw_id)
            if m:
                val = int(m.group(1))
                if val < 500:
                    seq_nums.append(val)

        next_seq = (max(seq_nums) + 1) if seq_nums else 1

        # Guarantee no collision with any existing ID
        while True:
            candidate = f"PAT-{next_seq:02d}"
            if candidate.lower() not in existing_ids and f"pat-{next_seq}" not in existing_ids:
                return candidate
            next_seq += 1

    def save_assessment(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Saves assessment strictly inside this institution's dedicated database.
        Populates collections: assessments, patients, triage_results, risk_timeline.
        """
        record = dict(assessment_data)
        asm_id = record.get("id") or record.get("assessment_id") or record.get("assessmentId") or f"ASM-{uuid.uuid4().hex[:8].upper()}"
        record["id"] = asm_id
        record["assessment_id"] = asm_id
        record["assessmentId"] = asm_id
        if "timestamp" not in record:
            record["timestamp"] = datetime.now().isoformat()

        patient_id = record.get("patient_id") or record.get("patientId")
        if not patient_id or not str(patient_id).strip():
            patient_id = self.get_next_patient_id()

        patient_name = record.get("patient_name") or record.get("patientName") or "Unknown Patient"
        record["patient_id"] = patient_id
        record["patientId"] = patient_id
        record["patient_name"] = patient_name
        record["patientName"] = patient_name

        # 1. Save in assessments collection
        if self.db is not None:
            self.db.assessments.insert_one(record)
            record["_id"] = str(record.get("_id", record["id"]))
        else:
            items = self._read_local_coll("assessments")
            items.insert(0, record)
            self._write_local_coll("assessments", items)

        # 2. Update patients collection
        if patient_id:
            patient_summary = {
                "patientId": patient_id,
                "patient_id": patient_id,
                "patientName": patient_name,
                "patient_name": patient_name,
                "latestPriority": record.get("priority"),
                "latestPriorityLabel": record.get("priority_label"),
                "latestRiskScore": record.get("risk_score"),
                "latestConfidence": record.get("confidence"),
                "lastAssessedAt": record.get("timestamp"),
                "createdAt": record.get("timestamp"),
            }
            if self.db is not None:
                self.db.patients.update_one(
                    {"$or": [{"patientId": patient_id}, {"patient_id": patient_id}]},
                    {"$set": patient_summary, "$inc": {"totalAssessments": 1}},
                    upsert=True
                )
            else:
                patients = self._read_local_coll("patients")
                existing = next((p for p in patients if p.get("patient_id") == patient_id or p.get("patientId") == patient_id), None)
                if existing:
                    existing.update(patient_summary)
                    existing["totalAssessments"] = existing.get("totalAssessments", 1) + 1
                else:
                    patient_summary["totalAssessments"] = 1
                    patients.append(patient_summary)
                self._write_local_coll("patients", patients)

        # 3. Save in triage_results collection
        triage_summary = {
            "resultId": f"RES-{uuid.uuid4().hex[:6].upper()}",
            "assessmentId": record.get("assessment_id"),
            "patientId": patient_id,
            "patientName": patient_name,
            "priority": record.get("priority"),
            "priorityLevel": record.get("priority_level"),
            "priorityColor": record.get("priority_color"),
            "riskScore": record.get("risk_score"),
            "targetTime": record.get("target_time"),
            "createdAt": record.get("timestamp"),
        }
        if self.db is not None:
            self.db.triage_results.insert_one(triage_summary)
        else:
            results = self._read_local_coll("triage_results")
            results.insert(0, triage_summary)
            self._write_local_coll("triage_results", results)

        # 4. Append to risk_timeline
        if patient_id:
            self.append_timeline_point(patient_id, record)

        return record

    def list_assessments(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Lists patient assessments strictly from this tenant's database."""
        if self.db is not None:
            cursor = self.db.assessments.find().sort("timestamp", -1).limit(limit)
            results = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                results.append(doc)
            return results
        else:
            items = self._read_local_coll("assessments")
            return items[:limit]

    def get_assessment_by_id(self, assessment_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single assessment by ID from this tenant database."""
        if self.db is not None:
            res = self.db.assessments.find_one({"$or": [{"assessment_id": assessment_id}, {"id": assessment_id}]})
            if res:
                res["_id"] = str(res["_id"])
                return res
        else:
            items = self._read_local_coll("assessments")
            for it in items:
                if it.get("assessment_id") == assessment_id or it.get("id") == assessment_id:
                    return it
        return None

    def append_timeline_point(self, patient_id: str, assessment_record: Dict[str, Any]):
        """Appends a longitudinal trajectory point in this tenant's risk_timeline."""
        point = {
            "observation_id": f"OBS-{uuid.uuid4().hex[:6].upper()}",
            "assessment_id": assessment_record.get("assessment_id"),
            "timestamp": assessment_record.get("timestamp", datetime.now().strftime("%H:%M:%S")),
            "risk_score": assessment_record.get("risk_score"),
            "priority": assessment_record.get("priority"),
            "priority_color": assessment_record.get("priority_color"),
            "vitals_summary": {
                "hr": assessment_record.get("clinical_indices", {}).get("hr"),
                "sbp": assessment_record.get("clinical_indices", {}).get("sbp"),
                "spo2": assessment_record.get("clinical_indices", {}).get("spo2"),
                "shock_index": assessment_record.get("clinical_indices", {}).get("shock_index")
            },
            "modalities_count": assessment_record.get("modalities_used", {}).get("count", 1)
        }

        if self.db is not None:
            self.db.risk_timeline.update_one(
                {"$or": [{"patientId": patient_id}, {"patient_id": patient_id}]},
                {
                    "$push": {"trajectory": point},
                    "$set": {
                        "patientId": patient_id,
                        "patient_id": patient_id,
                        "patientName": assessment_record.get("patient_name", "Patient"),
                        "patient_name": assessment_record.get("patient_name", "Patient"),
                        "last_updated": datetime.now().isoformat()
                    }
                },
                upsert=True
            )
        else:
            timelines = self._read_local_coll("risk_timeline")
            if patient_id not in timelines:
                timelines[patient_id] = {
                    "patient_id": patient_id,
                    "patient_name": assessment_record.get("patient_name", "Patient"),
                    "trajectory": []
                }
            traj = timelines[patient_id]["trajectory"]
            if traj:
                prev_risk = traj[-1]["risk_score"]
                delta = round(point["risk_score"] - prev_risk, 1)
                point["delta_risk"] = delta
                point["delta_direction"] = "increased" if delta > 0 else ("decreased" if delta < 0 else "unchanged")
            else:
                point["delta_risk"] = 0.0
                point["delta_direction"] = "initial"

            traj.append(point)
            self._write_local_coll("risk_timeline", timelines)

    def get_patient_timeline(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves patient longitudinal trajectory strictly from this tenant's database."""
        if self.db is not None:
            doc = self.db.risk_timeline.find_one({"$or": [{"patientId": patient_id}, {"patient_id": patient_id}]})
            if doc:
                doc["_id"] = str(doc["_id"])
                return doc
        else:
            timelines = self._read_local_coll("risk_timeline")
            return timelines.get(patient_id)
        return None

    def clear_all(self) -> Dict[str, Any]:
        """Clears all assessments, patients, and timelines within THIS tenant only."""
        counts = {"assessments": 0, "timelines": 0, "patients": 0}
        if self.db is not None:
            counts["assessments"] = self.db.assessments.delete_many({}).deleted_count
            counts["timelines"] = self.db.risk_timeline.delete_many({}).deleted_count
            counts["patients"] = self.db.patients.delete_many({}).deleted_count
            self.db.triage_results.delete_many({})
        else:
            counts["assessments"] = len(self._read_local_coll("assessments"))
            self._write_local_coll("assessments", [])
            self._write_local_coll("patients", [])
            self._write_local_coll("triage_results", [])
            self._write_local_coll("risk_timeline", {})
        return counts

    def get_metrics(self) -> Dict[str, int]:
        """Returns patient and assessment count in this tenant database."""
        if self.db is not None:
            return {
                "patients": self.db.patients.count_documents({}),
                "assessments": self.db.assessments.count_documents({})
            }
        else:
            return {
                "patients": len(self._read_local_coll("patients")),
                "assessments": len(self._read_local_coll("assessments"))
            }

    def get_database_info(self) -> Dict[str, Any]:
        metrics = self.get_metrics()
        return {
            "type": "MongoDB Multi-Tenant Cluster" if self.db_mgr.is_mongo else "Local Multi-Tenant Atomic Storage",
            "connected": True,
            "master_database": self.db_mgr.master_db_name,
            "tenant_database": self.database_name,
            "uri": self.db_mgr.mongo_uri if self.db_mgr.is_mongo else "local_filesystem",
            "counts": {
                "institutions": self.db_mgr.get_institution_count(),
                "patients": metrics["patients"],
                "assessments": metrics["assessments"]
            }
        }


class TriageRepository:
    """
    Unified Multi-Tenant Facade.
    Provides Master repository operations and resolves Tenant repositories on the fly.
    """
    def __init__(self, tenant_db_name: Optional[str] = None):
        self.master = MasterRepository()
        self.db_mgr = DatabaseManager.get_db()
        
        # If tenant_db_name is not provided, default to fallback clinic
        self.tenant_db_name = tenant_db_name or "triageai_clinic_default"
        self._tenant_repo = TenantRepository(self.tenant_db_name)

    @classmethod
    def for_institution(cls, institution_id_or_db_name: str):
        """Factory method to get a tenant-scoped repository instance."""
        if not institution_id_or_db_name:
            return cls("triageai_clinic_default")

        # If it's already a databaseName format:
        if institution_id_or_db_name.startswith("triageai_clinic_"):
            return cls(institution_id_or_db_name)

        # Lookup in master repository to resolve databaseName
        master = MasterRepository()
        inst = master.get_institution_by_identifier(institution_id_or_db_name)
        if inst and inst.get("databaseName"):
            return cls(inst["databaseName"])

        # Otherwise synthesize safe database name
        return cls(DatabaseManager.sanitize_db_name(institution_id_or_db_name))

    # Master DB proxy methods
    def find_institution_by_id(self, inst_id: str) -> Optional[Dict[str, Any]]:
        return self.master.find_institution_by_id(inst_id)

    def find_institution_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        return self.master.find_institution_by_email(email)

    def get_institution_by_identifier(self, identifier: str) -> Optional[Dict[str, Any]]:
        return self.master.get_institution_by_identifier(identifier)

    def find_institution_for_google_user(self, email: str) -> Optional[Dict[str, Any]]:
        return self.master.find_institution_for_google_user(email)

    def create_institution(self, inst_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.master.create_institution(inst_data)

    def sanitize_institution(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        return self.master.sanitize_institution(doc)

    # Tenant DB proxy methods (scoped to self.tenant_db_name)
    def save_assessment(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._tenant_repo.save_assessment(assessment_data)

    def list_assessments(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._tenant_repo.list_assessments(limit=limit)

    def get_assessment_by_id(self, assessment_id: str) -> Optional[Dict[str, Any]]:
        return self._tenant_repo.get_assessment_by_id(assessment_id)

    def get_patient_timeline(self, patient_id: str) -> Optional[Dict[str, Any]]:
        return self._tenant_repo.get_patient_timeline(patient_id)

    def append_timeline_point(self, patient_id: str, record: Dict[str, Any]):
        return self._tenant_repo.append_timeline_point(patient_id, record)

    def clear_all(self) -> Dict[str, Any]:
        return self._tenant_repo.clear_all()

    def get_next_patient_id(self) -> str:
        return self._tenant_repo.get_next_patient_id()

    def get_database_info(self) -> Dict[str, Any]:
        metrics = self._tenant_repo.get_metrics()
        return {
            "type": "MongoDB Multi-Tenant Cluster" if self.db_mgr.is_mongo else "Local Multi-Tenant Atomic Storage",
            "connected": True,
            "master_database": self.db_mgr.master_db_name,
            "tenant_database": self.tenant_db_name,
            "uri": self.db_mgr.mongo_uri if self.db_mgr.is_mongo else "local_filesystem",
            "counts": {
                "institutions": self.db_mgr.get_institution_count(),
                "patients": metrics["patients"],
                "assessments": metrics["assessments"]
            }
        }
