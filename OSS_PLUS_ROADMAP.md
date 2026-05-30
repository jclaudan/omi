# Omi — Open Source Plus : Roadmap d'intégration

Branch: `feat/use-only-opensource-alternative`

---

## Vision

Un **mode switcher** au premier lancement de l'app Omi.
L'utilisateur choisit entre deux modes, et l'app s'adapte entièrement à ce choix.

| Mode | Description |
|---|---|
| **Officiel** | Comportement Omi actuel — Firebase, Deepgram, Pinecone, OpenAI. Rien ne change. |
| **Open Source+** | Stack entièrement self-hosted — Supabase, Qdrant, Faster-Whisper, Ollama. Aucun token API obligatoire. |

Le code des deux modes **cohabite** dans la même codebase sans se casser mutuellement.
Les rebases sur `main` (upstream Omi) produisent le moins de conflits possible.

---

## Architecture cible

```
App Flutter (1er lancement)
    │
    ▼
┌─────────────────────────────────┐
│         Choix du mode           │
│                                 │
│   ○  Officiel (Omi Cloud)       │
│   ○  Open Source+               │
└──────────┬──────────────────────┘
           │ si OSS+
           ▼
┌─────────────────────────────────┐
│       Onboarding OSS+           │
│                                 │
│  • URL Supabase                 │
│  • Clé anonyme Supabase         │
│  • URL Qdrant                   │
│  • URL Faster-Whisper (batch)   │
│  • URL Faster-Whisper (stream)  │
│  • URL Ollama (optionnel)       │
│                                 │
│  → Test de connexion live       │
│  → Création du compte user      │
└──────────┬──────────────────────┘
           │
           ▼
  App en mode OSS+ (persisté dans SharedPreferences)
           │
    ┌──────┴───────┐
    │              │
    ▼              ▼
Auth            Données
Supabase        Firestore (v1) → Supabase PostgreSQL (v2 futur)
    │
    ▼
Services métier
• STT batch      → Faster-Whisper  :8001
• STT streaming  → Faster-Whisper-WS :8002
• Vectors        → Qdrant          :6333
• Storage        → MinIO           :9000
• Search         → Typesense       :8108
• LLM            → Ollama          :11434 (optionnel)
• MCPs / addons  → inchangés ✅
           │
           ▼
┌─────────────────────────────────┐
│     Dashboard santé services    │
│                                 │
│  ● Supabase      ✓ connecté    │
│  ● Qdrant        ✓ connecté    │
│  ● Whisper       ✓ connecté    │
│  ● Typesense     ✓ connecté    │
│  ● MinIO         ✓ connecté    │
│  ● Ollama        ✗ offline     │
└─────────────────────────────────┘
```

---

## Contrainte clé : cohabitation sans conflits

### Problème actuel

Les commits déjà mergés dans la branche qui remplacent GCS→MinIO et Pinecone→Qdrant
**modifient directement** les fichiers existants (`storage.py`, `vector_db.py`).
Résultat : chaque fois que l'équipe Omi touche ces fichiers sur `main`, un conflit de rebase
est garanti.

### Solution : pattern Strategy

Au lieu de modifier les fichiers existants, on crée des implémentations parallèles et une
factory qui sélectionne la bonne selon la configuration.

```
# Exemple pour le storage
backend/utils/storage/
    gcs.py        ← fichier original de main — on n'y touche JAMAIS
    minio.py      ← notre ajout, nouveau fichier
    factory.py    ← renvoie l'un ou l'autre selon OMI_STORAGE_BACKEND

# Même logique pour vector DB
backend/database/
    vector_db_pinecone.py   ← original main
    vector_db_qdrant.py     ← notre ajout
    vector_db.py            ← factory
```

La rule d'or : **ne jamais modifier un fichier existant de `main`**.
Toujours créer un fichier parallèle + une factory qui orchestre.

---

## Roadmap — étapes dans l'ordre

### Étape 1 — Refactoring Strategy (prérequis technique)
**Complexité : Moyenne | Priorité : Bloquante**

Transformer les fichiers déjà modifiés en pattern Strategy pour éviter les conflits futurs.

