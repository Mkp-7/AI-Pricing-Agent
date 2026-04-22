"""
Pricing Intelligence Agent
Analyzes 10-20 SKUs against competitors using Claude API with web search
Zero-cost MVP for E-commerce Retailer
"""

import anthropic
import json
import sqlite3
from datetime import datetime
from typing import List, Dict
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

class PricingAgent:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.db_path = "pricing_data.db"
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                sku TEXT PRIMARY KEY,
                name TEXT,
                category TEXT,
                our_price REAL,
                cost REAL,
                last_updated TEXT
            )
        """)
        
        # Competitor prices table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competitor_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT,
                competitor TEXT,
                price REAL,
                in_stock INTEGER,
                url TEXT,
                scraped_at TEXT,
                FOREIGN KEY (sku) REFERENCES products(sku)
            )
        """)
        
        # Price analysis table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT,
                our_price REAL,
                competitor_avg REAL,
                competitor_min REAL,
                competitor_max REAL,
                price_gap_pct REAL,
                recommendation TEXT,
                reasoning TEXT,
                confidence_score REAL,
                analyzed_at TEXT,
                FOREIGN KEY (sku) REFERENCES products(sku)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def analyze_sku(self, sku: str, product_name: str, our_price: float, cost: float = None) -> Dict:
        """
        Analyze a single SKU against competitors using Claude with web search
        """
        
        prompt = f"""You are a pricing analyst API that returns ONLY valid JSON.

Product to analyze:
- SKU: {sku}
- Name: {product_name}
- Our Price: ${our_price}
{f"- Our Cost: ${cost}" if cost else ""}

Task:
1. Search Amazon.com, Walmart.com, LesliesPool.com for this product
2. Extract current prices
3. Return analysis as JSON

CRITICAL RULES:
- Return ONLY the JSON object below
- NO explanations, NO markdown, NO text before or after
- Start with {{ and end with }}
- If you can't find a competitor, omit them from the array

{{
    "competitors_found": [
        {{
            "competitor": "Amazon",
            "price": 29.99,
            "in_stock": true,
            "url": "https://...",
            "product_match_confidence": "high",
            "notes": "Exact match found"
        }}
    ],
    "analysis": {{
        "our_price": {our_price},
        "competitor_avg": 31.50,
        "competitor_min": 29.99,
        "competitor_max": 34.99,
        "price_gap_pct": -4.8,
        "market_position": "below_market",
        "recommendation": "increase",
        "recommended_price": 32.99,
        "reasoning": "We are 4.8% below market average. Consider increasing to $32.99 to capture margin.",
        "confidence_score": 0.85,
        "urgency": "low"
    }}
}}

Return ONLY this JSON structure with actual data. No other text."""

        print(f"\n Analyzing {sku} - {product_name}...")
        
        try:
            # Call Claude with web search enabled
            message = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2000,
                tools=[
                    {
                        "type": "web_search_20260209",
                        "name": "web_search",
                        "allowed_callers": ["direct"]
                    }
                ],
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract the response
            response_text = ""
            for block in message.content:
                if block.type == "text":
                    response_text += block.text
            
            print(f" Raw response received for {sku}")
            
            # Parse JSON response - extract JSON from any surrounding text
            response_text = response_text.strip()

            # Remove markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            # Find JSON object boundaries
            start = response_text.find('{')
            end = response_text.rfind('}') + 1

            if start != -1 and end > start:
                response_text = response_text[start:end]
            else:
                raise ValueError("No valid JSON found in response")

            result = json.loads(response_text)

            result['sku'] = sku
            result['product_name'] = product_name
            
            # Save to database
            self.save_analysis(result)
            
            return result
            
        except json.JSONDecodeError as e:
            print(f" JSON parsing error for {sku}: {e}")
            print(f"Response text: {response_text[:500]}")
            return {
                "error": "JSON parsing failed",
                "sku": sku,
                "raw_response": response_text[:500]
            }
        except Exception as e:
            print(f" Error analyzing {sku}: {str(e)}")
            return {
                "error": str(e),
                "sku": sku
            }
    
    def save_analysis(self, result: Dict):
        """Save analysis results to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        sku = result['sku']
        timestamp = datetime.now().isoformat()
        
        # Save competitor prices
        for comp in result.get('competitors_found', []):
            cursor.execute("""
                INSERT INTO competitor_prices 
                (sku, competitor, price, in_stock, url, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                sku,
                comp['competitor'],
                comp.get('price'),
                1 if comp.get('in_stock') else 0,
                comp.get('url'),
                timestamp
            ))
        
        # Save analysis
        analysis = result.get('analysis', {})
        cursor.execute("""
            INSERT INTO price_analysis
            (sku, our_price, competitor_avg, competitor_min, competitor_max,
             price_gap_pct, recommendation, reasoning, confidence_score, analyzed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sku,
            analysis.get('our_price'),
            analysis.get('competitor_avg'),
            analysis.get('competitor_min'),
            analysis.get('competitor_max'),
            analysis.get('price_gap_pct'),
            analysis.get('recommendation'),
            analysis.get('reasoning'),
            analysis.get('confidence_score'),
            timestamp
        ))
        
        conn.commit()
        conn.close()
        print(f" Saved analysis for {sku}")
    
    def batch_analyze(self, products: List[Dict]) -> List[Dict]:
        """
        Analyze multiple products
        """
        results = []
        
        for i, product in enumerate(products, 1):
            print(f"\n{'='*60}")
            print(f"Analyzing {i}/{len(products)}")
            print(f"{'='*60}")
            
            result = self.analyze_sku(
                sku=product['sku'],
                product_name=product['name'],
                our_price=product['our_price'],
                cost=product.get('cost')
            )
            results.append(result)
            
            import time
            time.sleep(1)
        
        return results
    
    def generate_report(self) -> str:
        """Generate a text report from latest analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get latest analysis for all SKUs
        cursor.execute("""
            SELECT 
                pa.sku,
                pa.our_price,
                pa.competitor_avg,
                pa.competitor_min,
                pa.competitor_max,
                pa.price_gap_pct,
                pa.recommendation,
                pa.reasoning,
                pa.confidence_score,
                pa.analyzed_at
            FROM price_analysis pa
            INNER JOIN (
                SELECT sku, MAX(analyzed_at) as max_date
                FROM price_analysis
                GROUP BY sku
            ) latest ON pa.sku = latest.sku AND pa.analyzed_at = latest.max_date
            ORDER BY ABS(pa.price_gap_pct) DESC
        """)
        
        results = cursor.fetchall()
        
        report = f"""
╔══════════════════════════════════════════════════════════════════╗
║                 PRICING INTELLIGENCE REPORT                      ║
║          Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  ║
╚══════════════════════════════════════════════════════════════════╝

"""
        
        # Summary stats
        if results:
            avg_gap = sum(abs(r[5]) for r in results) / len(results)
            above_market = sum(1 for r in results if r[5] > 5)
            below_market = sum(1 for r in results if r[5] < -5)
            
            report += f"""
SUMMARY:
  Total SKUs Analyzed: {len(results)}
  Average Price Gap: {avg_gap:.1f}%
  
  Pricing Position:
    • Above Market (>5%): {above_market} SKUs
    • At Market (-5% to +5%): {len(results) - above_market - below_market} SKUs
    • Below Market (<-5%): {below_market} SKUs

"""
        
        report += "\n" + "="*70 + "\n"
        report += "DETAILED ANALYSIS BY SKU\n"
        report += "="*70 + "\n\n"
        
        for row in results:
            sku, our_price, comp_avg, comp_min, comp_max, gap, rec, reasoning, conf, analyzed_at = row
            
            # Get competitor details for this SKU
            cursor.execute("""
                SELECT competitor, price, in_stock, url
                FROM competitor_prices
                WHERE sku = ?
                AND scraped_at = (
                    SELECT MAX(scraped_at) 
                    FROM competitor_prices 
                    WHERE sku = ?
                )
                ORDER BY price ASC
            """, (sku, sku))
            
            competitors = cursor.fetchall()
            
            # Status indicator
            if gap > 10:
                status = " HIGH RISK"
            elif gap > 5:
                status = " CAUTION"
            elif gap < -10:
                status = " MARGIN OPP"
            else:
                status = " COMPETITIVE"
            
            report += f"""
SKU: {sku}
Status: {status}
Price Gap: {gap:+.1f}%

Our Price:         ${our_price:.2f}
Market Range:      ${comp_min:.2f} - ${comp_max:.2f}
Market Average:    ${comp_avg:.2f}

COMPETITOR PRICES:
"""
            
            # Add competitor details
            if competitors:
                for comp_name, comp_price, in_stock, url in competitors:
                    stock_status = "In Stock" if in_stock else "Out of Stock"
                    report += f"  • {comp_name}: ${comp_price:.2f} ({stock_status})\n"
                    if url:
                        report += f"    URL: {url}\n"
            else:
                report += "  • No competitor data found\n"
            
            report += f"""
Recommendation: {rec.upper()}
{reasoning}

Confidence: {conf*100:.0f}%
Analyzed: {analyzed_at}

{'-'*70}
"""
        
        conn.close()
        return report
    
    def get_alerts(self, threshold: float = 10.0) -> List[Dict]:
        """Get high-priority alerts for SKUs with large price gaps"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                sku,
                our_price,
                competitor_avg,
                price_gap_pct,
                recommendation,
                reasoning
            FROM price_analysis
            WHERE ABS(price_gap_pct) > ?
            ORDER BY ABS(price_gap_pct) DESC
        """, (threshold,))
        
        alerts = []
        for row in cursor.fetchall():
            alerts.append({
                "sku": row[0],
                "our_price": row[1],
                "competitor_avg": row[2],
                "price_gap_pct": row[3],
                "recommendation": row[4],
                "reasoning": row[5]
            })
        
        conn.close()
        return alerts


