#!/usr/bin/env python3
"""
Create Interactive HTML Visualizations for Each Analysis
"""

import json
import pandas as pd
from collections import Counter, defaultdict
import os

print("Loading network data...")
with open('network_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

nodes = data['nodes']
edges = data['edges']

PERIODS = ['Pre-Crimea', 'Post-Crimea', 'COVID', 'War']

network_json = json.dumps(data, ensure_ascii=False)

os.makedirs('interactive_visuals', exist_ok=True)

# ============================================================================
# VISUALIZATION 1: PERIOD COMPOSITION DASHBOARD
# ============================================================================
print("\nCreating Period Composition Dashboard...")

html_1 = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Period Composition Analysis</title>
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0f0f1e 0%, #1a1a2e 100%);
            color: #e0e0e0;
            padding: 20px;
        }}
        .container {{ max-width: 1800px; margin: 0 auto; }}
        h1 {{
            text-align: center;
            font-size: 32px;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .subtitle {{ text-align: center; color: #888; margin-bottom: 30px; }}
        .controls {{
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            gap: 20px;
            align-items: center;
            justify-content: center;
        }}
        .control-group {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        label {{
            font-size: 12px;
            color: #aaa;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        select {{
            padding: 10px 15px;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 6px;
            color: #e0e0e0;
            font-size: 14px;
            cursor: pointer;
        }}
        .chart-container {{
            background: rgba(255, 255, 255, 0.03);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .chart-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        .chart-title {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 15px;
            color: #667eea;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Attribute Composition Analysis Across Periods</h1>
        <p class="subtitle">How actor attributes change over the four time periods</p>
        
        <div class="controls">
            <div class="control-group">
                <label>Attribute</label>
                <select id="attributeSelect" onchange="updateCharts()">
                    <option value="sector">Sector</option>
                    <option value="state_private">State/Private</option>
                    <option value="actor_type">Actor Type</option>
                    <option value="jurisdiction">Jurisdiction</option>
                </select>
            </div>
            
            <div class="control-group">
                <label>Weighting</label>
                <select id="weightSelect" onchange="updateCharts()">
                    <option value="count">Entity Count</option>
                    <option value="mentions">Weighted by Mentions</option>
                </select>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">Period-by-Period Breakdown</div>
            <div class="chart-row">
                <div id="pie1"></div>
                <div id="pie2"></div>
            </div>
            <div class="chart-row">
                <div id="pie3"></div>
                <div id="pie4"></div>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">Evolution Over Time</div>
            <div id="evolution"></div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">Comparative Stacked View</div>
            <div id="stacked"></div>
        </div>
    </div>
    
    <script>
        const DATA = {network_json};
        const PERIODS = ['Pre-Crimea', 'Post-Crimea', 'COVID', 'War'];
        
        function getAttributeData(attribute, weighting) {{
            const result = {{}};
            
            PERIODS.forEach(period => {{
                const periodNodes = DATA.nodes.filter(n => n.periods.includes(period));
                const values = new Set(DATA.nodes.map(n => n[attribute]));
                const counts = {{}};
                
                values.forEach(val => {{
                    if (weighting === 'count') {{
                        counts[val] = periodNodes.filter(n => n[attribute] === val).length;
                    }} else {{
                        counts[val] = periodNodes
                            .filter(n => n[attribute] === val)
                            .reduce((sum, n) => sum + (n.period_counts[period] || 0), 0);
                    }}
                }});
                
                result[period] = counts;
            }});
            
            return result;
        }}
        
        function updateCharts() {{
            const attribute = document.getElementById('attributeSelect').value;
            const weighting = document.getElementById('weightSelect').value;
            const data = getAttributeData(attribute, weighting);
            
            // Create pie charts
            PERIODS.forEach((period, idx) => {{
                const counts = data[period];
                const labels = Object.keys(counts);
                const values = Object.values(counts);
                
                const pieData = [{{
                    labels: labels,
                    values: values,
                    type: 'pie',
                    hole: 0.4,
                    textinfo: 'label+percent',
                    textposition: 'outside',
                    marker: {{
                        colors: [
                            '#667eea', '#f6ad55', '#48bb78', '#ed64a6', '#fc8181',
                            '#4299e1', '#9f7aea', '#38b2ac', '#ed8936', '#ecc94b',
                            '#e53e3e', '#805ad5', '#d69e2e', '#718096'
                        ]
                    }}
                }}];
                
                const layout = {{
                    title: `${{period}} (${{values.reduce((a,b) => a+b, 0).toLocaleString()}} total)`,
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    font: {{ color: '#e0e0e0' }},
                    showlegend: true
                }};
                
                Plotly.newPlot(`pie${{idx+1}}`, pieData, layout, {{responsive: true}});
            }});
            
            // Create evolution line chart
            const allValues = [...new Set(DATA.nodes.map(n => n[attribute]))];
            const evolutionTraces = allValues.map(val => {{
                const y = PERIODS.map(period => {{
                    const total = Object.values(data[period]).reduce((a,b) => a+b, 0);
                    return total > 0 ? (data[period][val] || 0) / total * 100 : 0;
                }});
                
                return {{
                    x: PERIODS,
                    y: y,
                    mode: 'lines+markers',
                    name: val,
                    line: {{ width: 3 }},
                    marker: {{ size: 10 }}
                }};
            }});
            
            const evolutionLayout = {{
                xaxis: {{ title: 'Period' }},
                yaxis: {{ title: 'Percentage (%)' }},
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0.2)',
                font: {{ color: '#e0e0e0' }},
                hovermode: 'closest',
                legend: {{ orientation: 'h', y: -0.2 }}
            }};
            
            Plotly.newPlot('evolution', evolutionTraces, evolutionLayout, {{responsive: true}});
            
            // Create stacked area chart
            const stackedTraces = allValues.map(val => {{
                const y = PERIODS.map(period => data[period][val] || 0);
                
                return {{
                    x: PERIODS,
                    y: y,
                    name: val,
                    stackgroup: 'one',
                    groupnorm: 'percent'
                }};
            }});
            
            const stackedLayout = {{
                xaxis: {{ title: 'Period' }},
                yaxis: {{ title: 'Percentage (%)' }},
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0.2)',
                font: {{ color: '#e0e0e0' }},
                hovermode: 'x unified',
                legend: {{ orientation: 'h', y: -0.2 }}
            }};
            
            Plotly.newPlot('stacked', stackedTraces, stackedLayout, {{responsive: true}});
        }}
        
        // Initial render
        updateCharts();
    </script>
</body>
</html>
'''

with open('interactive_visuals/1_period_composition.html', 'w', encoding='utf-8') as f:
    f.write(html_1)
print("  ✓ Created: interactive_visuals/1_period_composition.html")

# ============================================================================
# VISUALIZATION 2: TOP 50 vs OVERALL COMPARISON
# ============================================================================
print("\nCreating Top 50 Comparison Dashboard...")

html_2 = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Top 50 vs Overall Network</title>
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0f0f1e 0%, #1a1a2e 100%);
            color: #e0e0e0;
            padding: 20px;
        }}
        .container {{ max-width: 1800px; margin: 0 auto; }}
        h1 {{
            text-align: center;
            font-size: 32px;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .subtitle {{ text-align: center; color: #888; margin-bottom: 30px; }}
        .controls {{
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            gap: 20px;
            align-items: center;
            justify-content: center;
        }}
        select {{
            padding: 10px 15px;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 6px;
            color: #e0e0e0;
            font-size: 14px;
        }}
        .chart-container {{
            background: rgba(255, 255, 255, 0.03);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .comparison-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Top 50 vs Overall Network Comparison</h1>
        <p class="subtitle">Does elite composition differ from the overall network?</p>
        
        <div class="controls">
            <select id="periodSelect" onchange="updateCharts()">
                <option value="Pre-Crimea">Pre-Crimea</option>
                <option value="Post-Crimea">Post-Crimea</option>
                <option value="COVID">COVID</option>
                <option value="War">War</option>
            </select>
            
            <select id="attributeSelect" onchange="updateCharts()">
                <option value="sector">Sector</option>
                <option value="state_private">State/Private</option>
                <option value="actor_type">Actor Type</option>
                <option value="jurisdiction">Jurisdiction</option>
            </select>
        </div>
        
        <div class="comparison-grid">
            <div class="chart-container">
                <div id="overallChart"></div>
            </div>
            <div class="chart-container">
                <div id="top50Chart"></div>
            </div>
        </div>
        
        <div class="chart-container">
            <div id="comparisonBar"></div>
        </div>
    </div>
    
    <script>
        const DATA = {network_json};
        
        function updateCharts() {{
            const period = document.getElementById('periodSelect').value;
            const attribute = document.getElementById('attributeSelect').value;
            
            // Get period nodes
            const periodNodes = DATA.nodes.filter(n => n.periods.includes(period));
            const top50 = periodNodes
                .sort((a, b) => (b.period_counts[period] || 0) - (a.period_counts[period] || 0))
                .slice(0, 50);
            
            // Count attributes
            const overallCounts = {{}};
            const top50Counts = {{}};
            
            periodNodes.forEach(n => {{
                const val = n[attribute];
                overallCounts[val] = (overallCounts[val] || 0) + 1;
            }});
            
            top50.forEach(n => {{
                const val = n[attribute];
                top50Counts[val] = (top50Counts[val] || 0) + 1;
            }});
            
            // Overall pie chart
            const overallData = [{{
                labels: Object.keys(overallCounts),
                values: Object.values(overallCounts),
                type: 'pie',
                hole: 0.4,
                textinfo: 'label+percent',
                marker: {{ colors: ['#667eea', '#f6ad55', '#48bb78', '#ed64a6', '#fc8181',
                                    '#4299e1', '#9f7aea', '#38b2ac', '#ed8936', '#ecc94b'] }}
            }}];
            
            Plotly.newPlot('overallChart', overallData, {{
                title: `Overall Network (${{periodNodes.length}} entities)`,
                paper_bgcolor: 'rgba(0,0,0,0)',
                font: {{ color: '#e0e0e0' }}
            }}, {{responsive: true}});
            
            // Top 50 pie chart
            const top50Data = [{{
                labels: Object.keys(top50Counts),
                values: Object.values(top50Counts),
                type: 'pie',
                hole: 0.4,
                textinfo: 'label+percent',
                marker: {{ colors: ['#667eea', '#f6ad55', '#48bb78', '#ed64a6', '#fc8181',
                                    '#4299e1', '#9f7aea', '#38b2ac', '#ed8936', '#ecc94b'] }}
            }}];
            
            Plotly.newPlot('top50Chart', top50Data, {{
                title: 'Top 50 Actors',
                paper_bgcolor: 'rgba(0,0,0,0)',
                font: {{ color: '#e0e0e0' }}
            }}, {{responsive: true}});
            
            // Comparison bar chart
            const allValues = [...new Set([...Object.keys(overallCounts), ...Object.keys(top50Counts)])];
            
            const overallPcts = allValues.map(v => 
                (overallCounts[v] || 0) / periodNodes.length * 100
            );
            const top50Pcts = allValues.map(v => 
                (top50Counts[v] || 0) / 50 * 100
            );
            
            const comparisonData = [
                {{ x: allValues, y: overallPcts, name: 'Overall', type: 'bar' }},
                {{ x: allValues, y: top50Pcts, name: 'Top 50', type: 'bar' }}
            ];
            
            Plotly.newPlot('comparisonBar', comparisonData, {{
                title: 'Side-by-Side Comparison',
                xaxis: {{ title: attribute.replace('_', ' ').toUpperCase() }},
                yaxis: {{ title: 'Percentage (%)' }},
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0.2)',
                font: {{ color: '#e0e0e0' }},
                barmode: 'group'
            }}, {{responsive: true}});
        }}
        
        updateCharts();
    </script>
</body>
</html>
'''

with open('interactive_visuals/2_top50_comparison.html', 'w', encoding='utf-8') as f:
    f.write(html_2)
print("  ✓ Created: interactive_visuals/2_top50_comparison.html")

print("\n" + "="*80)
print("✅ Created interactive HTML visualizations!")
print("   Open files in interactive_visuals/ directory")
print("="*80)