- [ ] `backend/utils/storage/` → `gcs.py` + `minio.py` + `factory.py`
- [ ] `backend/database/vector_db.py` → `vector_db_pinecone.py` + `vector_db_qdrant.py` + `vector_db.py` (factory)
- [ ] Variable d'env `OMI_STORAGE_BACKEND=gcs|minio`
- [ ] Variable d'env `OMI_VECTOR_BACKEND=pinecone|qdrant`
- [ ] Variable d'env `OMI_STT_BACKEND=deepgram|faster_whisper`
- [ ] Variable d'env `OMI_LLM_BACKEND=openai|anthropic|ollama`

---

### Étape 2 — Mode selector dans l'app Flutter
**Complexité : Faible | Priorité : Haute**

Nouvel écran au premier lancement, avant l'onboarding existant.

- [x] `AppMode` enum : `official` | `opensourcePlus` → `app/lib/backend/schema/app_mode.dart`
- [x] Stockage dans `SharedPreferencesUtil` (`ossAppMode`) + préférences OSS+ services
- [x] Écran de sélection → `app/lib/pages/onboarding/mode_selector.dart`
- [x] Routing conditionnel : si `appMode == official` → onboarding Omi existant, sinon → onboarding OSS+
- [ ] L'app injecte `AppMode` dans un provider global accessible partout (différé à Étape 4)

---

### Étape 3 — Onboarding OSS+
**Complexité : Moyenne | Priorité : Haute**

Flux de configuration guidé, affiché uniquement en mode OSS+.

**Écrans :** ✅ Tous implémentés dans `app/lib/pages/onboarding/oss_plus/`
1. **Écran accueil OSS+** → `step_welcome.dart`
2. **Supabase** → `step_supabase.dart`
3. **Services STT** → `step_stt.dart`
4. **Qdrant** → `step_qdrant.dart`
5. **Stockage MinIO** → `step_minio.dart`
6. **Ollama** → `step_ollama.dart`
7. **Test de connexion** → `step_test.dart`

**Test de connexion :**
- Chaque service est pingué en temps réel pendant la saisie
- Impossible de passer à l'étape suivante si le service est inaccessible (sauf Ollama = optionnel)
- Tous les paramètres sont stockés chiffrés dans SharedPreferences

---

### Étape 4 — Supabase Auth (backend + Flutter)
**Complexité : Haute | Priorité : Haute** ✅ **DONE**

Remplacement de Firebase Auth en mode OSS+. En mode Officiel, Firebase Auth est inchangé.

**Backend :**
- [x] `backend/utils/auth/firebase_auth.py` ← code existant déplacé ici
- [x] `backend/utils/auth/supabase_auth.py` ← nouveau, vérifie JWT HS256 avec `SUPABASE_JWT_SECRET`
- [x] `backend/utils/auth/factory.py` ← sélectionne selon `OMI_AUTH_BACKEND=firebase|supabase`
- [x] `backend/dependencies.py` → `get_current_user_id()` délègue à la factory

**Flutter app :**
- [x] `supabase_flutter: ^2.8.0` ajouté dans `pubspec.yaml`
- [x] `app/lib/services/oss_supabase_service.dart` — singleton client Supabase
- [x] `AuthService.signInWithSupabase()` / `signUpWithSupabase()` ajoutés
- [x] `AuthService.isSignedIn()` / `getIdToken()` / `signOut()` routent selon `appMode`
- [x] Supabase initialisé au démarrage uniquement si `appMode == opensourcePlus`
- [x] `StepAuth` (étape 8) — écran email/password dans l'onboarding OSS+
- [x] L10n : 8 nouvelles clés traduites en 49 langues

---

### Étape 5 — Initialisation utilisateur sur Supabase
**Complexité : Moyenne | Priorité : Haute** ✅ **DONE**

Création et gestion du profil utilisateur sur l'instance Supabase self-hosted.

- [x] Écran inscription/connexion Supabase (email + password) — fait à l'Étape 4 (`StepAuth`)
- [x] Script SQL Supabase — `selfhost/supabase/migrations/001_profiles.sql` : table `profiles` + trigger auto-create + RLS
- [x] Création du profil dans la table `profiles` Supabase après inscription (trigger PostgreSQL + belt-and-suspenders via endpoint)
- [x] Backend `backend/utils/oss_supabase_client.py` — client REST Supabase (httpx, sans nouvelle dépendance)
- [x] Backend `backend/routers/oss_user.py` — POST `/v1/oss/profile/init` (upsert profil, auth via JWT existant)
- [x] Flutter `app/lib/backend/http/api/oss_user.dart` — helper `initOssUserProfile(email)`
- [x] `StepAuth` appelle `initOssUserProfile` après sign-up/sign-in Supabase
- [x] Migration du token Supabase dans les headers API — fait à l'Étape 4 (`AuthService.getIdToken()`)
- [x] Refresh automatique du token — fait à l'Étape 4 (`OssSupabaseService.getAccessToken()`)

