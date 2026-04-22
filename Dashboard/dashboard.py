"""
Streamlit Dashboard for Pricing Intelligence
Shows pricing analysis results in an interactive dashboard
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="E-commerce Retail Pricing Intelligence",
    page_icon="**",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .big-metric {
        font-size: 2em;
        font-weight: bold;
    }
    .alert-high { color: #dc3545; }
    .alert-medium { color: #ffc107; }
    .alert-low { color: #28a745; }
</style>
""", unsafe_allow_html=True)


def load_data():
    """Load data from SQLite database"""
    conn = sqlite3.connect('pricing_data.db')
    
    # Latest analysis
    analysis_df = pd.read_sql_query("""
        SELECT 
            pa.*,
            ROW_NUMBER() OVER (PARTITION BY pa.sku ORDER BY pa.analyzed_at DESC) as rn
        FROM price_analysis pa
    """, conn)
    analysis_df = analysis_df[analysis_df['rn'] == 1].drop('rn', axis=1)
    
    # Competitor prices
    prices_df = pd.read_sql_query("""
        SELECT * FROM competitor_prices
        WHERE scraped_at IN (
            SELECT MAX(scraped_at) FROM competitor_prices GROUP BY sku, competitor
        )
    """, conn)
    
    conn.close()
    return analysis_df, prices_df


# Header
st.title(" E-commerce Retail Pricing Intelligence Dashboard")
st.markdown("**Real-time competitive pricing analysis powered by AI**")

