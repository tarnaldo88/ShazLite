#!/usr/bin/env python3
"""
Database optimization tools for the Audio Fingerprinting System.

This module provides tools to analyze and optimize database performance,
including query analysis, index optimization, and performance tuning.

Requirements addressed:
- 4.2: Database query optimization
- 4.5: Database performance monitoring
"""

import time
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class QueryAnalysis:
    """Container for database query analysis results."""
    query: str
    calls: int
    total_time_ms: float
    mean_time_ms: float
    min_time_ms: float
    max_time_ms: float
    rows_returned: Optional[int] = None
    rows_affected: Optional[int] = None


@dataclass
class IndexAnalysis:
    """Container for database index analysis results."""
    table_name: str
    index_name: str
    size_mb: float
    scans: int
    tuples_read: int
    tuples_fetched: int
    usage_ratio: float
    is_used: bool


class DatabaseOptimizer:
    """Main database optimization class."""
    
    def __init__(self):
        self.connection = None
    
    def get_connection(self):
        """Get database connection."""
        if not self.connection:
            from backend.database.connection import get_db_session
            self.connection = get_db_session()
        return self.connection
    
    def analyze_query_performance(self) -> List[QueryAnalysis]:
        """Analyze query performance using pg_stat_statements."""
        with self.get_connection() as session:
            # Enable pg_stat_statements if not already enabled
            session.execute("CREATE EXTENSION IF NOT EXISTS pg_stat_statements;")
            
            # Get query statistics
            query = """
            SELECT 
                query,
                calls,
                total_exec_time as total_time_ms,
                mean_exec_time as mean_time_ms,
                min_exec_time as min_time_ms,
                max_exec_time as max_time_ms,
                rows
            FROM pg_stat_statements 
            WHERE query NOT LIKE '%pg_stat_statements%'
            ORDER BY total_exec_time DESC 
            LIMIT 50;
            """
            
            result = session.execute(query)
            analyses = []
            
            for row in result:
                analysis = QueryAnalysis(
                    query=row.query,
                    calls=row.calls,
                    total_time_ms=row.total_time_ms,
                    mean_time_ms=row.mean_time_ms,
                    min_time_ms=row.min_time_ms,
                    max_time_ms=row.max_time_ms,
                    rows_returned=row.rows
                )
                analyses.append(analysis)
            
            return analyses
    
    def analyze_index_usage(self) -> List[IndexAnalysis]:
        """Analyze index usage and effectiveness."""
        with self.get_connection() as session:
            query = """
            SELECT 
                schemaname,
                tablename,
                indexname,
                pg_size_pretty(pg_relation_size(indexrelid))::text as size,
                pg_relation_size(indexrelid) / 1024.0 / 1024.0 as size_mb,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch,
                CASE 
                    WHEN idx_scan = 0 THEN 0
                    ELSE idx_tup_fetch::float / idx_tup_read::float
                END as usage_ratio
            FROM pg_stat_user_indexes 
            ORDER BY pg_relation_size(indexrelid) DESC;
            """
            
            result = session.execute(query)
            analyses = []
            
            for row in result:
                analysis = IndexAnalysis(
                    table_name=row.tablename,
                    index_name=row.indexname,
                    size_mb=row.size_mb,
                    scans=row.idx_scan,
                    tuples_read=row.idx_tup_read,
                    tuples_fetched=row.idx_tup_fetch,
                    usage_ratio=row.usage_ratio or 0,
                    is_used=row.idx_scan > 0
                )
                analyses.append(analysis)
            
            return analyses
    
    def get_table_statistics(self) -> Dict[str, Any]:
        """Get comprehensive table statistics."""
        with self.get_connection() as session:
            # Table sizes
            size_query = """
            SELECT 
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))::text as total_size,
                pg_total_relation_size(schemaname||'.'||tablename) / 1024.0 / 1024.0 as total_size_mb,
                pg_size_pretty(pg_relation_size(schemaname||'.'||tablename))::text as table_size,
                pg_relation_size(schemaname||'.'||tablename) / 1024.0 / 1024.0 as table_size_mb
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
            """
            
            size_result = session.execute(size_query)
            table_sizes = {row.tablename: {
                'total_size': row.total_size,
                'total_size_mb': row.total_size_mb,
                'table_size': row.table_size,
                'table_size_mb': row.table_size_mb
            } for row in size_result}
            
            # Row counts
            stats = {}
            for table_name in table_sizes.keys():
                try:
                    count_result = session.execute(f"SELECT COUNT(*) as count FROM {table_name};")
                    row_count = count_result.fetchone().count
                    
                    stats[table_name] = {
                        **table_sizes[table_name],
                        'row_count': row_count,
                        'avg_row_size_bytes': (table_sizes[table_name]['table_size_mb'] * 1024 * 1024) / row_count if row_count > 0 else 0
                    }
                except Exception as e:
                    stats[table_name] = {
                        **table_sizes[table_name],
                        'row_count': 0,
                        'avg_row_size_bytes': 0,
                        'error': str(e)
                    }
            
            return stats
    
    def analyze_fingerprint_query_performance(self) -> Dict[str, Any]:
        """Analyze performance of fingerprint-specific queries."""
        with self.get_connection() as session:
            analyses = {}
            
            # Test fingerprint lookup performance
            test_hashes = [12345, 67890, 11111, 22222, 33333]
            
            # Single hash lookup
            start_time = time.time()
            result = session.execute(
                "SELECT COUNT(*) FROM fingerprints WHERE hash_value = %s",
                (test_hashes[0],)
            )
            single_lookup_time = (time.time() - start_time) * 1000
            analyses['single_hash_lookup_ms'] = single_lookup_time
            
            # Multiple hash lookup
            start_time = time.time()
            result = session.execute(
                "SELECT hash_value, COUNT(*) FROM fingerprints WHERE hash_value = ANY(%s) GROUP BY hash_value",
                (test_hashes,)
            )
            multi_lookup_time = (time.time() - start_time) * 1000
            analyses['multi_hash_lookup_ms'] = multi_lookup_time
            
            # Complex matching query (similar to actual fingerprint matching)
            start_time = time.time()
            result = session.execute("""
                WITH fingerprint_matches AS (
                    SELECT 
                        f.song_id,
                        f.time_offset_ms,
                        COUNT(*) as match_count
                    FROM fingerprints f
                    WHERE f.hash_value = ANY(%s)
                    GROUP BY f.song_id, f.time_offset_ms
                    HAVING COUNT(*) >= 2
                )
                SELECT 
                    s.id,
                    s.title,
                    s.artist,
                    SUM(fm.match_count) as total_matches
                FROM fingerprint_matches fm
                JOIN songs s ON s.id = fm.song_id
                GROUP BY s.id, s.title, s.artist
                ORDER BY total_matches DESC
                LIMIT 10;
            """, (test_hashes,))
            complex_query_time = (time.time() - start_time) * 1000
            analyses['complex_matching_query_ms'] = complex_query_time
            
            return analyses
    
    def suggest_optimizations(self) -> List[Dict[str, Any]]:
        """Generate optimization suggestions based on analysis."""
        suggestions = []
        
        # Analyze query performance
        try:
            query_analyses = self.analyze_query_performance()
            
            # Find slow queries
            for analysis in query_analyses:
                if analysis.mean_time_ms > 1000:  # Queries taking more than 1 second
                    suggestions.append({
                        'type': 'slow_query',
                        'priority': 'high',
                        'issue': f'Query taking {analysis.mean_time_ms:.1f}ms on average',
                        'query': analysis.query[:100] + '...' if len(analysis.query) > 100 else analysis.query,
                        'suggestion': 'Consider adding indexes, rewriting query, or optimizing WHERE clauses'
                    })
                
                if analysis.calls > 1000 and analysis.mean_time_ms > 100:
                    suggestions.append({
                        'type': 'frequent_slow_query',
                        'priority': 'medium',
                        'issue': f'Frequently called query ({analysis.calls} times) taking {analysis.mean_time_ms:.1f}ms',
                        'query': analysis.query[:100] + '...' if len(analysis.query) > 100 else analysis.query,
                        'suggestion': 'High impact optimization target - consider caching or query optimization'
                    })
        except Exception as e:
            suggestions.append({
                'type': 'analysis_error',
                'priority': 'low',
                'issue': f'Could not analyze query performance: {e}',
                'suggestion': 'Enable pg_stat_statements extension'
            })
        
        # Analyze index usage
        try:
            index_analyses = self.analyze_index_usage()
            
            # Find unused indexes
            unused_indexes = [idx for idx in index_analyses if not idx.is_used and idx.size_mb > 1]
            for idx in unused_indexes:
                suggestions.append({
                    'type': 'unused_index',
                    'priority': 'medium',
                    'issue': f'Unused index {idx.index_name} on {idx.table_name} ({idx.size_mb:.1f}MB)',
                    'suggestion': 'Consider dropping this index to save space and improve write performance'
                })
            
            # Find inefficient indexes
            inefficient_indexes = [idx for idx in index_analyses if idx.is_used and idx.usage_ratio < 0.1 and idx.scans > 100]
            for idx in inefficient_indexes:
                suggestions.append({
                    'type': 'inefficient_index',
                    'priority': 'medium',
                    'issue': f'Index {idx.index_name} has low efficiency ({idx.usage_ratio:.2%})',
                    'suggestion': 'Review index definition and query patterns'
                })
        except Exception as e:
            suggestions.append({
                'type': 'analysis_error',
                'priority': 'low',
                'issue': f'Could not analyze index usage: {e}',
                'suggestion': 'Check database permissions and statistics'
            })
        
        # Analyze table statistics
        try:
            table_stats = self.get_table_statistics()
            
            # Check for large tables without proper indexing
            for table_name, stats in table_stats.items():
                if stats['row_count'] > 100000 and table_name == 'fingerprints':
                    # Check if we have the critical indexes
                    fingerprint_analyses = self.analyze_fingerprint_query_performance()
                    
                    if fingerprint_analyses.get('single_hash_lookup_ms', 0) > 10:
                        suggestions.append({
                            'type': 'missing_index',
                            'priority': 'high',
                            'issue': f'Slow fingerprint hash lookups ({fingerprint_analyses["single_hash_lookup_ms"]:.1f}ms)',
                            'suggestion': 'Ensure hash_value index exists and is being used'
                        })
                    
                    if fingerprint_analyses.get('complex_matching_query_ms', 0) > 100:
                        suggestions.append({
                            'type': 'slow_matching',
                            'priority': 'high',
                            'issue': f'Slow fingerprint matching queries ({fingerprint_analyses["complex_matching_query_ms"]:.1f}ms)',
                            'suggestion': 'Consider composite indexes on (hash_value, song_id, time_offset_ms)'
                        })
        except Exception as e:
            suggestions.append({
                'type': 'analysis_error',
                'priority': 'low',
                'issue': f'Could not analyze table statistics: {e}',
                'suggestion': 'Check database connectivity and permissions'
            })
        
        return suggestions
    
    def apply_optimizations(self, auto_apply: bool = False) -> List[Dict[str, Any]]:
        """Apply database optimizations."""
        applied_optimizations = []
        
        with self.get_connection() as session:
            # Update table statistics
            try:
                session.execute("ANALYZE;")
                applied_optimizations.append({
                    'type': 'statistics_update',
                    'status': 'success',
                    'description': 'Updated table statistics for query planner'
                })
            except Exception as e:
                applied_optimizations.append({
                    'type': 'statistics_update',
                    'status': 'failed',
                    'description': f'Failed to update statistics: {e}'
                })
            
            # Vacuum tables if auto_apply is enabled
            if auto_apply:
                try:
                    session.execute("VACUUM ANALYZE;")
                    applied_optimizations.append({
                        'type': 'vacuum',
                        'status': 'success',
                        'description': 'Performed VACUUM ANALYZE to reclaim space and update statistics'
                    })
                except Exception as e:
                    applied_optimizations.append({
                        'type': 'vacuum',
                        'status': 'failed',
                        'description': f'Failed to vacuum: {e}'
                    })
            
            # Check and create missing indexes
            try:
                # Ensure critical fingerprint indexes exist
                critical_indexes = [
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fingerprints_hash_optimized ON fingerprints USING btree (hash_value);",
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fingerprints_song_time_optimized ON fingerprints USING btree (song_id, time_offset_ms);",
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fingerprints_hash_song_optimized ON fingerprints USING btree (hash_value, song_id, time_offset_ms);"
                ]
                
                for index_sql in critical_indexes:
                    try:
                        session.execute(index_sql)
                        applied_optimizations.append({
                            'type': 'index_creation',
                            'status': 'success',
                            'description': f'Created/verified index: {index_sql.split()[-3]}'
                        })
                    except Exception as e:
                        if 'already exists' in str(e).lower():
                            applied_optimizations.append({
                                'type': 'index_creation',
                                'status': 'skipped',
                                'description': f'Index already exists: {index_sql.split()[-3]}'
                            })
                        else:
                            applied_optimizations.append({
                                'type': 'index_creation',
                                'status': 'failed',
                                'description': f'Failed to create index: {e}'
                            })
            
            except Exception as e:
                applied_optimizations.append({
                    'type': 'index_creation',
                    'status': 'failed',
                    'description': f'Failed to create indexes: {e}'
                })
        
        return applied_optimizations
    
    def generate_optimization_report(self, output_file: str = None) -> Dict[str, Any]:
        """Generate comprehensive optimization report."""
        report = {
            'timestamp': time.time(),
            'database_statistics': {},
            'query_analysis': [],
            'index_analysis': [],
            'fingerprint_performance': {},
            'optimization_suggestions': [],
            'applied_optimizations': []
        }
        
        try:
            # Gather all analysis data
            report['database_statistics'] = self.get_table_statistics()
            report['query_analysis'] = [
                {
                    'query': qa.query,
                    'calls': qa.calls,
                    'total_time_ms': qa.total_time_ms,
                    'mean_time_ms': qa.mean_time_ms,
                    'min_time_ms': qa.min_time_ms,
                    'max_time_ms': qa.max_time_ms
                }
                for qa in self.analyze_query_performance()
            ]
            report['index_analysis'] = [
                {
                    'table_name': ia.table_name,
                    'index_name': ia.index_name,
                    'size_mb': ia.size_mb,
                    'scans': ia.scans,
                    'usage_ratio': ia.usage_ratio,
                    'is_used': ia.is_used
                }
                for ia in self.analyze_index_usage()
            ]
            report['fingerprint_performance'] = self.analyze_fingerprint_query_performance()
            report['optimization_suggestions'] = self.suggest_optimizations()
            
            # Apply basic optimizations
            report['applied_optimizations'] = self.apply_optimizations(auto_apply=False)
            
        except Exception as e:
            report['error'] = str(e)
        
        # Save report if output file specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
        
        return report


