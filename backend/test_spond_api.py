"""
Quick diagnostic script to test Spond API connection
"""
import asyncio
from spond.spond import Spond


async def main():
    # Initialize Spond client
    client = Spond(
        username="lillehammer@bueklubb.no",
        password="bz*2gVTJqD9Y5W"
    )

    try:
        print("=" * 60)
        print("SPOND API DIAGNOSTIC TEST")
        print("=" * 60)

        # Test 1: Fetch groups
        print("\n1. Fetching groups...")
        groups = await client.get_groups()
        print(f"   Found {len(groups)} groups:")
        for i, group in enumerate(groups[:5], 1):  # Show first 5
            print(f"   {i}. {group.get('name', 'N/A')} (ID: {group.get('id', 'N/A')})")
        if len(groups) > 5:
            print(f"   ... and {len(groups) - 5} more")

        # Test 2: Fetch events (default parameters)
        print("\n2. Fetching events (default parameters)...")
        events = await client.get_events(max_events=100)
        print(f"   Found {len(events)} events:")
        for i, event in enumerate(events[:5], 1):  # Show first 5
            print(f"   {i}. {event.get('heading', 'N/A')} - {event.get('startTimestamp', 'N/A')}")
        if len(events) > 5:
            print(f"   ... and {len(events) - 5} more")

        # Test 3: Check if there are any events in specific groups
        if groups:
            print("\n3. Checking events in first group (with all filters)...")
            first_group_id = groups[0].get('id')
            group_events = await client.get_events(
                group_id=first_group_id,
                include_hidden=True,
                include_scheduled=True,
                max_events=100
            )
            print(f"   Found {len(group_events)} events in group '{groups[0].get('name')}':")
            for i, event in enumerate(group_events[:10], 1):  # Show first 10
                heading = event.get('heading', 'N/A')
                start = event.get('startTimestamp', 'N/A')
                hidden = event.get('hidden', False)
                cancelled = event.get('cancelled', False)
                print(f"   {i}. {heading} - {start} (hidden: {hidden}, cancelled: {cancelled})")
            if len(group_events) > 10:
                print(f"   ... and {len(group_events) - 10} more")

            # Show some event details
            if group_events:
                print("\n4. Sample event details:")
                sample = group_events[0]
                print(f"   Heading: {sample.get('heading')}")
                print(f"   Start: {sample.get('startTimestamp')}")
                print(f"   End: {sample.get('endTimestamp')}")
                print(f"   Description: {sample.get('description', 'N/A')[:100]}")
                print(f"   Event type: {sample.get('type', 'N/A')}")
                print(f"   Responses count: {len(sample.get('responses', {}).get('acceptedIds', []))}")

    finally:
        # Close the session
        if client.clientsession:
            await client.clientsession.close()

    print("\n" + "=" * 60)
    print("DIAGNOSTIC TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