# Load data
try:
    analysis_df, prices_df = load_data()
    
    if len(analysis_df) == 0:
        st.warning(" No pricing data found. Run `python pricing_agent.py` first to analyze products.")
        st.stop()
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "SKUs Analyzed",
            len(analysis_df),
            help="Total products in database"
        )
    
    with col2:
        avg_gap = analysis_df['price_gap_pct'].mean()
        st.metric(
            "Avg Price Gap",
            f"{avg_gap:+.1f}%",
            delta=f"{'Below' if avg_gap < 0 else 'Above'} market",
            help="Negative = we're cheaper, Positive = we're more expensive"
        )
    
    with col3:
        high_alerts = len(analysis_df[abs(analysis_df['price_gap_pct']) > 10])
        st.metric(
            "High Priority",
            high_alerts,
            help="SKUs with >10% price gap"
        )
    
    with col4:
        margin_opps = len(analysis_df[analysis_df['price_gap_pct'] < -10])
        st.metric(
            "Margin Opportunities",
            margin_opps,
            help="SKUs where we're significantly cheaper (can raise price)"
        )
    
    st.divider()
    
    # Main content - tabs
    tab1, tab2, tab3, tab4 = st.tabs([" Overview", " Alerts", " Trends", " Opportunities"])
    
    with tab1:
        st.subheader("Pricing Position Overview")
        
        # Price gap distribution
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Create price gap chart
            fig = go.Figure()
            
            # Add bars colored by severity
            colors = []
            for gap in analysis_df['price_gap_pct']:
                if gap > 10:
                    colors.append('#dc3545')  # Red - above market
                elif gap > 5:
                    colors.append('#ffc107')  # Yellow - caution
                elif gap < -10:
                    colors.append('#17a2b8')  # Blue - margin opportunity
                else:
                    colors.append('#28a745')  # Green - competitive
            
            fig.add_trace(go.Bar(
                x=analysis_df['sku'],
                y=analysis_df['price_gap_pct'],
                marker_color=colors,
                text=analysis_df['price_gap_pct'].round(1),
                texttemplate='%{text}%',
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Price Gap: %{y:.1f}%<extra></extra>'
            ))
            
            fig.update_layout(
                title="Price Gap by SKU (%)",
                xaxis_title="SKU",
                yaxis_title="Price Gap (%)",
                height=400,
                showlegend=False,
                hovermode='x'
            )
            
            # Add reference lines
            fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
            fig.add_hline(y=10, line_dash="dot", line_color="red", opacity=0.3)
            fig.add_hline(y=-10, line_dash="dot", line_color="blue", opacity=0.3)
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Position distribution
            above = len(analysis_df[analysis_df['price_gap_pct'] > 5])
            at_market = len(analysis_df[(analysis_df['price_gap_pct'] >= -5) & (analysis_df['price_gap_pct'] <= 5)])
            below = len(analysis_df[analysis_df['price_gap_pct'] < -5])
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=['Above Market', 'At Market', 'Below Market'],
                values=[above, at_market, below],
                marker_colors=['#dc3545', '#28a745', '#17a2b8'],
                hole=0.4
            )])
            
            fig_pie.update_layout(
                title="Market Position Distribution",
                height=400,
                showlegend=True
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Detailed table
        st.subheader("Detailed Analysis")
        
        # Format dataframe for display
        display_df = analysis_df[[
            'sku', 'our_price', 'competitor_avg', 'competitor_min', 
            'competitor_max', 'price_gap_pct', 'recommendation', 'confidence_score'
        ]].copy()
        
        display_df.columns = ['SKU', 'Our Price', 'Avg Comp', 'Min Comp', 'Max Comp', 'Gap %', 'Action', 'Confidence']
        display_df['Our Price'] = display_df['Our Price'].apply(lambda x: f'${x:.2f}')
        display_df['Avg Comp'] = display_df['Avg Comp'].apply(lambda x: f'${x:.2f}')
        display_df['Min Comp'] = display_df['Min Comp'].apply(lambda x: f'${x:.2f}')
        display_df['Max Comp'] = display_df['Max Comp'].apply(lambda x: f'${x:.2f}')
        display_df['Gap %'] = display_df['Gap %'].apply(lambda x: f'{x:+.1f}%')
        display_df['Confidence'] = display_df['Confidence'].apply(lambda x: f'{x*100:.0f}%')
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=400
        )
    
    with tab2:
        st.subheader(" High Priority Alerts")
        
        # Filter high priority items
        alerts = analysis_df[abs(analysis_df['price_gap_pct']) > 10].copy()
        alerts = alerts.sort_values('price_gap_pct', key=abs, ascending=False)
        
        if len(alerts) == 0:
            st.success(" No high-priority alerts! All prices are within 10% of market.")
        else:
            for idx, row in alerts.iterrows():
                gap = row['price_gap_pct']
                
                # Determine alert level
                if abs(gap) > 20:
                    alert_type = "error"
                    icon = "!"
                elif abs(gap) > 15:
                    alert_type = "warning"
                    icon = "@"
                else:
                    alert_type = "info"
                    icon = "#"
                
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"### {icon} {row['sku']}")
                        st.markdown(f"**Price Gap:** {gap:+.1f}%")
                        st.markdown(f"**Our Price:** ${row['our_price']:.2f} | **Market Avg:** ${row['competitor_avg']:.2f}")
                        st.markdown(f"**Recommendation:** {row['recommendation'].upper()}")
                        st.markdown(f"**Reasoning:** {row['reasoning']}")
                    
                    with col2:
                        if gap > 0:
                            st.error(f"We're {gap:.1f}% HIGHER")
                        else:
                            st.info(f"We're {abs(gap):.1f}% LOWER")
                        
                        st.metric("Confidence", f"{row['confidence_score']*100:.0f}%")
                    
                    st.divider()
    
    with tab3:
        st.subheader("📈 Price Trends")
        st.info("🚧 Historical trend analysis will be available after multiple scans over time.")
        
        # For now, show current price ranges
        st.markdown("### Current Price Ranges by SKU")
        
        fig_range = go.Figure()
        
        for idx, row in analysis_df.iterrows():
            fig_range.add_trace(go.Scatter(
                x=[row['competitor_min'], row['competitor_max']],
                y=[row['sku'], row['sku']],
                mode='lines',
                line=dict(color='lightgray', width=8),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            # Add our price as a marker
            fig_range.add_trace(go.Scatter(
                x=[row['our_price']],
                y=[row['sku']],
                mode='markers',
                marker=dict(
                    size=12,
                    color='red' if row['price_gap_pct'] > 5 else 'green',
                    symbol='diamond'
                ),
                name='Our Price',
                showlegend=idx==0,
                hovertemplate=f"<b>{row['sku']}</b><br>Our Price: ${row['our_price']:.2f}<extra></extra>"
            ))
        
        fig_range.update_layout(
            title="Our Price vs Competitor Range",
            xaxis_title="Price ($)",
            yaxis_title="SKU",
            height=max(400, len(analysis_df) * 40),
            hovermode='closest'
        )
        
        st.plotly_chart(fig_range, use_container_width=True)
    
    with tab4:
        st.subheader("💰 Margin Opportunities")
        
        # Find products where we're significantly below market
        opps = analysis_df[analysis_df['price_gap_pct'] < -5].copy()
        opps = opps.sort_values('price_gap_pct')
        
        if len(opps) == 0:
            st.info("No significant margin opportunities identified at this time.")
        else:
            st.success(f"Found {len(opps)} products where we can potentially increase prices!")
            
            for idx, row in opps.iterrows():
                with st.expander(f"💎 {row['sku']} - Opportunity to increase by {abs(row['price_gap_pct']):.1f}%"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Current Price", f"${row['our_price']:.2f}")
                        st.metric("Market Average", f"${row['competitor_avg']:.2f}")
                    
                    with col2:
                        potential_increase = row['competitor_avg'] - row['our_price']
                        st.metric("Potential Increase", f"${potential_increase:.2f}")
                        st.metric("New Suggested Price", f"${row['competitor_avg'] * 0.98:.2f}")
                    
                    with col3:
                        # Calculate potential revenue impact (assuming 100 units sold)
                        units = 100  # This would come from sales data
                        revenue_impact = potential_increase * units
                        st.metric("Revenue Impact", f"${revenue_impact:.2f}", 
                                 delta=f"Based on {units} units/month")
                    
                    st.markdown(f"**Reasoning:** {row['reasoning']}")
    
    # Footer
    st.divider()
    last_update = analysis_df['analyzed_at'].max()
    st.caption(f"Last updated: {last_update} | Data source: pricing_data.db")

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.info("Make sure you've run `python pricing_agent.py` first to generate data.")
