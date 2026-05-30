# OSS+ Remaining Tasks & Deployment Checklist

## ✅ **Complete & Done**

### Database Layer (22 Étapes)
- [x] Étape 1-7: Core routing (storage, vectors, conversations, memories)
- [x] Étape 8-10: STT routing, app-side ops
- [x] Étape 15: Chat sub-collection (messages, sessions, files)
- [x] Étape 16: Guards/middleware routing  
- [x] Étape 17: Apps system (CRUD, personas, public/private)
- [x] Étape 18: Enabled apps (Redis ↔ Supabase factory)
- [x] Étape 19: Daily summaries sub-collection
- [x] Étape 20: Goals + progress history
- [x] Étape 21: Conversation photos schema
- [x] Étape 22: Phone numbers sub-collection

**Status**: All 14 Supabase migrations + 9 repos ready ✅

---

## 📋 **Remaining Work**

### 1. **Docker & Deployment** (Priority: HIGH)

#### 1.1 Docker Compose Stack
- [ ] Create `docker-compose.yml` with:
  - Supabase (PostgreSQL + PostgREST)
  - Qdrant (vector DB)
  - MinIO (S3-compatible storage)
  - Faster-Whisper (STT service)
  - Ollama (LLM service)
  - Redis (caching, optional)
  - Backend API
  - Mobile app (optional)

**Files to Create**:
```
- docker-compose.yml
- docker/.env.example
- docker/postgres/init.sql (schema bootstrap)
- docker/supabase/docker-compose.yml (full Supabase stack)
- selfhost/setup.sh (automated setup script)
```

#### 1.2 Kubernetes Deployment (Optional)
- [ ] K8s manifests for:
  - Backend API
  - Supabase operators
  - Qdrant StatefulSet
  - MinIO Operator
  - Faster-Whisper deployment
  - Ollama GPU node pool

**Files to Create**:
```
- k8s/base/kustomization.yaml
- k8s/overlays/dev/
- k8s/overlays/prod/
- Helm chart (optional)
```

---

### 2. **Data Migration Tools** (Priority: HIGH)

#### 2.1 Firebase → Supabase Migration
- [ ] Migration script to:
  - Extract all user profiles from Firestore
  - Extract all conversations + segments
  - Extract all memories
  - Extract all action items
  - Extract all chat messages
  - Extract all apps (if any Cloud deployments)
  - Preserve encryption keys during migration

**Files to Create**:
```
- scripts/migrate/firestore_to_supabase.py
- scripts/migrate/config.yaml (migration settings)
- scripts/migrate/verify.py (validation script)
- scripts/migrate/rollback.py (safety rollback)
```

#### 2.2 Data Validation
- [ ] Script to verify:
  - All rows migrated correctly
  - Encryption keys still work
  - User counts match
  - Conversation counts match
  - No data loss

---

### 3. **Integration Testing** (Priority: HIGH)

#### 3.1 OSS+ Mode Tests
- [ ] Test suite for:
  - Auth flow (register, login, JWT)
  - Conversation CRUD operations
  - Memory operations (create, search, delete)
  - App marketplace operations
  - Chat messaging (encryption, decryption)
  - Daily summaries (creation, retrieval)
  - Goals (tracking progress)
  - STT integration (Faster-Whisper)
  - LLM routing (Ollama fallback)
  - Storage operations (MinIO)
  - Vector search (Qdrant)

**Files to Create**:
```
- backend/tests/integration/test_ossp_mode.py
- backend/tests/integration/conftest.py (fixtures for OSS+ test DB)
- app/integration_tests/ossp_mode_test.dart
```

#### 3.2 End-to-End Tests
- [ ] E2E tests for:
  - Full user onboarding in OSS+ mode
  - Audio recording → transcription → memories
  - Chat with apps
  - App marketplace browsing
  - Privacy settings (visibility, encryption)

**Files to Create**:
```
- e2e/tests/ossp_mode.e2e.ts (or equivalent)
- e2e/fixtures/ossp_mode_users.ts
```

---

### 4. **Admin Dashboard & Management** (Priority: MEDIUM)

#### 4.1 OSS+ Admin UI
- [ ] Dashboard for:
  - User management (view, suspend, delete)
  - Storage usage monitoring
  - Vector DB health
  - STT service status
  - LLM service status
  - Migration progress tracking
  - Backup/restore operations

**Files to Create**:
```
- selfhost/admin-dashboard/ (new app, could be React/Next.js)
- selfhost/admin-api/ (new backend routes)
- backend/routers/admin/ (admin endpoints)
```

#### 4.2 Monitoring & Observability
- [ ] Prometheus metrics for:
  - DB query latency (Supabase)
  - Vector DB hit rate (Qdrant)
  - Storage usage (MinIO)
  - API latency
  - Error rates

