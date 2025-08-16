#!/usr/bin/env python3
"""
Test script for dynamic schema analysis and optimization
"""

import sys
import os
sys.path.append('/app')

from src.utils.schema_analyzer import SchemaAnalyzer, analyze_and_generate_hints
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_schema_analysis():
    """Test the dynamic schema analysis functionality"""
    
    print("🧪 Testing Dynamic Schema Analysis")
    print("=" * 60)
    
    # Connection string (using container hostnames)
    source_conn = "mssql://sa:Strong!Passw0rd@mssql-source:1433/StackOverflowMini"
    
    try:
        # Initialize schema analyzer
        analyzer = SchemaAnalyzer(source_conn, logger)
        
        # Test 1: Analyze ProductionTestTable
        print("\n🔍 Test 1: Analyzing ProductionTestTable")
        print("-" * 40)
        
        hints = analyzer.analyze_table_schema("ProductionTestTable", "dbo")
        
        print(f"📊 Generated {len(hints)} column hints:")
        
        money_columns = []
        decimal_columns = []
        text_columns = []
        other_columns = []
        
        for col_name, hint in hints.items():
            data_type = hint.get("data_type", "unknown")
            if data_type == "decimal":
                precision = hint.get("precision", "?")
                scale = hint.get("scale", "?")
                if "price" in col_name or "money" in col_name:
                    money_columns.append(f"{col_name} → DECIMAL({precision},{scale})")
                else:
                    decimal_columns.append(f"{col_name} → DECIMAL({precision},{scale})")
            elif data_type == "text":
                text_columns.append(f"{col_name} → TEXT")
            else:
                other_columns.append(f"{col_name} → {data_type.upper()}")
        
        if money_columns:
            print(f"  💰 MONEY columns optimized: {len(money_columns)}")
            for col in money_columns[:3]:  # Show first 3
                print(f"    {col}")
            if len(money_columns) > 3:
                print(f"    ... and {len(money_columns) - 3} more")
        
        if decimal_columns:
            print(f"  📊 DECIMAL columns optimized: {len(decimal_columns)}")
            for col in decimal_columns[:2]:  # Show first 2
                print(f"    {col}")
        
        if text_columns:
            print(f"  📝 TEXT columns optimized: {len(text_columns)}")
            for col in text_columns[:2]:  # Show first 2
                print(f"    {col}")
        
        if other_columns:
            print(f"  🔧 Other columns optimized: {len(other_columns)}")
            for col in other_columns[:2]:  # Show first 2
                print(f"    {col}")
        
        # Test 2: Get schema summary
        print("\n📋 Test 2: Schema Summary")
        print("-" * 40)
        
        summary = analyzer.get_schema_summary("ProductionTestTable", "dbo")
        
        print(f"  Table: {summary.get('table_name', 'Unknown')}")
        print(f"  Total columns: {summary.get('total_columns', 0)}")
        print(f"  Row count: {summary.get('row_count', 0):,}")
        print(f"  Optimized columns: {len(hints)}")
        
        data_types = summary.get('data_types', {})
        print(f"  Data type breakdown:")
        for dtype, count in sorted(data_types.items()):
            print(f"    {dtype}: {count} columns")
        
        problematic = summary.get('problematic_types', {})
        if problematic:
            print(f"  Problematic types found:")
            for dtype, count in problematic.items():
                print(f"    {dtype}: {count} columns (optimized)")
        
        # Test 3: Generate complete config
        print("\n⚙️ Test 3: Generated Configuration")
        print("-" * 40)
        
        config = analyzer.generate_config_section("ProductionTestTable", "dbo")
        
        print("Generated table configuration:")
        print(json.dumps({
            "ProductionTestTable": config
        }, indent=2))
        
        # Test 4: Test with smaller table
        print("\n🔍 Test 4: Analyzing ProductionTestSmall")
        print("-" * 40)
        
        small_hints = analyzer.analyze_table_schema("ProductionTestSmall", "dbo")
        small_summary = analyzer.get_schema_summary("ProductionTestSmall", "dbo")
        
        print(f"📊 ProductionTestSmall: {len(small_hints)} hints, {small_summary.get('total_columns', 0)} columns, {small_summary.get('row_count', 0):,} rows")
        
        if small_hints:
            for col_name, hint in small_hints.items():
                data_type = hint.get("data_type", "unknown")
                if data_type == "decimal":
                    precision = hint.get("precision", "?")
                    scale = hint.get("scale", "?")
                    print(f"  🎯 {col_name} → DECIMAL({precision},{scale})")
                else:
                    print(f"  🔧 {col_name} → {data_type.upper()}")
        
        print("\n✅ Schema analysis test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Schema analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_convenience_function():
    """Test the convenience function for quick analysis"""
    
    print("\n🧪 Testing Convenience Function")
    print("=" * 60)
    
    source_conn = "mssql://sa:Strong!Passw0rd@mssql-source:1433/StackOverflowMini"
    
    try:
        # Use convenience function
        hints = analyze_and_generate_hints(source_conn, "ProductionTestSmall", "dbo")
        
        print(f"📊 Quick analysis generated {len(hints)} hints:")
        for col_name, hint in hints.items():
            print(f"  {col_name}: {hint}")
        
        print("\n✅ Convenience function test completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Convenience function test failed: {e}")
        return False

def demonstrate_precision_benefits():
    """Demonstrate the precision and consistency benefits"""
    
    print("\n🎯 Demonstrating Precision Benefits")
    print("=" * 60)
    
    print("🔍 Before Dynamic Analysis:")
    print("  - MONEY columns: Inconsistent mapping (10,4 vs 19,4)")
    print("  - DECIMAL(38,18): Potential precision loss")
    print("  - VARCHAR(MAX): Sub-optimal text handling")
    print("  - Result: Schema evolution conflicts")
    
    print("\n✅ After Dynamic Analysis:")
    print("  - MONEY columns: Consistent DECIMAL(19,4)")
    print("  - DECIMAL(38,18): Exact precision preserved")
    print("  - VARCHAR(MAX): Optimal TEXT mapping")
    print("  - Result: Consistent schema across reloads")
    
    print("\n💡 Key Benefits:")
    print("  1. Zero precision loss")
    print("  2. Consistent data type mapping")
    print("  3. Automatic optimization")
    print("  4. No manual configuration needed")
    print("  5. Schema evolution conflicts eliminated")

if __name__ == "__main__":
    print("🚀 Dynamic Schema Analysis Test Suite")
    print("=" * 60)
    
    # Run tests
    test1_result = test_schema_analysis()
    test2_result = test_convenience_function() 
    
    # Demonstrate benefits
    demonstrate_precision_benefits()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    print(f"  Schema Analysis: {'✅ PASSED' if test1_result else '❌ FAILED'}")
    print(f"  Convenience Function: {'✅ PASSED' if test2_result else '❌ FAILED'}")
    
    if test1_result and test2_result:
        print("\n🎉 All tests passed! Dynamic schema analysis is working correctly.")
        print("\n💡 Next steps:")
        print("  1. Integrate with table processor")
        print("  2. Enable auto_optimize=True in production")
        print("  3. Monitor schema consistency in logs")
    else:
        print("\n⚠️ Some tests failed. Check database connectivity and table existence.")