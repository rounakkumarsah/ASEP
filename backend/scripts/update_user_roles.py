"""
Script to update user records in Neon PostgreSQL using SQLAlchemyUnitOfWork.
Ensures rounakkrsah429@gmail.com and rounakkumar4294@gmail.com have role='user',
account_type='individual', current_plan='free', monthly_token_quota=100000,
active and verified.
"""

import asyncio
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from src.auth.utils import normalize_email
from src.db.models.user import User
from src.unit_of_work.sqlalchemy import SQLAlchemyUnitOfWork


async def main():
    target_emails = [
        "rounakkrsah429@gmail.com",
        "rounakkumar4294@gmail.com",
        "rounak.kr.sah429@gmail.com",
    ]
    normalized_targets = {normalize_email(e) for e in target_emails}
    print(f"Target normalized emails: {normalized_targets}")

    async with SQLAlchemyUnitOfWork() as uow:
        # Fetch all users
        result = await uow._session.execute(select(User))
        all_users = result.scalars().all()
        print(f"Total users found in database: {len(all_users)}")

        for user in all_users:
            print(f"User: id={user.id}, username='{user.username}', email='{user.email}', role='{user.role}', status='{user.status}', active={user.is_active}, verified={user.email_verified}")

        matched_users = []
        for user in all_users:
            norm = normalize_email(user.email)
            if norm in normalized_targets or "rounak" in user.username.lower():
                print(f"Updating user: {user.username} ({user.email})...")
                user.role = "user"
                user.account_type = "individual"
                user.current_plan = "free"
                user.monthly_token_quota = 100000
                user.is_active = True
                user.email_verified = True
                user.status = "active"
                matched_users.append(user)

        if matched_users:
            await uow.commit()
            print(f"Successfully committed updates for {len(matched_users)} user(s):")
            for u in matched_users:
                print(f"  - id={u.id}, username={u.username}, email={u.email}, role={u.role}, plan={u.current_plan}, quota={u.monthly_token_quota}")
        else:
            print("No matching users found to update!")


if __name__ == "__main__":
    asyncio.run(main())
