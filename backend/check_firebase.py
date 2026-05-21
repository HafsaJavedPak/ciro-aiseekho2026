import asyncio
from backend.services.firestore_service import firestore_service

async def main():
    print("==================================================")
    print("🔥 Firebase Connection Check")
    print("==================================================")
    
    if not firestore_service._available:
        print("❌ Firebase is NOT connected. The system is using the mock fallback.")
        return
    
    print("✅ Firebase is successfully connected!\n")
    
    print("Fetching active incidents directly from Firebase...")
    incidents = await firestore_service.get_active_incidents()
    
    if not incidents:
        print("No active incidents found in Firebase.")
    else:
        print(f"Found {len(incidents)} active incidents:")
        for inc in incidents:
            print(f"  - ID: {inc.get('incident_id')}")
            print(f"    Type: {inc.get('classification', {}).get('crisis_type')}")
            print(f"    Status: {inc.get('status')}")
            print(f"    Updated At: {inc.get('updated_at')}")
            print()

if __name__ == "__main__":
    asyncio.run(main())
