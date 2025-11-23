"""
Diagnostic script to check available imports from rag_pipeline_secure
"""

import sys
from pathlib import Path

# Add RAG pipeline to path
sys.path.append(str(Path(__file__).parent / "RAG-Pipeline-Ollama"))

try:
    import rag_pipeline_secure
    
    print("✅ Successfully imported rag_pipeline_secure module")
    print("\n📋 Available classes and functions:")
    print("-" * 50)
    
    for item in dir(rag_pipeline_secure):
        if not item.startswith('_'):
            obj = getattr(rag_pipeline_secure, item)
            obj_type = type(obj).__name__
            print(f"  • {item} ({obj_type})")
    
    print("\n" + "=" * 50)
    print("Please update the imports in streamlit_app_advanced.py")
    print("to use the correct class names shown above.")
    
except ImportError as e:
    print(f"❌ Failed to import: {e}")
    print("\n🔍 Checking file existence:")
    
    rag_file = Path(__file__).parent / "RAG-Pipeline-Ollama" / "rag_pipeline_secure.py"
    if rag_file.exists():
        print(f"  ✅ File exists: {rag_file}")
    else:
        print(f"  ❌ File not found: {rag_file}")
