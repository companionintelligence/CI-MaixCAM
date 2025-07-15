#!/usr/bin/env python3
"""
Simple AI Engine Test
Test if the AI engine can be imported and initialized without errors

Author: Companion Intelligence  
Date: July 14, 2025
"""

def test_ai_engine_import():
    """Test if AI engine can be imported"""
    print("Testing AI engine import...")
    
    try:
        from ai_engine.ai_engine import AIEngine
        print("✅ AI Engine imported successfully")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in AI engine: {e}")
        return False
    except IndentationError as e:
        print(f"❌ Indentation error in AI engine: {e}")
        return False
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Other error: {e}")
        return False

def test_ai_engine_init():
    """Test if AI engine can be initialized"""
    print("Testing AI engine initialization...")
    
    try:
        from ai_engine.ai_engine import AIEngine
        from utils.config import Config
        
        config = Config()
        ai_engine = AIEngine(config)
        
        print(f"✅ AI Engine initialized with {len(ai_engine.get_active_models())} active models")
        return True
    except Exception as e:
        print(f"❌ AI Engine initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🤖 AI Engine Test Script")
    print("=" * 40)
    
    # Test import first
    if not test_ai_engine_import():
        print("\n❌ Cannot proceed - fix import errors first")
        return False
    
    print()
    
    # Test initialization
    if not test_ai_engine_init():
        print("\n❌ Initialization failed")
        return False
    
    print("\n✅ All AI engine tests passed!")
    return True

if __name__ == "__main__":
    main()