---

### Étape 6 — Dashboard santé des services
**Complexité : Faible | Priorité : Moyenne** ✅ **DONE**

Écran accessible depuis les paramètres en mode OSS+.

- [x] Ping de chaque service toutes les 30 secondes (Timer.periodic 30s)
- [x] Indicateur visuel : ● vert (connecté) / ● rouge (hors ligne) / ● orange (latence élevée > 2000ms)
- [x] Affichage de la latence en ms
- [x] Bouton "Reconfigurer" → ouvre l'écran de config du service concerné (StepSupabase, StepStt, StepQdrant, StepMinio, StepOllama)
- [x] Bouton "Tester maintenant" pour forcer un check immédiat
- [x] Entrée "Services OSS+" dans le settings drawer (uniquement en mode OSS+)
- [x] L10n : 5 nouvelles clés traduites en 49 langues

**Services monitorés :**
| Service | Endpoint de santé |
|---|---|
| Supabase | `GET /rest/v1/` |
| Qdrant | `GET /health` |
| Faster-Whisper | `GET /health` |
| Faster-Whisper-WS | `GET /health` |
| MinIO | `GET /minio/health/live` |
| Typesense | `GET /health` |
| Ollama | `GET /api/tags` |

---

### Étape 7 — Migration Firestore → Supabase PostgreSQL
**Complexité : Très haute | Priorité : Basse (v2)** ✅ **DONE (fondation)**

Remplacement du stockage de données principal. En OSS+, Supabase gère l'auth ;
cette étape ajoute les tables Postgres et la couche repository pour migrer les données.

- [x] Schéma PostgreSQL — `selfhost/supabase/migrations/002_core_schema.sql` : tables `conversations`, `memories`, `action_items`, `people` avec RLS et index
- [x] Couche repository abstraite — `backend/database/repo/base.py` : Protocols Python `ConversationRepo`, `MemoryRepo`, `ActionItemRepo`
- [x] Implémentations Supabase — `repo/supabase_conversations.py`, `repo/supabase_memories.py`, `repo/supabase_action_items.py` via REST API httpx (zero nouvelle dépendance)
- [x] Adaptateurs Firestore — wrap des modules existants sans les modifier
- [x] Factory — `backend/database/repo/factory.py` : sélectionne selon `OMI_DB_BACKEND=firestore|supabase`
- [x] Script de migration — `selfhost/scripts/migrate_firestore_to_supabase.py` : Firestore → Supabase Postgres (un user ou --all avec fichier de mapping)
- [x] Tests — `backend/tests/unit/test_repo_factory.py` : factory, adapters, fail-open sans config

**Variables d'env backend à ajouter (en plus de SUPABASE_URL/KEY) :**
```
OMI_DB_BACKEND=supabase   # défaut: firestore
```

**Routing implémenté (Étape 10) :**
- `database/conversations.py` : `upsert_conversation`, `get_conversation`, `get_conversations`, `update_conversation`, `delete_conversation` routent vers `SupabaseConversationRepo` quand `OMI_DB_BACKEND=supabase`
- `database/memories.py` : `create_memory`, `get_memory`, `get_memories`, `update_memory_fields`, `delete_memory` routent vers `SupabaseMemoryRepo`
- `database/action_items.py` : `create_action_item`, `get_action_item`, `get_action_items`, `update_action_item`, `delete_action_item` routent vers `SupabaseActionItemRepo`

**Ce qui reste (scope v3) :**
- Fonctions spécialisées non couvertes par le repo : `update_conversation_status`, `mark_action_item_completed`, `edit_memory`, sous-collections photos, goals, daily_summaries
- Chiffrement côté application pour les segments dans Postgres
- Migration des sous-collections Firestore (chat, daily_summaries, goals…)

---

