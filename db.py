# db.py
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("GITHUB_TOKEN.env")

_url = os.getenv("SUPABASE_URL", "")
_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# URL이 없으면 None — 테스트에서 mock으로 교체됨
supabase: Client | None = create_client(_url, _key) if _url and _key else None
