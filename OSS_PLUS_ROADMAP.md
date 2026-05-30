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

### Étape 7 — Migration Firestore → Supabase PostgreSQL *(futur)*
**Complexité : Très haute | Priorité : Basse (v2)**

Remplacement du stockage de données principal. Non bloquant pour la v1 — en OSS+, Supabase
gère l'auth mais Firestore peut rester pour les données dans un premier temps.

- [ ] Schéma PostgreSQL équivalent aux collections Firestore (users, conversations, memories, apps…)
- [ ] Couche repository abstraite : `ConversationRepository` → implémentée par Firestore ou Supabase Postgres
- [ ] Migration des données existantes (script de migration Firestore → Postgres)
- [ ] Tests de non-régression

---

## État actuel de la branche

### Ce qui est fait ✅

| Composant | Statut | Notes |
|---|---|---|
| MinIO (remplace GCS) | ✅ Backend modifié | À refactorer en Strategy (étape 1) |
| Qdrant (remplace Pinecone) | ✅ Backend modifié | À refactorer en Strategy (étape 1) |
| Faster-Whisper batch STT | ✅ Service + Dockerfile CPU + GPU | Prêt |
| Faster-Whisper-WS streaming | ✅ Service + Dockerfile CPU + GPU | Prêt |
| Typesense self-hosted | ✅ Dans docker-compose | Prêt |
| Ollama LLM local | ✅ Dans docker-compose (optionnel) | Prêt |
| GPU NVIDIA (RTX 4090) | ✅ Dockerfile.cuda + deploy block | Prêt |
| docker-compose.yml complet | ✅ Tous les services | Prêt |
| `.env.selfhosted.example` | ✅ Template commenté | Prêt |
| `SELFHOST.md` | ✅ Documentation | Prêt |

### Ce qui reste à faire 🔲

| Composant | Étape | Complexité |
|---|---|---|
| Refactoring Strategy (éviter conflits) | 1 | Moyenne |
| Mode selector Flutter | 2 | Faible |
| Onboarding OSS+ Flutter | 3 | Moyenne |
| Supabase Auth backend | 4 | Haute |
| Supabase Auth Flutter | 4 | Haute |
| Initialisation user Supabase | 5 | Moyenne |
| Dashboard santé services | 6 | Faible |
| Migration Firestore → Postgres | 7 | Très haute |

---

## Principe directeur

> **Ne jamais modifier un fichier existant de `main`. Toujours créer en parallèle.**

Chaque service ajouté = un nouveau fichier, jamais une modification d'un fichier Omi existant.
Les factories lisent une variable d'environnement pour choisir l'implémentation.
En mode Officiel, le code suit exactement le même chemin qu'avant cette branche.
