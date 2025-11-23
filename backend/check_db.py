"""
Quick script to check database contents
"""
import asyncio
from sqlalchemy import select, func
from app.db.session import AsyncSessionLocal
from app.models.event import Event
from app.models.group import Group
from app.models.member import Member

async def check_data():
    async with AsyncSessionLocal() as session:
        # Count events
        result = await session.execute(select(func.count(Event.id)))
        event_count = result.scalar()
        print(f'Events in database: {event_count}')

        # Count groups
        result = await session.execute(select(func.count(Group.id)))
        group_count = result.scalar()
        print(f'Groups in database: {group_count}')

        # Count members
        result = await session.execute(select(func.count(Member.id)))
        member_count = result.scalar()
        print(f'Members in database: {member_count}')

        if event_count > 0:
            # Show a sample event
            result = await session.execute(select(Event).limit(1))
            event = result.scalar_one_or_none()
            if event:
                print(f'\nSample event:')
                print(f'  ID: {event.id}')
                print(f'  Heading: {event.heading}')
                print(f'  Type: {event.event_type}')
                print(f'  Start: {event.start_time}')

if __name__ == '__main__':
    asyncio.run(check_data())
