import asyncio
import httpx
import time
import random

API_BASE = "http://127.0.0.1:8000"
TOTAL_SIGNALS = 150
CONCURRENCY_LIMIT = 50

async def send_signal(client, semaphore, i):
    async with semaphore:
        lat = 33.6844 + random.uniform(-0.05, 0.05)
        lng = 73.0479 + random.uniform(-0.05, 0.05)
        
        signal = {
            "source_type": "sensor",
            "source_name": f"StressTester_{i}",
            "raw_content": f"Automated stress test signal {i}: Potential anomaly detected.",
            "location": {"lat": lat, "lng": lng, "area_name": "Stress Test Sector", "precision": "low"},
            "timestamp": "2026-05-20T10:00:00Z"
        }
        
        start_time = time.time()
        try:
            response = await client.post(f"{API_BASE}/signals/ingest", json=signal)
            duration = time.time() - start_time
            return response.status_code, duration
        except Exception as e:
            return 500, time.time() - start_time

async def run_stress_test():
    print("==================================================")
    print("🔥 CIRO Concurrency Stress Test")
    print(f"   Target: {TOTAL_SIGNALS} signals")
    print(f"   Concurrency: {CONCURRENCY_LIMIT} concurrent requests")
    print("==================================================")
    
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        start_time = time.time()
        
        tasks = [send_signal(client, semaphore, i) for i in range(TOTAL_SIGNALS)]
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        successes = sum(1 for status, _ in results if status in (200, 202))
        failures = TOTAL_SIGNALS - successes
        avg_time = sum(duration for _, duration in results) / TOTAL_SIGNALS
        
        print("\n📊 STRESS TEST RESULTS:")
        print(f"   Total Time: {total_time:.2f} seconds")
        print(f"   Requests/sec: {TOTAL_SIGNALS / total_time:.2f}")
        print(f"   Successful Ingests: {successes}/{TOTAL_SIGNALS}")
        print(f"   Failed Ingests: {failures}/{TOTAL_SIGNALS}")
        print(f"   Average Latency: {avg_time:.3f} seconds")
        
        if failures > 0:
            print("   ⚠️ WARNING: API dropped requests. Consider scaling FastAPI workers or tuning BackgroundTasks.")
        else:
            print("   ✅ SUCCESS: FastAPI gracefully queued all incoming signals!")
            print("   Note: LangGraph is currently processing these in the background.")
            print("   Monitor Firebase to ensure all signals merge into incidents.")

if __name__ == "__main__":
    asyncio.run(run_stress_test())
