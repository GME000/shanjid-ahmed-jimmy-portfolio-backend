# DevFolio Backend

Django REST Framework backend for Shanjid Ahmed Jimmy's portfolio and blog. Blog content is stored as plain text (Markdown can be rendered by the frontend). The owner is the authenticated superuser; there is deliberately no registration endpoint.

## Run
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo
python manage.py runserver
```

API base: `/api/`. JWT login is `/api/auth/login/`; media URLs are serialized as absolute URLs. Public post detail view counting uses `X-Visitor-Id` and a five-minute cache cooldown, with an atomic `F()` update, so refreshes do not double count. Pagination is 6 posts, 9 projects, and 10 comments/messages.

Frontend repository: https://github.com/GME000/shanjid-ahmed-jimmy-portfolio-frontend
Backend repository: https://github.com/GME000/shanjid-ahmed-jimmy-portfolio-backend

The local `media/` directory contains the portfolio avatar and resume. It is excluded by the default `.gitignore` for production safety; upload equivalent media through Django Admin or your deployment's media storage.