**Files to Create**:
```
- selfhost/monitoring/prometheus.yml
- selfhost/monitoring/grafana-dashboards/
- backend/utils/metrics.py (Prometheus integration)
```

---

### 5. **Documentation & Guides** (Priority: MEDIUM)

#### 5.1 Deployment Guide
- [ ] `SELFHOST_SETUP.md`:
  - Hardware requirements
  - Network setup
  - Domain configuration
  - SSL/TLS setup
  - Firewall rules
  - Backup strategy
  - Disaster recovery

#### 5.2 Configuration Guide
- [ ] `OSS_CONFIG.md`:
  - All environment variables explained
  - Service dependencies
  - Optional components (Redis, GPU for Ollama)
  - Performance tuning
  - Scaling guidelines

#### 5.3 Troubleshooting Guide
- [ ] `OSS_TROUBLESHOOTING.md`:
  - Common issues
  - Debugging steps
  - Log locations
  - Health check commands

#### 5.4 Migration Guide
- [ ] `MIGRATION_GUIDE.md`:
  - Step-by-step Firebase → Supabase
  - Data validation
  - Rollback procedures
  - Downtime planning

---

### 6. **Performance & Optimization** (Priority: LOW)

#### 6.1 Benchmarks
- [ ] Create benchmarks comparing:
  - Cloud mode vs OSS+ mode
  - Latency (API, DB, vector search)
  - Throughput (messages/sec)
  - Storage efficiency
  - CPU/memory usage

**Files to Create**:
```
- scripts/benchmarks/compare_modes.py
- scripts/benchmarks/latency_test.py
- docs/PERFORMANCE_BENCHMARKS.md
```

#### 6.2 Optimization
- [ ] Database tuning:
  - Index optimization
  - Query performance
  - Connection pooling
  - Cache strategies

- [ ] Vector DB tuning:
  - Index type selection
  - Query optimization
  - Memory usage

---

### 7. **Security Hardening** (Priority: MEDIUM)

#### 7.1 Security Audit
- [ ] Verify:
  - All RLS policies in place
  - CORS configuration
  - Rate limiting
  - Input validation
  - Encryption at rest and in transit

#### 7.2 Security Docs
- [ ] `OSS_SECURITY.md`:
  - Firewall rules
  - Network isolation
  - Secret management
  - Backup encryption
  - Audit logging

---

### 8. **Advanced Features** (Priority: LOW)

#### 8.1 High Availability
- [ ] Setup:
  - Database replication (if multi-node)
  - Service redundancy
  - Load balancing
  - Health checks & auto-restart

#### 8.2 Backup & Recovery
- [ ] Automated backups:
  - Daily database dumps
  - Incremental backups
  - Point-in-time recovery
  - Off-site backup storage

#### 8.3 Federation (Optional)
- [ ] Setup for:
  - Multi-site deployments
  - Data sync between sites
  - Failover between sites

---

## 📊 **Summary by Priority**

| Priority | Component | Status | Est. Effort |
|----------|-----------|--------|-------------|
| **HIGH** | Docker Compose | ⬜ | 2-3 days |
| **HIGH** | Data Migration Tools | ⬜ | 2-3 days |
| **HIGH** | Integration Tests | ⬜ | 3-4 days |
| **MEDIUM** | Admin Dashboard | ⬜ | 3-5 days |
| **MEDIUM** | Documentation | ⬜ | 2-3 days |
| **MEDIUM** | Security Hardening | ⬜ | 1-2 days |
| **LOW** | Performance Benchmarks | ⬜ | 1-2 days |
| **LOW** | Advanced Features | ⬜ | 5+ days |

**Total Estimated Effort**: 2-3 weeks for MVP (core functionality)

---

## 🚀 **MVP Deployment Path**

**Phase 1: Foundation (Week 1)**
1. ✅ Database layer complete (already done)
2. Docker Compose stack
3. Basic migration tooling
4. Integration tests (core paths)

**Phase 2: Validation (Week 2)**
1. Migration from test Firestore project
2. Admin dashboard (basic)
3. Security audit
4. Documentation

**Phase 3: Production Ready (Week 3)**
1. Performance optimization
2. HA setup (if needed)
3. Comprehensive documentation
4. Production deployment

---

## 📝 **Success Criteria**

- [ ] All 14 migrations execute successfully
- [ ] Data migrates from Firebase without loss
- [ ] All core features work in OSS+ mode
- [ ] No proprietary APIs required
- [ ] Can be deployed via Docker Compose
- [ ] Passes security audit
- [ ] Documentation complete
- [ ] Integration tests passing

---

**Last Updated**: 2026-05-30  
**Overall Status**: **Core implementation 100% ✅ | Deployment 10% ⬜**
