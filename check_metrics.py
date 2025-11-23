"""
Diagnostic script to check if metrics are properly exposed and queryable
"""

import requests
import json

print("🔍 RAG Pipeline Metrics Diagnostic Tool\n")
print("=" * 70)

# Step 1: Check metrics endpoint
print("\n1️⃣  Checking Metrics Endpoint (http://localhost:8000/metrics)...")
print("-" * 70)

try:
    response = requests.get("http://localhost:8000/metrics", timeout=5)
    if response.status_code == 200:
        print("✅ Metrics endpoint is accessible")
        
        metrics_text = response.text
        lines = metrics_text.split('\n')
        
        # Count metrics
        metric_lines = [l for l in lines if l and not l.startswith('#')]
        print(f"📊 Total metric samples: {len(metric_lines)}")
        
        # Check for rag_ metrics
        rag_metrics = [l for l in metric_lines if l.startswith('rag_')]
        print(f"📊 RAG-specific metrics: {len(rag_metrics)}")
        
        # Display query metrics with labels
        print("\n📈 Query Metrics by Status:")
        for line in rag_metrics:
            if 'rag_queries_total' in line:
                print(f"   {line}")
        
        # Display attack metrics
        print("\n🔒 Security Attack Metrics:")
        for line in rag_metrics:
            if 'rag_security_attacks_total' in line:
                print(f"   {line}")
        
        # Display PII metrics
        print("\n🔐 PII Redaction Metrics:")
        pii_count = 0
        for line in rag_metrics:
            if 'rag_security_pii_redacted_total' in line:
                print(f"   {line}")
                pii_count += 1
        if pii_count == 0:
            print("   ⚠️  No PII metrics found")
        
    else:
        print(f"❌ Metrics endpoint returned status {response.status_code}")
        print("   Make sure your application is running on port 8000")
        
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to http://localhost:8000")
    print("   Is your RAG application with instrumentation running?")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Step 2: Check Prometheus
print("\n2️⃣  Checking Prometheus (http://localhost:9090)...")
print("-" * 70)

try:
    response = requests.get("http://localhost:9090/api/v1/targets", timeout=5)
    if response.status_code == 200:
        print("✅ Prometheus API is accessible")
        
        data = response.json()
        if data['status'] == 'success':
            active_targets = data['data']['activeTargets']
            print(f"📊 Active targets: {len(active_targets)}")
            
            # Find our app target
            for target in active_targets:
                if '8000' in target['scrapeUrl']:
                    health = target['health']
                    last_scrape = target.get('lastScrape', 'N/A')
                    print(f"\n   Target: {target['scrapeUrl']}")
                    print(f"   Health: {health}")
                    print(f"   Last Scrape: {last_scrape}")
                    
                    if health != 'up':
                        print(f"   ⚠️  Target is {health} - Prometheus cannot scrape metrics!")
                        if 'lastError' in target:
                            print(f"   Error: {target['lastError']}")
    else:
        print(f"⚠️  Prometheus API returned status {response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to Prometheus at http://localhost:9090")
    print("   Is Prometheus running?")
except Exception as e:
    print(f"⚠️  Error checking Prometheus: {e}")

# Step 3: Test PromQL queries
print("\n3️⃣  Testing PromQL Queries...")
print("-" * 70)

queries = {
    "Total Queries": 'sum(rag_queries_total)',
    "Success Queries": 'sum(rag_queries_total{status="success"})',
    "Blocked Queries": 'sum(rag_queries_total{status="blocked"})',
    "No Context Queries": 'sum(rag_queries_total{status="no_context"})',
    "Total Attacks": 'sum(rag_security_attacks_total)',
    "Success Rate": 'sum(increase(rag_queries_total{status="success"}[5m])) / sum(increase(rag_queries_total[5m])) * 100'
}

try:
    for name, query in queries.items():
        response = requests.get(
            "http://localhost:9090/api/v1/query",
            params={"query": query},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                result = data['data']['result']
                if result:
                    value = result[0]['value'][1]
                    print(f"✅ {name}: {value}")
                else:
                    print(f"❌ {name}: No data")
            else:
                print(f"❌ {name}: Query failed")
        else:
            print(f"❌ {name}: HTTP {response.status_code}")
            
except Exception as e:
    print(f"❌ Error testing queries: {e}")

# Step 4: Recommendations
print("\n4️⃣  Recommendations:")
print("-" * 70)

print("""
If metrics are not showing in Grafana:

1. ✅ Metrics Endpoint Working?
   → Run: curl http://localhost:8000/metrics | grep rag_queries_total
   
2. ✅ Prometheus Scraping?
   → Check: http://localhost:9090/targets
   → Target should show "UP"
   
3. ✅ Data in Prometheus?
   → Test query: http://localhost:9090/graph
   → Enter: rag_queries_total
   
4. ✅ Grafana Time Range?
   → Set to "Last 5 minutes" or "Last 15 minutes"
   → Click refresh button
   
5. ✅ Grafana Data Source?
   → Configuration → Data Sources → Prometheus
   → Click "Save & Test" (should be green)

For empty pie chart / blocked vs allowed:
   → These queries need data with specific labels
   → Run test_metrics.py again to generate more data
   → Wait 15-30 seconds for Prometheus to scrape
   → Refresh Grafana dashboard
""")

print("=" * 70)
print("✨ Diagnostic complete!\n")
