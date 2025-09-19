#!/usr/bin/env python3
"""
Database Query Tool for Enhanced Multi-Strategy NIFTY Trading Bot

Interactive tool to query and analyze the trading database.
"""

import sqlite3
import pandas as pd
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import json


class DatabaseQuery:
    """Interactive database query tool."""
    
    def __init__(self, db_path: str = "DBs/nifty500_trading_data.db"):
        """Initialize database query tool."""
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
    
    def get_connection(self):
        """Get database connection."""
        return sqlite3.connect(str(self.db_path))
    
    def show_database_info(self):
        """Show database information and statistics."""
        print("Enhanced Multi-Strategy NIFTY Trading Bot - Database Info")
        print("=" * 60)
        
        with self.get_connection() as conn:
            # Show tables
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            print(f"\nTables in database: {len(tables)}")
            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table}: {count:,} records")
            
            # Show unique symbols
            cursor = conn.execute("SELECT COUNT(DISTINCT symbol) FROM price_data")
            unique_symbols = cursor.fetchone()[0]
            print(f"\nUnique symbols: {unique_symbols}")
            
            # Show date range
            cursor = conn.execute("SELECT MIN(timestamp), MAX(timestamp) FROM price_data")
            date_range = cursor.fetchone()
            print(f"Date range: {date_range[0]} to {date_range[1]}")
            
            # Show recent signals if enhanced_signals table exists
            if 'enhanced_signals' in tables:
                cursor = conn.execute("""
                    SELECT composite_signal, COUNT(*) as count 
                    FROM enhanced_signals 
                    GROUP BY composite_signal 
                    ORDER BY count DESC
                """)
                signal_counts = cursor.fetchall()
                
                if signal_counts:
                    print(f"\nRecent Enhanced Signals:")
                    for signal, count in signal_counts:
                        print(f"  {signal}: {count}")
    
    def get_latest_signals(self, limit: int = 20, signal_type: str = None):
        """Get latest enhanced signals."""
        print(f"\nLatest Enhanced Signals (limit: {limit})")
        print("-" * 80)
        
        with self.get_connection() as conn:
            query = """
                SELECT symbol, timestamp, composite_signal, composite_score, 
                       composite_confidence, price, price_change_percent
                FROM enhanced_signals 
            """
            
            params = []
            if signal_type:
                query += " WHERE composite_signal = ?"
                params.append(signal_type)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            df = pd.read_sql_query(query, conn, params=params)
            
            if df.empty:
                print("No enhanced signals found.")
                return
            
            # Format the output
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['price'] = df['price'].round(2)
            df['price_change_percent'] = df['price_change_percent'].round(2)
            df['composite_score'] = df['composite_score'].round(1)
            df['composite_confidence'] = (df['composite_confidence'] * 100).round(1)
            
            print(df.to_string(index=False))
    
    def get_symbol_analysis(self, symbol: str):
        """Get comprehensive analysis for a specific symbol."""
        print(f"\nSymbol Analysis: {symbol}")
        print("=" * 50)
        
        with self.get_connection() as conn:
            # Get latest price data
            cursor = conn.execute("""
                SELECT timestamp, close, volume 
                FROM price_data 
                WHERE symbol = ? 
                ORDER BY timestamp DESC 
                LIMIT 5
            """, (symbol,))
            
            price_data = cursor.fetchall()
            if price_data:
                print("\nRecent Price Data:")
                for timestamp, close, volume in price_data:
                    print(f"  {timestamp}: ₹{close:.2f} (Vol: {volume:,})")
            
            # Get latest enhanced indicators if available
            cursor = conn.execute("""
                SELECT * FROM enhanced_indicators 
                WHERE symbol = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            """, (symbol,))
            
            indicator_data = cursor.fetchone()
            if indicator_data:
                print(f"\nLatest Enhanced Indicators:")
                columns = [desc[0] for desc in cursor.description]
                for i, col in enumerate(columns):
                    if col not in ['id', 'symbol', 'created_at'] and indicator_data[i] is not None:
                        value = indicator_data[i]
                        if isinstance(value, float):
                            print(f"  {col}: {value:.2f}")
                        else:
                            print(f"  {col}: {value}")
            
            # Get latest enhanced signals
            cursor = conn.execute("""
                SELECT timestamp, composite_signal, composite_score, 
                       composite_confidence, strategy_signals 
                FROM enhanced_signals 
                WHERE symbol = ? 
                ORDER BY timestamp DESC 
                LIMIT 3
            """, (symbol,))
            
            signals = cursor.fetchall()
            if signals:
                print(f"\nRecent Enhanced Signals:")
                for timestamp, signal, score, confidence, strategies in signals:
                    print(f"  {timestamp}: {signal} (Score: {score:.1f}, Confidence: {confidence:.1%})")
                    if strategies:
                        try:
                            strategy_data = json.loads(strategies)
                            for strategy_name, strategy_info in strategy_data.items():
                                print(f"    {strategy_name}: {strategy_info['signal']} ({strategy_info['confidence']:.1%})")
                        except:
                            pass
    
    def get_performance_summary(self, days: int = 30):
        """Get performance summary for recent signals."""
        print(f"\nPerformance Summary (Last {days} days)")
        print("-" * 50)
        
        with self.get_connection() as conn:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get signal distribution
            cursor = conn.execute("""
                SELECT composite_signal, COUNT(*) as count,
                       AVG(composite_score) as avg_score,
                       AVG(composite_confidence) as avg_confidence
                FROM enhanced_signals 
                WHERE timestamp > ?
                GROUP BY composite_signal
                ORDER BY count DESC
            """, (cutoff_date,))
            
            results = cursor.fetchall()
            if results:
                print("Signal Distribution:")
                for signal, count, avg_score, avg_confidence in results:
                    print(f"  {signal}: {count} signals (Avg Score: {avg_score:.1f}, Avg Confidence: {avg_confidence:.1%})")
            
            # Get top performing symbols
            cursor = conn.execute("""
                SELECT symbol, COUNT(*) as signal_count,
                       AVG(ABS(composite_score)) as avg_abs_score
                FROM enhanced_signals 
                WHERE timestamp > ? AND composite_signal != 'NO_SIGNAL'
                GROUP BY symbol
                HAVING signal_count >= 2
                ORDER BY avg_abs_score DESC
                LIMIT 10
            """, (cutoff_date,))
            
            top_symbols = cursor.fetchall()
            if top_symbols:
                print(f"\nTop Active Symbols:")
                for symbol, count, avg_score in top_symbols:
                    print(f"  {symbol}: {count} signals (Avg Score: {avg_score:.1f})")
    
    def export_signals_to_csv(self, output_file: str = "exported_signals.csv", days: int = 7):
        """Export recent signals to CSV file."""
        print(f"\nExporting signals from last {days} days to {output_file}...")
        
        with self.get_connection() as conn:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            query = """
                SELECT symbol, timestamp, composite_signal, composite_score, 
                       composite_confidence, legacy_signal, legacy_score,
                       price, price_change_percent, data_quality
                FROM enhanced_signals 
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            """
            
            df = pd.read_sql_query(query, conn, params=(cutoff_date,))
            
            if df.empty:
                print("No signals found for the specified period.")
                return
            
            df.to_csv(output_file, index=False)
            print(f"✅ Exported {len(df)} signals to {output_file}")
    
    def run_custom_query(self, query: str):
        """Run a custom SQL query."""
        print(f"\nExecuting custom query:")
        print(f"Query: {query}")
        print("-" * 50)
        
        try:
            with self.get_connection() as conn:
                df = pd.read_sql_query(query, conn)
                
                if df.empty:
                    print("No results found.")
                else:
                    print(df.to_string(index=False))
                    print(f"\nReturned {len(df)} rows")
                    
        except Exception as e:
            print(f"Error executing query: {e}")


