"""
Export utilities for arbitrage data
Support CSV, Excel, JSON, and PDF formats
"""

import json
import csv
import logging
from typing import List, Dict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class DataExporter:
    """Export arbitrage data to various formats"""
    
    def __init__(self, output_dir: str = "exports"):
        """
        Initialize exporter
        
        Args:
            output_dir: Directory for exported files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_opportunities_to_csv(self, opportunities: List, 
                                   filename: str = None) -> str:
        """
        Export opportunities to CSV
        
        Args:
            opportunities: List of ArbitrageOpportunity objects
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to exported file
        """
        if filename is None:
            filename = f"opportunities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if not opportunities:
                    f.write("No opportunities to export\n")
                    return str(filepath)
                
                # Get field names from first opportunity
                fieldnames = [
                    'Timestamp', 'Type', 'Asset', 'Source', 'Destination',
                    'Profit %', 'Profit $', 'Buy Price', 'Sell Price',
                    'Risk', 'Confidence', 'Capital Required', 'Fees',
                    'Path'
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for opp in opportunities:
                    writer.writerow({
                        'Timestamp': opp.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'Type': opp.arbitrage_type.value,
                        'Asset': opp.asset,
                        'Source': opp.source,
                        'Destination': opp.destination,
                        'Profit %': f"{opp.profit_percentage:.2f}",
                        'Profit $': f"{opp.profit_absolute:.2f}",
                        'Buy Price': f"{opp.buy_price:.4f}",
                        'Sell Price': f"{opp.sell_price:.4f}",
                        'Risk': opp.risk_level,
                        'Confidence': f"{opp.confidence*100:.0f}%",
                        'Capital Required': f"{opp.required_capital:.2f}",
                        'Fees': f"{opp.fees_estimated:.4f}",
                        'Path': ' → '.join(opp.path)
                    })
            
            logger.info(f"Exported {len(opportunities)} opportunities to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return None
    
    def export_opportunities_to_json(self, opportunities: List,
                                    filename: str = None) -> str:
        """Export opportunities to JSON"""
        if filename is None:
            filename = f"opportunities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.output_dir / filename
        
        try:
            data = {
                'export_time': datetime.now().isoformat(),
                'total_count': len(opportunities),
                'opportunities': [
                    {
                        'id': opp.opportunity_id,
                        'timestamp': opp.timestamp.isoformat(),
                        'type': opp.arbitrage_type.value,
                        'asset': opp.asset,
                        'source': opp.source,
                        'destination': opp.destination,
                        'profit_percentage': opp.profit_percentage,
                        'profit_absolute': opp.profit_absolute,
                        'buy_price': opp.buy_price,
                        'sell_price': opp.sell_price,
                        'confidence': opp.confidence,
                        'risk_level': opp.risk_level,
                        'required_capital': opp.required_capital,
                        'fees_estimated': opp.fees_estimated,
                        'path': opp.path
                    }
                    for opp in opportunities
                ]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(opportunities)} opportunities to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            return None
    
    def export_opportunities_to_excel(self, opportunities: List,
                                     filename: str = None) -> str:
        """Export opportunities to Excel"""
        try:
            import pandas as pd
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment
            
            if filename is None:
                filename = f"opportunities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            filepath = self.output_dir / filename
            
            # Create DataFrame
            data = []
            for opp in opportunities:
                data.append({
                    'Timestamp': opp.timestamp,
                    'Type': opp.arbitrage_type.value,
                    'Asset': opp.asset,
                    'Source': opp.source,
                    'Destination': opp.destination,
                    'Profit %': opp.profit_percentage,
                    'Profit $': opp.profit_absolute,
                    'Buy Price': opp.buy_price,
                    'Sell Price': opp.sell_price,
                    'Risk': opp.risk_level,
                    'Confidence': opp.confidence * 100,
                    'Capital': opp.required_capital,
                    'Fees': opp.fees_estimated,
                    'Path': ' → '.join(opp.path)
                })
            
            df = pd.DataFrame(data)
            
            # Write to Excel with formatting
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Opportunities', index=False)
                
                # Get workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['Opportunities']
                
                # Format header
                header_fill = PatternFill(start_color='2ecc71', end_color='2ecc71', fill_type='solid')
                header_font = Font(bold=True, color='FFFFFF')
                
                for cell in worksheet[1]:
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal='center')
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            logger.info(f"Exported {len(opportunities)} opportunities to {filepath}")
            return str(filepath)
            
        except ImportError:
            logger.warning("pandas or openpyxl not installed. Excel export unavailable.")
            return None
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            return None
    
    def export_summary_report(self, opportunities: List, stats: Dict,
                             filename: str = None) -> str:
        """Export summary report as text"""
        if filename is None:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("ARBITRAGE OPPORTUNITY REPORT\n")
                f.write("=" * 80 + "\n\n")
                
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Opportunities: {len(opportunities)}\n\n")
                
                if stats:
                    f.write("-" * 80 + "\n")
                    f.write("SUMMARY STATISTICS\n")
                    f.write("-" * 80 + "\n")
                    f.write(f"Average Profit: {stats.get('avg_profit', 0):.2f}%\n")
                    f.write(f"Maximum Profit: {stats.get('max_profit', 0):.2f}%\n")
                    f.write(f"Minimum Profit: {stats.get('min_profit', 0):.2f}%\n\n")
                    
                    if 'by_type' in stats:
                        f.write("By Type:\n")
                        for typ, count in stats['by_type'].items():
                            f.write(f"  - {typ}: {count}\n")
                        f.write("\n")
                    
                    if 'by_risk' in stats:
                        f.write("By Risk Level:\n")
                        for risk, count in stats['by_risk'].items():
                            f.write(f"  - {risk}: {count}\n")
                        f.write("\n")
                
                if opportunities:
                    f.write("-" * 80 + "\n")
                    f.write("TOP 10 OPPORTUNITIES\n")
                    f.write("-" * 80 + "\n\n")
                    
                    for i, opp in enumerate(opportunities[:10], 1):
                        f.write(f"#{i} {opp.arbitrage_type.value.upper()} - {opp.asset}\n")
                        f.write(f"   Profit: {opp.profit_percentage:.2f}% (${opp.profit_absolute:.2f})\n")
                        f.write(f"   Path: {' → '.join(opp.path)}\n")
                        f.write(f"   Risk: {opp.risk_level} | Confidence: {opp.confidence*100:.0f}%\n")
                        f.write(f"   Capital: ${opp.required_capital:.2f}\n")
                        f.write("\n")
                
                f.write("=" * 80 + "\n")
                f.write("END OF REPORT\n")
                f.write("=" * 80 + "\n")
            
            logger.info(f"Exported summary report to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error exporting summary report: {e}")
            return None
    
    def export_all_formats(self, opportunities: List, stats: Dict = None) -> Dict[str, str]:
        """
        Export to all available formats
        
        Returns:
            Dict of {format: filepath}
        """
        results = {}
        
        # CSV
        csv_path = self.export_opportunities_to_csv(opportunities)
        if csv_path:
            results['csv'] = csv_path
        
        # JSON
        json_path = self.export_opportunities_to_json(opportunities)
        if json_path:
            results['json'] = json_path
        
        # Excel
        excel_path = self.export_opportunities_to_excel(opportunities)
        if excel_path:
            results['excel'] = excel_path
        
        # Summary report
        report_path = self.export_summary_report(opportunities, stats or {})
        if report_path:
            results['report'] = report_path
        
        return results