### Étape 8 — STT streaming : routing Faster-Whisper dans transcribe.py
**Complexité : Faible** ✅ **DONE**

- [x] Import `process_audio_whisper_ws` dans `routers/transcribe.py`
- [x] Dispatch dans `_process_stt()` : si `stt_service == STTService.whisper_ws` → `process_audio_whisper_ws`, sinon `process_audio_dg`
- [x] Idem pour le cas multi-channel (une connexion Whisper WS par channel)

**Variable d'env backend :**
```
FASTER_WHISPER_WS_URL=ws://faster-whisper-ws:8002   # active le backend Whisper streaming
# DEEPGRAM_API_KEY doit être absent pour que la sélection soit automatique
```

---

### Étape 9 — STT batch : routing Faster-Whisper dans sync.py
**Complexité : Faible** ✅ **DONE**

- [x] `faster_whisper_prerecorded_from_bytes` dans `utils/stt/pre_recorded.py` — POST multipart vers `/transcribe`
- [x] `faster_whisper_prerecorded(audio_url)` — télécharge l'audio puis appelle `from_bytes`
- [x] `get_prerecorded_transcript(audio_url, ...)` — factory : route vers FW si `FASTER_WHISPER_URL` est défini et `DEEPGRAM_API_KEY` absent
- [x] `routers/sync.py` appelle `get_prerecorded_transcript` à la place de `deepgram_prerecorded`

**Variable d'env backend :**
```
FASTER_WHISPER_URL=http://faster-whisper:8001   # active le backend batch Whisper
```

---

### Étape 10 — DB factory : routing CRUD vers Supabase dans les modules database/
**Complexité : Haute** ✅ **DONE (CRUD de base)**

Les fonctions CRUD de base dans les modules `database/` existants routent maintenant vers `SupabaseConversationRepo` / `SupabaseMemoryRepo` / `SupabaseActionItemRepo` quand `OMI_DB_BACKEND=supabase`.

**`database/conversations.py` :**
- [x] `upsert_conversation` — dispatch Supabase en tête de fonction
- [x] `get_conversation` — refactoré : dispatch public + `_get_conversation_firestore` (décorée)
- [x] `get_conversations` — refactoré : dispatch public + `_get_conversations_firestore` (décorée)
- [x] `update_conversation` — dispatch Supabase en tête de fonction
- [x] `delete_conversation` — dispatch Supabase en tête de fonction

**`database/memories.py` :**
- [x] `create_memory` — dispatch public + `_create_memory_firestore` (décorée)
- [x] `get_memory` — refactoré : dispatch public + `_get_memory_firestore` (décorée)
- [x] `get_memories` — dispatch Supabase en tête de fonction
- [x] `update_memory_fields` — dispatch Supabase en tête de fonction
- [x] `delete_memory` — dispatch Supabase en tête de fonction

**`database/action_items.py` :**
- [x] `create_action_item` — dispatch Supabase en tête de fonction
- [x] `get_action_item` — dispatch Supabase en tête de fonction
- [x] `get_action_items` — dispatch Supabase en tête de fonction
- [x] `update_action_item` — dispatch Supabase en tête de fonction
- [x] `delete_action_item` — dispatch Supabase en tête de fonction

**Fonctions spécialisées non routées (scope v3) :**
- `update_conversation_status`, `set_conversation_as_discarded`, `get_in_progress_conversation` → Firestore only
- `edit_memory`, `change_memory_visibility`, `review_memory` → Firestore only
- `mark_action_item_completed`, `batch_update_action_items` → via `update_action_item` donc OK en Supabase
- Sous-collections Firestore (photos, fal_whisperx, chat, goals, daily_summaries) → scope v3

---

### Étape 11 — Scope v3 : fonctions spécialisées + chiffrement Postgres
**Complexité : Haute** ✅ **DONE**

**Migrations SQL :**
- [x] `003_memories_extra_fields.sql` : `user_review`, `reviewed`, `edited`, `kg_extracted`, `conversation_id` sur `memories`
- [x] `004_conversations_encryption.sql` : `transcript_segments_encrypted` (flag) sur `conversations`

