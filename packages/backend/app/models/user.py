"""Re-export Django auth user (`app.accounts.models.User`) — see checklist Step 2.3."""

from app.accounts.models import User

__all__ = ["User"]
