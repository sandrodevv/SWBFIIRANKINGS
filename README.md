# Star Wars Battlefront II Player Rankings

Community-driven player rankings for every Hero and Villain in Star Wars Battlefront II. Rankings update dynamically based on votes.

## Stack

- **Backend:** Django, Django REST Framework, SQLite (dev) / PostgreSQL (production)
- **Frontend:** HTML shells, SCSS, Vanilla JavaScript (API-first — no server-side rendering of dynamic data)

## Setup

### 1. Create virtual environment and install dependencies

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Environment variables

Copy `.env.example` to `.env` and adjust as needed:

```bash
copy .env.example .env
```

For PostgreSQL, set `DATABASE_URL`:

```
DATABASE_URL=postgresql://user:password@localhost:5432/battlefront_rankings
```

### 3. Migrate and seed

```bash
python manage.py migrate
python manage.py seed_rankings
```

Re-seed with fresh vote data:

```bash
python manage.py seed_rankings --force
```

### 4. Run the development server

**Windows (recommended — no venv activation needed):**

```bash
runserver.bat
```

Or call the venv Python directly:

```bash
venv\Scripts\python.exe manage.py runserver
```

**Linux / macOS:**

```bash
source venv/bin/activate
python manage.py runserver
```

> **Note:** On Windows PowerShell, `venv\Scripts\activate` may fail due to execution policy. Use `runserver.bat` or `venv\Scripts\python.exe` instead of `python manage.py`.

Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## Character Images

Drop your character image files into:

```
frontend/static/images/characters/
```

Use the character slug as the filename:

```
frontend/static/images/characters/luke-skywalker.jpg
frontend/static/images/characters/darth-vader.jpg
frontend/static/images/characters/leia-organa.jpg
... (one file per character slug)
```

Supported formats: `.jpg`, `.png`, `.webp`

Until images are added, the UI shows a styled fallback with character initials and side-colored gradients.

### All character slugs

**Heroes:** `luke-skywalker`, `leia-organa`, `han-solo`, `chewbacca`, `lando-calrissian`, `rey`, `finn`, `obi-wan-kenobi`, `anakin-skywalker`, `yoda`, `bb-8`

**Villains:** `darth-vader`, `emperor-palpatine`, `darth-maul`, `boba-fett`, `bossk`, `iden-versio`, `kylo-ren`, `captain-phasma`, `general-grievous`, `count-dooku`, `bb-9e`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/characters/` | List all characters with top player summary |
| GET | `/api/characters/{slug}/` | Character detail |
| GET | `/api/characters/{slug}/rankings/` | Rankings for a character |
| POST | `/api/rankings/{id}/vote/` | Cast a vote (1 per character per IP/device per week) |
| GET | `/api/characters/{slug}/vote-status/` | Check if the current visitor can vote |
| GET | `/api/champions/` | #1 player for every character |

## Player assignment rules

Each player can be ranked on **at most one Hero and one Villain** character.

Example: **Sandro** could appear on Luke Skywalker's leaderboard (Hero) and Darth Vader's leaderboard (Villain), but not on both Luke and Obi-Wan.

To clean up existing duplicate assignments:

```bash
.\manage.bat enforce_player_assignments
```

Rebuild seed data with the rule applied:

```bash
.\manage.bat seed_rankings --force
```

## Vote limits & weekly reset

Rankings use **two vote counters** per player/character:

| Field | Purpose |
|-------|---------|
| `votes` | Current weekly count — shown on the site, **resets to 0** each period |
| `all_time_votes` | Lifetime total — kept in the database for future features |

Each **7-day period** (configurable via `VOTE_COOLDOWN_DAYS`):

- Weekly `votes` reset to **0** for every character ranking
- Rankings reorder from scratch for the new week
- `all_time_votes` is **never reset**

The reset runs automatically on the first API request after a period expires. You can also trigger it manually:

```bash
.\manage.bat reset_weekly_votes
```

Each visitor can vote **once per character per period**. Restrictions use:

- **Hashed IP address** — prevents repeated votes from the same network
- **Signed HttpOnly cookie** — ties votes to the same browser/device

When a new period starts, vote cooldowns reset too — everyone can vote again.

## Project Structure

```
apps/characters/     Character model, admin, seed command
apps/rankings/       Player & CharacterRanking models
api/                 DRF serializers, views, routers
frontend/templates/  HTML shells (no dynamic DB content)
frontend/static/     SCSS, JavaScript, images
```

## SCSS

Styles are written in SCSS under `frontend/static/scss/` and compiled automatically by `django-sass-processor` when templates load `{% sass_src 'scss/main.scss' %}`.

## Admin

Create a superuser to manage data via Django admin:

```bash
python manage.py createsuperuser
```

Admin panel: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

## Future Expansion

The architecture supports adding authentication, one-vote-per-user, comments, seasons, search, and API versioning without refactoring the core API.