def main():
    """Main function for database optimization."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database Optimization Tool')
    parser.add_argument('--analyze', action='store_true', help='Analyze database performance')
    parser.add_argument('--optimize', action='store_true', help='Apply optimizations')
    parser.add_argument('--report', help='Generate optimization report')
    parser.add_argument('--auto-apply', action='store_true', help='Automatically apply safe optimizations')
    
    args = parser.parse_args()
    
    optimizer = DatabaseOptimizer()
    
    if args.analyze or not any([args.optimize, args.report]):
        print("Analyzing database performance...")
        
        # Query analysis
        print("\nTop slow queries:")
        try:
            query_analyses = optimizer.analyze_query_performance()
            for i, qa in enumerate(query_analyses[:5], 1):
                print(f"  {i}. {qa.mean_time_ms:.1f}ms avg ({qa.calls} calls): {qa.query[:80]}...")
        except Exception as e:
            print(f"  Error analyzing queries: {e}")
        
        # Index analysis
        print("\nIndex usage:")
        try:
            index_analyses = optimizer.analyze_index_usage()
            for ia in index_analyses[:10]:
                status = "USED" if ia.is_used else "UNUSED"
                print(f"  {ia.table_name}.{ia.index_name}: {status} ({ia.size_mb:.1f}MB, {ia.scans} scans)")
        except Exception as e:
            print(f"  Error analyzing indexes: {e}")
        
        # Fingerprint performance
        print("\nFingerprint query performance:")
        try:
            fp_perf = optimizer.analyze_fingerprint_query_performance()
            for metric, value in fp_perf.items():
                print(f"  {metric}: {value:.1f}ms")
        except Exception as e:
            print(f"  Error analyzing fingerprint performance: {e}")
    
    if args.optimize:
        print("\nApplying optimizations...")
        optimizations = optimizer.apply_optimizations(auto_apply=args.auto_apply)
        
        for opt in optimizations:
            status_symbol = "✓" if opt['status'] == 'success' else "✗" if opt['status'] == 'failed' else "~"
            print(f"  {status_symbol} {opt['description']}")
    
    if args.report:
        print(f"\nGenerating optimization report: {args.report}")
        report = optimizer.generate_optimization_report(args.report)
        
        print(f"Report saved to: {args.report}")
        
        # Print summary
        if 'optimization_suggestions' in report:
            print(f"\nOptimization suggestions: {len(report['optimization_suggestions'])}")
            for suggestion in report['optimization_suggestions'][:5]:
                print(f"  {suggestion['priority'].upper()}: {suggestion['issue']}")


if __name__ == "__main__":
    main()