import sys
import os
sys.path.append("python_pop_sdk")

from pop.config import ConfigFactory

def verify():
    schema_path = "specs/context_schema.yaml"
    print(f"Testing ConfigFactory.load_schema('{schema_path}')...")
    
    try:
        schema = ConfigFactory.load_schema(schema_path)
        print("✅ Load Successful!")
        print(f"   Object: {schema}")
        
        # Assertions
        assert "age" in schema.domain_fields, "FAIL: 'age' field missing in domain."
        assert schema.domain_fields["age"].type == "integer", "FAIL: 'age' type mismatch."
        print("✅ Domain Fields: OK")
        
    except Exception as e:
        print(f"❌ Load Failed: {e}")
        exit(1)

if __name__ == "__main__":
    verify()