**Chiffrement AES-256-GCM des segments (`SupabaseConversationRepo`) :**
- [x] `_apply_encryption` : sérialise + chiffre `transcript_segments` avant POST Supabase
- [x] `_apply_decryption` : déchiffre + désérialise au retour de GET
- [x] Toutes les lectures (get_conversation, get_conversations, get_by_status) déchiffrent
- [x] Désactivable via `SUPABASE_ENCRYPT_SEGMENTS=false`
- [x] Réutilise `ENCRYPTION_SECRET` + dérivation HKDF-SHA256 par uid

**Conversations — fonctions spécialisées :**
- [x] `upsert_conversation` : refactorisé en wrapper public + `_upsert_conversation_firestore` (décorée) — corrige bug double chiffrement
- [x] `update_conversation_title` → `update_conversation(uid, id, {'title': title})`
- [x] `update_conversation_summary` → `overview` column ou `apps_response` JSONB
- [x] `update_conversation_status` → `update_conversation(uid, id, {'status': status})`
- [x] `set_conversation_as_discarded` → `update_conversation(uid, id, {'discarded': True})`
- [x] `get_in_progress_conversation` → `SupabaseConversationRepo.get_by_status(uid, 'in_progress')`
- [x] `get_processing_conversations` → wrapper public + `_get_processing_conversations_firestore`

**Memories — fonctions spécialisées :**
- [x] `edit_memory` → `update_memory_fields(uid, id, {'content': value, 'edited': True})`
- [x] `change_memory_visibility` → `update_memory_fields(uid, id, {'visibility': value})`
- [x] `review_memory` → `update_memory_fields(uid, id, {'reviewed': True, 'user_review': value})`

**LLM Ollama :**
- [x] Déjà présent depuis l'étape 1 dans `utils/llm/clients.py` — `OLLAMA_BASE_URL` + pas de `OPENAI_API_KEY`

**Variables d'env :**
```
SUPABASE_ENCRYPT_SEGMENTS=false   # pour désactiver le chiffrement (défaut: true)
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2             # défaut
```

---

## État actuel de la branche

### Ce qui est fait ✅

| Composant | Statut | Notes |
|---|---|---|
| MinIO (remplace GCS) | ✅ Strategy pattern | `OMI_STORAGE_BACKEND=minio` |
| Qdrant (remplace Pinecone) | ✅ Strategy pattern | `QDRANT_URL` |
| Faster-Whisper streaming | ✅ Routé dans transcribe.py | `FASTER_WHISPER_WS_URL` |
| Faster-Whisper batch | ✅ Routé dans sync.py | `FASTER_WHISPER_URL` |
| Typesense self-hosted | ✅ Dans docker-compose | Prêt |
| Ollama LLM local | ✅ Dans docker-compose (optionnel) | Prêt |
| GPU NVIDIA (RTX 4090) | ✅ Dockerfile.cuda + deploy block | Prêt |
| docker-compose.yml complet | ✅ Tous les services | Prêt |
| `.env.selfhosted.example` | ✅ Template commenté | Prêt |
| `SELFHOST.md` | ✅ Documentation | Prêt |
| Supabase Auth | ✅ Étapes 4-5 | `OMI_AUTH_BACKEND=supabase` |
| Dashboard santé services | ✅ Étape 6 | Mode OSS+ uniquement |
| DB factory Supabase | ✅ Étapes 7+10+11 | `OMI_DB_BACKEND=supabase` |
| Chiffrement Postgres segments | ✅ Étape 11b | `SUPABASE_ENCRYPT_SEGMENTS=true` (défaut) |
| Routage LLM Ollama | ✅ Déjà présent | `OLLAMA_BASE_URL` + pas de `OPENAI_API_KEY` |

### Ce qui reste à faire 🔲

| Composant | Scope | Complexité |
|---|---|---|
| Sous-collections Firestore (photos, chat, goals, daily_summaries) | v4 | Très haute |
| Fonctions DB très spécialisées (segment_text, audio_chunks, fal_whisperx) | v4 | Haute |
| Chiffrement contenu memories dans Postgres | v4 | Faible |

---

## Principe directeur

> **Ne jamais modifier un fichier existant de `main`. Toujours créer en parallèle.**

Chaque service ajouté = un nouveau fichier, jamais une modification d'un fichier Omi existant.
Les factories lisent une variable d'environnement pour choisir l'implémentation.
En mode Officiel, le code suit exactement le même chemin qu'avant cette branche.
