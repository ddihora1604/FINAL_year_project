import requests
import time
import sys

def check_metrics_endpoint():
    """Check if the metrics endpoint is accessible"""
    print("🔍 Checking metrics endpoint...")
    
    try:
        response = requests.get("http://localhost:8000/metrics", timeout=5)
        if response.status_code == 200:
            print("✅ Metrics endpoint is accessible at http://localhost:8000/metrics")
            print(f"📊 Sample metrics (first 500 chars):\n{response.text[:500]}\n")
            return True
        else:
            print(f"❌ Metrics endpoint returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to http://localhost:8000/metrics")
        print("   Make sure the RAG pipeline is running with monitoring enabled")
        return False
    except Exception as e:
        print(f"❌ Error checking metrics: {e}")
        return False

def check_prometheus():
    """Check if Prometheus is accessible"""
    print("\n🔍 Checking Prometheus...")
    
    try:
        response = requests.get("http://localhost:9090/-/healthy", timeout=5)
        if response.status_code == 200:
            print("✅ Prometheus is running at http://localhost:9090")
            return True
        else:
            print(f"❌ Prometheus returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Prometheus at http://localhost:9090")
        print("   Run: docker-compose up -d")
        return False
    except Exception as e:
        print(f"❌ Error checking Prometheus: {e}")
        return False

def check_prometheus_targets():
    """Check Prometheus targets"""
    print("\n🔍 Checking Prometheus targets...")
    
    try:
        response = requests.get("http://localhost:9090/api/v1/targets", timeout=5)
        if response.status_code == 200:
            data = response.json()
            active_targets = data.get('data', {}).get('activeTargets', [])
            
            if not active_targets:
                print("❌ No active targets found in Prometheus")
                return False
            
            for target in active_targets:
                state = target.get('health', 'unknown')
                labels = target.get('labels', {})
                job = labels.get('job', 'unknown')
                last_error = target.get('lastError', 'none')
                
                if state == 'up':
                    print(f"✅ Target '{job}' is UP")
                else:
                    print(f"❌ Target '{job}' is {state.upper()}")
                    if last_error != 'none':
                        print(f"   Error: {last_error}")
            
            return True
        else:
            print(f"❌ Failed to get targets: status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking targets: {e}")
        return False

def check_grafana():
    """Check if Grafana is accessible"""
    print("\n🔍 Checking Grafana...")
    
    try:
        response = requests.get("http://localhost:3000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Grafana is running at http://localhost:3000")
            return True
        else:
            print(f"❌ Grafana returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Grafana at http://localhost:3000")
        print("   Run: docker-compose up -d")
        return False
    except Exception as e:
        print(f"❌ Error checking Grafana: {e}")
        return False

def test_metric_generation():
    """Test if metrics are being generated"""
    print("\n🔍 Testing metric generation...")
    print("   (This requires the RAG pipeline to be running)")
    
    try:
        response1 = requests.get("http://localhost:8000/metrics", timeout=5)
        if response1.status_code != 200:
            print("❌ Cannot access metrics endpoint")
            return False
        
        initial_metrics = response1.text
        
        print("   Waiting 6 seconds for new metrics...")
        time.sleep(6)
        
        response2 = requests.get("http://localhost:8000/metrics", timeout=5)
        if response2.status_code != 200:
            print("❌ Cannot access metrics endpoint")
            return False
        
        updated_metrics = response2.text
        
        if initial_metrics != updated_metrics:
            print("✅ Metrics are being updated")
            return True
        else:
            print("⚠️  Metrics exist but may not be updating (run some queries)")
            return True
            
    except Exception as e:
        print(f"❌ Error testing metrics: {e}")
        return False

def main():
    print("=" * 60)
    print("RAG Pipeline Monitoring Setup Verification")
    print("=" * 60)
    
    checks = [
        ("Metrics Endpoint", check_metrics_endpoint),
        ("Prometheus", check_prometheus),
        ("Prometheus Targets", check_prometheus_targets),
        ("Grafana", check_grafana),
        ("Metric Generation", test_metric_generation),
    ]
    
    results = {}
    for name, check_func in checks:
        results[name] = check_func()
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    all_passed = True
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("✅ All checks passed! Your monitoring setup is working.")
        print("\nNext steps:")
        print("1. Open Grafana: http://localhost:3000 (admin/admin)")
        print("2. Add Prometheus datasource: http://prometheus:9090")
        print("3. Create dashboards using the metrics")
    else:
        print("❌ Some checks failed. See errors above.")
        print("\nTroubleshooting steps:")
        if not results.get("Metrics Endpoint"):
            print("• Start the RAG pipeline: python rag_pipeline_secure.py")
        if not results.get("Prometheus"):
            print("• Start Docker containers: docker-compose up -d")
        if not results.get("Prometheus Targets"):
            print("• Check prometheus.yml configuration")
            print("• On Windows Docker Desktop, ensure 'host.docker.internal' is used")
        if not results.get("Grafana"):
            print("• Restart Docker containers: docker-compose restart")
    
    print("=" * 60)
    
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
