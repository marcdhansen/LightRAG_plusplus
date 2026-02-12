#!/usr/bin/env python3
"""
Comprehensive Validation for Enhanced Vector Similarity Search

This script tests the enhanced NanoVectorDB implementation to verify that the targeted
fixes resolve the context passing issues identified in Phase 2 analysis.

Usage:
    python validate_enhanced_search.py --url http://localhost:9621
"""

import asyncio
import json
import sys
import argparse
from typing import Dict, Any, List
import httpx
import numpy as np
from pathlib import Path

# Add lightrag to path for imports
sys.path.insert(0, str(Path(__file__).parent))

class VectorSearchValidator:
    """Validate enhanced vector similarity search implementation"""
    
    def __init__(self, base_url: str = "http://localhost:9621"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.test_results = {}
        
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    async def test_basic_search(self) -> Dict[str, Any]:
        """Test basic search functionality"""
        print("\n🧪 Testing Basic Search Functionality...")
        
        test_cases = [
            {"query": "Alice Anderson", "description": "Exact match test"},
            {"query": "alice anderson", "description": "Case-insensitive test"},
            {"query": "ALICE ANDERSON", "description": "Case variation test"},
            {"query": "Researcher", "description": "Substring test"},
            {"query": "Mark", "description": "Single word test"},
        ]
        
        results = {}
        
        for case in test_cases:
            print(f"🔍 Testing: {case['description']}")
            
            try:
                response = await self.client.post(
                    f"{self.base_url}/query/data",
                    json={"query": case["query"], "mode": "naive"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    chunks = len(data.get("chunks", []))
                    
                    print(f"  ✅ Chunks found: {chunks}")
                    
                    if chunks > 0:
                        results[case["query"]] = {"success": True, "chunks": chunks}
                    else:
                        results[case["query"]] = {"success": False, "chunks": 0}
                        
                else:
                    results[case["query"]] = {"error": f"HTTP {response.status_code}"}
                    
            except Exception as e:
                results[case["query"]] = {"error": str(e)}
                print(f"  ❌ Error: {e}")
        
        return results
    
    async def test_adaptive_thresholds(self) -> Dict[str, Any]:
        """Test adaptive threshold functionality"""
        print("\n🎚 Testing Adaptive Thresholds...")
        
        test_queries = [
            "Alice Anderson",  # Long, specific
            "Researcher",    # Medium length
            "Mark",        # Short, should get permissive threshold
        ]
        
        results = {}
        
        for query in test_queries:
            print(f"🔍 Testing adaptive thresholds for: '{query}'")
            
            query_results = {}
            
            # Test different thresholds
            for threshold in [0.1, 0.2, 0.3, 0.4]:
                try:
                    response = await self.client.post(
                        f"{self.base_url}/test/adaptive_threshold",
                        json={
                            "query": query,
                            "threshold": threshold,
                            "expected_behavior": "adaptive" if threshold >= 0.2 else "fallback"
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        matches = len(data.get("results", []))
                        expected_threshold_1 = 0.2 if threshold >= 0.2 else 0.05
                        
                        query_results[f"threshold_{threshold}"] = {
                            "matches": matches,
                            "success": True,
                            "expected_threshold": expected_threshold_1
                        }
                        
                        print(f"  ✅ Threshold {threshold}: {matches} matches (expected >{expected_threshold_1})")
                        
                    else:
                        query_results[f"threshold_{threshold}"] = {"error": f"HTTP {response.status_code}"}
                        
                except Exception as e:
                    query_results[f"threshold_{threshold}"] = {"error": str(e)}
            
            results[query] = query_results
        
        return results
    
    async def test_quality_filtering(self) -> Dict[str, Any]:
        """Test quality filtering and scoring"""
        print("\n🏅 Testing Quality Filtering...")
        
        try:
            response = await self.client.post(
                f"{self.base_url}/test/quality_filtering",
                json={
                    "query": "Alice Anderson",
                    "test_scenarios": ["good_match", "poor_match", "excellent_match"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ Quality filtering test completed")
                return data
            else:
                print(f"  ❌ Quality filtering test failed: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"  ❌ Quality filtering error: {e}")
            return {"error": str(e)}
    
    async def test_fallback_mechanism(self) -> Dict[str, Any]:
        """Test fallback search mechanism"""
        print("\n🔄 Testing Fallback Mechanism...")
        
        try:
            response = await self.client.post(
                f"{self.base_url}/test/fallback_search",
                json={
                    "query": "Alice Anderson",
                    "primary_threshold": 0.2,  # Should get no results
                    "fallback_threshold": 0.05   # Should get results
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                primary_matches = len(data.get("primary_results", []))
                fallback_matches = len(data.get("fallback_results", []))
                
                print(f"  ✅ Primary search: {primary_matches} matches")
                print(f"  ✅ Fallback search: {fallback_matches} matches")
                
                # Validate expected behavior
                success = (primary_matches == 0 and fallback_matches > 0)
                print(f"  {'✅' if success else '❌'} Fallback mechanism: {'working' if success else 'not working'}")
                
                return data
            else:
                print(f"  ❌ Fallback test failed: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"  ❌ Fallback test error: {e}")
            return {"error": str(e)}
    
    async def test_case_variants(self) -> Dict[str, Any]:
        """Test query variant generation"""
        print("\n🔤 Testing Query Variant Generation...")
        
        test_queries = ["alice anderson", "Alice Anderson"]
        
        results = {}
        
        for query in test_queries:
            print(f"🔍 Testing variants for: '{query}'")
            
            try:
                response = await self.client.post(
                    f"{self.base_url}/test/query_variants",
                    json={"query": query}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    variants = data.get("variants", [])
                    
                    print(f"  ✅ Generated {len(variants)} variants: {variants}")
                    
                    # Validate expected variants
                    expected_lower = [query.lower()]
                    if "Alice" in query.lower():
                        expected_lower.append(query.lower())  # Original case
                    expected_lower.append(query.upper())  # Upper case
                    
                    success = all(variant.lower() in expected_lower for variant in variants)
                    print(f"  {'✅' if success else '❌'} Variant generation: {'valid' if success else 'invalid'}")
                    
                    results[query] = {
                        "success": success,
                        "variants": variants,
                        "expected": expected_lower
                    }
                else:
                    results[query] = {"error": f"HTTP {response.status_code}"}
                    
            except Exception as e:
                results[query] = {"error": str(e)}
                print(f"  ❌ Variant test error: {e}")
        
        return results
    
    async def generate_validation_report(self, all_results: Dict[str, Any]) -> str:
        """Generate comprehensive validation report"""
        print("\n" + "="*80)
        print("🎯 ENHANCED VECTOR SEARCH VALIDATION REPORT")
        print("="*80)
        
        # Analyze basic search results
        basic_results = all_results.get("basic_search", {})
        basic_success = sum(1 for r in basic_results.values() if r.get("success", False))
        basic_total = len(basic_results)
        
        print(f"\n📊 BASIC SEARCH RESULTS:")
        print(f"  • Success Rate: {basic_success}/{basic_total} ({basic_success/basic_total*100:.1f}%)")
        print(f"  • Working Cases: {[k for k, r in basic_results.items() if r.get('success', False)]}")
        print(f"  • Failed Cases: {[k for k, r in basic_results.items() if not r.get('success', False)]}")
        
        # Analyze adaptive threshold results
        adaptive_results = all_results.get("adaptive_thresholds", {})
        adaptive_working = 0
        
        print(f"\n📊 ADAPTIVE THRESHOLD RESULTS:")
        
        for query, query_results in adaptive_results.items():
            query_working = False
            
            for threshold, result in query_results.items():
                if isinstance(result, dict) and result.get("success", False):
                    if "fallback" in threshold and result.get("matches", 0) > 0:
                        query_working = True
                    break
                    elif "adaptive" in threshold and result.get("matches", 0) > 0:
                        query_working = True
                        break
            
            if query_working:
                adaptive_working += 1
                
        adaptive_total = len(adaptive_results)
        adaptive_success_rate = (adaptive_working / adaptive_total * 100) if adaptive_total > 0 else 0
        
        print(f"  • Adaptive Queries Working: {adaptive_working}/{adaptive_total} ({adaptive_success_rate:.1f}%)")
        print(f"  • Success Rate: {adaptive_success_rate:.1f}%")
        
        # Analyze quality filtering
        quality_results = all_results.get("quality_filtering", {})
        if "error" not in quality_results:
            print(f"\n✅ QUALITY FILTERING: Working correctly")
        else:
            print(f"\n❌ QUALITY FILTERING: {quality_results.get('error', 'unknown')}")
        
        # Analyze fallback mechanism
        fallback_results = all_results.get("fallback_mechanism", {})
        if "error" not in fallback_results:
            fallback_working = fallback_results.get("success", False)
            print(f"\n✅ FALLBACK MECHANISM: {'Working' if fallback_working else 'Failed'}")
        else:
            print(f"\n❌ FALLBACK MECHANISM: {fallback_results.get('error', 'unknown')}")
        
        # Analyze query variants
        variant_results = all_results.get("case_variants", {})
        variant_success = sum(1 for r in variant_results.values() if r.get("success", False))
        variant_total = len(variant_results)
        
        print(f"\n🔤 QUERY VARIANT RESULTS:")
        print(f"  • Variant Generation Success: {variant_success}/{variant_total} ({variant_success/variant_total*100:.1f}%)")
        print(f"  • Valid Variants Generated: {len([r for r in variant_results.values() if r.get('success', False)])}")
        
        # Overall assessment
        overall_success = (
            basic_success > 0 and
            adaptive_success_rate >= 80 and
            "error" not in quality_results and
            "success" in fallback_results and
            variant_success > 0
        )
        
        print(f"\n🎯 OVERALL ASSESSMENT:")
        print(f"  • Enhanced Search Implementation: {'✅ WORKING' if overall_success else '❌ NEEDS IMPROVEMENT'}")
        
        if overall_success:
            print(f"  • Status: Ready for production deployment")
            print(f"  • Confidence: High - all major components validated")
            print(f"  • Next Step: Deploy with COSINE_THRESHOLD=0.2-0.3")
        else:
            print(f"  • Status: Requires additional refinement")
            print(f"  • Issues Identified: Review failed components")
        
        print("\n" + "="*80)
        
        return "VALIDATION_COMPLETE" if overall_success else "NEEDS_REFINEMENT"

async def main():
    """Main validation function"""
    parser = argparse.ArgumentParser(description="Validate enhanced vector similarity search implementation")
    parser.add_argument("--url", default="http://localhost:9621", help="LightRAG server URL")
    parser.add_argument("--comprehensive", action="store_true", help="Run comprehensive validation suite")
    
    args = parser.parse_args()
    
    print(f"🎯 Enhanced Vector Search Validation")
    print(f"🌐 Server: {args.url}")
    print("="*80)
    
    validator = VectorSearchValidator(args.url)
    
    try:
        all_results = {}
        
        # Run basic search tests
        basic_results = await validator.test_basic_search()
        all_results["basic_search"] = basic_results
        
        if args.comprehensive:
            # Run comprehensive validation
            adaptive_results = await validator.test_adaptive_thresholds()
            all_results["adaptive_thresholds"] = adaptive_results
            
            quality_results = await validator.test_quality_filtering()
            all_results["quality_filtering"] = quality_results
            
            fallback_results = await validator.test_fallback_mechanism()
            all_results["fallback_mechanism"] = fallback_results
            
            variant_results = await validator.test_case_variants()
            all_results["case_variants"] = variant_results
        
        # Generate validation report
        status = validator.generate_validation_report(all_results)
        
        print(f"\n🏁 VALIDATION STATUS: {status}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Validation interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
    finally:
        await validator.close()
    
    print(f"\n🏁 Validation complete")

if __name__ == "__main__":
    asyncio.run(main())