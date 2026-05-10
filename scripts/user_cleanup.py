"""
User cleanup script.

Run with: flask shell < scripts/user_cleanup.py

Or interactively in flask shell:
    exec(open('scripts/user_cleanup.py').read())

Steps:
  1. Run with DRY_RUN = True to review what will be deleted.
  2. Set DRY_RUN = False to perform the actual cleanup.
"""

from sqlalchemy import func

from mywhiskies.extensions import db
from mywhiskies.models import User, UserLogin
from mywhiskies.services.user.user import delete_user_account

DRY_RUN = False

# Users being contacted by email — do not delete
KEEP_USERNAMES = {"JMSTURM", "mattmccormick", "Bourbon_ThatsNeat"}

# ── Tracked users (have login history) + bottle counts ────────────────────────
print("\n=== Users with login history ===")
tracked = (
    db.session.execute(db.select(User).where(User.id.in_(db.select(UserLogin.user_id).distinct()))).scalars().all()
)

for u in sorted(tracked, key=lambda u: len(u.bottles), reverse=True):
    last = db.session.execute(db.select(func.max(UserLogin.login_date)).where(UserLogin.user_id == u.id)).scalar()
    print(f"  {u.username:<30} {len(u.bottles):>4} bottles  last login: {last}")

# ── Inactive users (no login history, not in keep list) ───────────────────────
print("\n=== Inactive users to be deleted ===")
inactive = (
    db.session.execute(
        db.select(User).where(
            User.id.notin_(db.select(UserLogin.user_id).distinct()),
            User.username.notin_(KEEP_USERNAMES),
        )
    )
    .scalars()
    .all()
)

for u in sorted(inactive, key=lambda u: len(u.bottles), reverse=True):
    print(f"  {u.username:<30} {len(u.bottles):>4} bottles")

print(f"\nTotal to delete: {len(inactive)}")

if DRY_RUN:
    print("\nDRY RUN — no deletions performed. Set DRY_RUN = False to proceed.")
else:
    print("\nDeleting...")
    for u in inactive:
        print(f"  Deleting {u.username}...")
        delete_user_account(u)
    print("Done.")
