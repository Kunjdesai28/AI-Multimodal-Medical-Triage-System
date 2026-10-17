"""
Multi-Tenant Database Connection Manager for TRIAGEAI.

Architecture:
- Master Database: triageai_master
    └── institutions (central registry of hospitals & clinics)

- Dedicated Tenant Database per Institution:
    └── triageai_clinic_<institutionId>
        ├── patients
        ├── assessments
        ├── triage_results
        ├── risk_timeline
        └── users

Dynamic connection pooling: Reuses MongoClient instance across all tenant databases.
Seamless local multi-tenant atomic storage fallback if MongoDB is offline.
"""
import os
import re
import json
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class DatabaseManager:
    _instance = None

    def __init__(self):
        self.mongo_client = None
        self.master_db = None
        self.is_mongo = False
        self._tenant_db_cache: Dict[str, Any] = {}

        self.local_storage_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "data")
        )
        self.local_master_dir = os.path.join(self.local_storage_dir, "triageai_master")
        self.local_tenants_dir = os.path.join(self.local_storage_dir, "tenants")
        os.makedirs(self.local_master_dir, exist_ok=True)
        os.makedirs(self.local_tenants_dir, exist_ok=True)

        self.mongo_uri = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
        self.master_db_name = os.getenv("MONGODB_MASTER_DB", "triageai_master")
        self._init_connection()

    def _init_connection(self):
        try:
            from pymongo import MongoClient
            client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=1500)
            client.admin.command('ping')
            self.mongo_client = client
            self.master_db = client[self.master_db_name]
            self.is_mongo = True

            # Ensure master indexes
            self._init_master_indexes()
            logger.info(f"Connected to live MongoDB multi-tenant cluster: {self.mongo_uri} -> Master DB: '{self.master_db_name}'")
            print(f"[Database] Connected to live MongoDB: {self.mongo_uri} -> Master: '{self.master_db_name}'")
        except Exception as e:
            self.is_mongo = False
            logger.warning(f"MongoDB not reachable ({e}). Activating local multi-tenant atomic storage.")
            print(f"[Database] MongoDB unavailable ({e}). Using local multi-tenant persistence in {self.local_storage_dir}")

    def _init_master_indexes(self):
        """Creates unique constraints on the master institutions collection."""
        if not self.is_mongo or self.master_db is None:
            return
        try:
            self.master_db.institutions.create_index("institutionId", unique=True)
            self.master_db.institutions.create_index("officialEmail", unique=True)
            self.master_db.institutions.create_index("username", unique=True, sparse=True)
            self.master_db.institutions.create_index("databaseName", unique=True)
        except Exception as e:
            logger.warning(f"Could not build master indexes: {e}")

    @staticmethod
    def sanitize_db_name(institution_id: str) -> str:
        """
        Generates a safe, sanitized MongoDB database name.
        Format: triageai_clinic_<sanitized_institution_id>
        """
        clean_id = re.sub(r'[^a-zA-Z0-9_]', '_', institution_id.strip()).strip('_')
        return f"triageai_clinic_{clean_id}"

    def get_master_db(self):
        """Returns handle to triageai_master database."""
        if self.is_mongo and self.master_db is not None:
            return self.master_db
        return None

    def get_tenant_db(self, database_name: str):
        """
        Dynamically retrieves or caches a dedicated tenant database handle from connection pool.
        """
        if not database_name:
            database_name = "triageai_clinic_default"

        if self.is_mongo and self.mongo_client is not None:
            if database_name not in self._tenant_db_cache:
                self._tenant_db_cache[database_name] = self.mongo_client[database_name]
            return self._tenant_db_cache[database_name]

        return None

    def initialize_tenant_database(self, database_name: str, admin_user: Dict[str, Any]) -> bool:
        """
        Initializes a newly registered institution's dedicated database.
        Creates collections: patients, assessments, triage_results, risk_timeline, users.
        Initializes indexes and stores the initial Administrator user record.
        """
        if self.is_mongo and self.mongo_client is not None:
            try:
                db = self.get_tenant_db(database_name)

                # Initialize collections by creating indexes
                db.patients.create_index("patientId")
                db.patients.create_index("createdAt")

                db.assessments.create_index("assessmentId", unique=True, sparse=True)
                db.assessments.create_index("patientId")
                db.assessments.create_index("createdAt")

                db.triage_results.create_index("patientId")
                db.triage_results.create_index("priority")
                db.triage_results.create_index("createdAt")

                db.risk_timeline.create_index("patientId")
                db.risk_timeline.create_index("timestamp")

                db.users.create_index("userId", unique=True)
                db.users.create_index("email")

                # Insert initial administrator user
                if admin_user:
                    db.users.insert_one(dict(admin_user))

                logger.info(f"Initialized dedicated tenant database '{database_name}' with 5 collections.")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize tenant database '{database_name}': {e}")
                # Rollback by dropping partially created database
                self.drop_tenant_database(database_name)
                raise e
        else:
            # Local atomic storage fallback
            tenant_path = os.path.join(self.local_tenants_dir, database_name)
            os.makedirs(tenant_path, exist_ok=True)
            for coll in ["patients", "assessments", "triage_results", "risk_timeline", "users"]:
                fpath = os.path.join(tenant_path, f"{coll}.json")
                if not os.path.exists(fpath):
                    initial_data = [dict(admin_user)] if coll == "users" and admin_user else []
                    with open(fpath, "w", encoding="utf-8") as f:
                        json.dump(initial_data, f, indent=2)
            return True

    def drop_tenant_database(self, database_name: str):
        """Rolls back and drops an institution database if registration fails."""
        if self.is_mongo and self.mongo_client is not None:
            try:
                self.mongo_client.drop_database(database_name)
                self._tenant_db_cache.pop(database_name, None)
                logger.info(f"Dropped tenant database '{database_name}' (Rollback).")
            except Exception as e:
                logger.warning(f"Error dropping database '{database_name}': {e}")
        else:
            tenant_path = os.path.join(self.local_tenants_dir, database_name)
            if os.path.exists(tenant_path):
                import shutil
                shutil.rmtree(tenant_path, ignore_errors=True)

    @property
    def db_name(self) -> str:
        return self.master_db_name

    def get_assessment_count(self) -> int:
        count = 0
        if self.is_mongo and self.mongo_client is not None:
            try:
                for name in self.mongo_client.list_database_names():
                    if name.startswith("triageai_clinic_"):
                        count += self.mongo_client[name].assessments.count_documents({})
            except Exception:
                pass
        return count

    def get_patient_count(self) -> int:
        count = 0
        if self.is_mongo and self.mongo_client is not None:
            try:
                for name in self.mongo_client.list_database_names():
                    if name.startswith("triageai_clinic_"):
                        count += self.mongo_client[name].patients.count_documents({})
            except Exception:
                pass
        return count

    def get_institution_count(self) -> int:
        if self.is_mongo and self.master_db is not None:
            return self.master_db.institutions.count_documents({})
        try:
            path = os.path.join(self.local_master_dir, "institutions.json")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return len(json.load(f))
        except Exception:
            pass
        return 0

    @classmethod
    def get_db(cls):
        if cls._instance is None:
            cls._instance = DatabaseManager()
        return cls._instance