def main():
    """Main function for database query tool."""
    parser = argparse.ArgumentParser(description="Query Enhanced Multi-Strategy Trading Database")
    parser.add_argument("--db", default="DBs/nifty500_trading_data.db", help="Database path")
    parser.add_argument("--info", action="store_true", help="Show database info")
    parser.add_argument("--signals", type=int, default=20, help="Show latest signals (default: 20)")
    parser.add_argument("--symbol", type=str, help="Analyze specific symbol")
    parser.add_argument("--performance", type=int, help="Show performance summary for N days")
    parser.add_argument("--export", type=str, help="Export signals to CSV file")
    parser.add_argument("--export-days", type=int, default=7, help="Days to export (default: 7)")
    parser.add_argument("--query", type=str, help="Run custom SQL query")
    parser.add_argument("--signal-type", type=str, choices=["BUY", "SELL", "NO_SIGNAL"], 
                       help="Filter signals by type")
    
    args = parser.parse_args()
    
    try:
        db_query = DatabaseQuery(args.db)
        
        if args.info:
            db_query.show_database_info()
        
        if args.signals:
            db_query.get_latest_signals(args.signals, args.signal_type)
        
        if args.symbol:
            db_query.get_symbol_analysis(args.symbol.upper())
        
        if args.performance:
            db_query.get_performance_summary(args.performance)
        
        if args.export:
            db_query.export_signals_to_csv(args.export, args.export_days)
        
        if args.query:
            db_query.run_custom_query(args.query)
        
        # If no specific action requested, show database info
        if not any([args.info, args.signals, args.symbol, args.performance, args.export, args.query]):
            db_query.show_database_info()
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()