def main():
    """Example usage"""
    
    # Get API key from environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Please set ANTHROPIC_API_KEY environment variable")
        print("   Get your free API key at: https://console.anthropic.com/")
        return
    
    # Initialize agent
    agent = PricingAgent(api_key=api_key)
    
    # Products to analyze
    products = [
        {
            "sku": "VAC-BRUSH-20",
            "name": "20 inch Pool & Spa Vacuum Brush",
            "our_price": 17.99,
            "cost": 12.00
        }
    ]
    
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                     PRICING INTELLIGENCE AGENT                   ║
║                        Starting Analysis...                      ║
╚══════════════════════════════════════════════════════════════════╝

Analyzing {len(products)} SKUs against:
  • Amazon.com
  • Walmart.com  
  • LesliesPool.com

This will take approximately {len(products) * 15} seconds...
""")
    
    # Run analysis
    results = agent.batch_analyze(products)
    
    # Generate and print report
    print("\n\n")
    report = agent.generate_report()
    print(report)
    
    # Save report to file
    with open("pricing_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n Report saved to: pricing_report.txt")
    
    # Get high-priority alerts
    alerts = agent.get_alerts(threshold=10.0)
    if alerts:
        print(f"\n  {len(alerts)} HIGH PRIORITY ALERTS (>10% price gap):")
        for alert in alerts:
            print(f"   • {alert['sku']}: {alert['price_gap_pct']:+.1f}% - {alert['recommendation'].upper()}")


if __name__ == "__main__":
    main()
