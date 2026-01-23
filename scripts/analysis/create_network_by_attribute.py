#!/usr/bin/env python3
"""
Create separate network visualizations for each attribute
"""

import json

with open('network_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

network_json = json.dumps(data, ensure_ascii=False)

# ============================================================================
# NETWORK BY SECTOR
# ============================================================================
print("Creating sector-based network visualization...")

html_sector = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Network by Sector</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0f0f1e 0%, #1a1a2e 100%);
            color: #e0e0e0;
            overflow: hidden;
        }}
        .container {{ display: flex; flex-direction: column; height: 100vh; }}
        header {{
            padding: 15px 40px;
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        h1 {{
            font-size: 22px;
            font-weight: 600;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .content {{ display: flex; flex: 1; overflow: hidden; }}
        #network {{ flex: 1; position: relative; background: rgba(0, 0, 0, 0.2); }}
        svg {{ width: 100%; height: 100%; }}
        .sidebar {{
            width: 300px;
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(10px);
            border-left: 1px solid rgba(255, 255, 255, 0.1);
            padding: 20px;
            overflow-y: auto;
        }}
        .section {{ margin-bottom: 25px; }}
        .section-title {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #667eea;
            margin-bottom: 12px;
            font-weight: 600;
        }}
        .filter-btn {{
            padding: 6px 12px;
            margin: 4px;
            font-size: 10px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            background: rgba(255, 255, 255, 0.05);
            color: #e0e0e0;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-block;
        }}
        .filter-btn:hover {{ background: rgba(255, 255, 255, 0.1); }}
        .filter-btn.active {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-color: transparent;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 10px;
            color: #aaa;
            margin: 5px 0;
        }}
        .legend-color {{ width: 10px; height: 10px; border-radius: 50%; }}
        .link {{ stroke: rgba(255, 255, 255, 0.08); stroke-width: 1; }}
        .link.highlighted {{ stroke: rgba(102, 126, 234, 0.6); stroke-width: 2; }}
        .node circle {{
            stroke: rgba(0, 0, 0, 0.5);
            stroke-width: 1.5;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .node:hover circle {{ stroke: #fff; stroke-width: 3; filter: brightness(1.3); }}
        .node.highlighted circle {{ stroke: #667eea; stroke-width: 3; }}
        .node.dimmed circle {{ opacity: 0.15; }}
        .node text {{
            font-size: 8px;
            fill: #e0e0e0;
            pointer-events: none;
            text-shadow: 0 0 3px rgba(0, 0, 0, 0.8);
        }}
        .tooltip {{
            position: absolute;
            background: rgba(0, 0, 0, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 10px 14px;
            border-radius: 6px;
            pointer-events: none;
            opacity: 0;
            font-size: 11px;
            max-width: 250px;
            z-index: 1000;
        }}
        .tooltip.visible {{ opacity: 1; }}
        .stats {{
            background: rgba(255, 255, 255, 0.05);
            padding: 12px;
            border-radius: 6px;
            font-size: 11px;
        }}
        .stat-row {{
            display: flex;
            justify-content: space-between;
            padding: 4px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎯 Network Analysis by Sector</h1>
        </header>
        <div class="content">
            <div id="network"></div>
            <div class="sidebar">
                <div class="section">
                    <div class="section-title">Period</div>
                    <button class="filter-btn active" onclick="filterPeriod('all')">All</button>
                    <button class="filter-btn" onclick="filterPeriod('Pre-Crimea')">Pre-Crimea</button>
                    <button class="filter-btn" onclick="filterPeriod('Post-Crimea')">Post-Crimea</button>
                    <button class="filter-btn" onclick="filterPeriod('COVID')">COVID</button>
                    <button class="filter-btn" onclick="filterPeriod('War')">War</button>
                </div>
                
                <div class="section">
                    <div class="section-title">Filter by Sector</div>
                    <button class="filter-btn active" onclick="filterSector('all')">All Sectors</button>
                    <div id="sector-filters"></div>
                </div>
                
                <div class="section">
                    <div class="section-title">Network Stats</div>
                    <div class="stats">
                        <div class="stat-row">
                            <span>Visible Nodes:</span>
                            <span id="stat-nodes">-</span>
                        </div>
                        <div class="stat-row">
                            <span>Visible Edges:</span>
                            <span id="stat-edges">-</span>
                        </div>
                        <div class="stat-row">
                            <span>Avg Degree:</span>
                            <span id="stat-degree">-</span>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">Sector Legend</div>
                    <div id="legend"></div>
                </div>
            </div>
        </div>
    </div>
    <div class="tooltip"></div>
    
    <script>
        const DATA = {network_json};
        const sectorColors = {{
            'Finance': '#667eea', 'Government': '#f6ad55', 'Health': '#48bb78',
            'Diplomacy': '#ed64a6', 'Energy': '#fc8181', 'Tech': '#4299e1',
            'Business': '#9f7aea', 'Education': '#38b2ac', 'Production': '#ed8936',
            'Infrastructure': '#ecc94b', 'Military': '#e53e3e',
            'Telecommunication': '#805ad5', 'Politics': '#d69e2e', 'Unknown': '#718096'
        }};
        
        let currentPeriod = 'all';
        let currentSector = 'all';
        let simulation, svg, g, link, node, tooltip;
        
        function init() {{
            // Setup D3
            const container = document.getElementById('network');
            const width = container.clientWidth;
            const height = container.clientHeight;
            
            svg = d3.select('#network').append('svg')
                .attr('width', width).attr('height', height);
            
            g = svg.append('g');
            svg.call(d3.zoom()
                .scaleExtent([0.1, 10])
                .on('zoom', (event) => g.attr('transform', event.transform)));
            
            tooltip = d3.select('.tooltip');
            
            simulation = d3.forceSimulation()
                .force('link', d3.forceLink().id(d => d.id).distance(250))
                .force('charge', d3.forceManyBody().strength(-800))
                .force('center', d3.forceCenter(width / 2, height / 2))
                .force('collision', d3.forceCollide().radius(5))
                .alphaDecay(0.02).velocityDecay(0.4);
            
            link = g.append('g').selectAll('.link');
            node = g.append('g').selectAll('.node');
            
            // Create sector filters
            const sectors = [...new Set(DATA.nodes.map(n => n.sector))].sort();
            const filterDiv = document.getElementById('sector-filters');
            sectors.forEach(sector => {{
                const btn = document.createElement('button');
                btn.className = 'filter-btn';
                btn.textContent = sector;
                btn.onclick = () => filterSector(sector);
                filterDiv.appendChild(btn);
            }});
            
            // Create legend
            const legendDiv = document.getElementById('legend');
            sectors.forEach(sector => {{
                legendDiv.innerHTML += `
                    <div class="legend-item">
                        <div class="legend-color" style="background: ${{sectorColors[sector]}}"></div>
                        <span>${{sector}}</span>
                    </div>
                `;
            }});
            
            updateVisualization();
        }}
        
        function filterPeriod(period) {{
            currentPeriod = period;
            document.querySelectorAll('.sidebar .filter-btn').forEach(b => {{
                if (b.textContent === period || (period === 'all' && b.textContent === 'All')) {{
                    b.classList.add('active');
                }} else if (!b.textContent.includes('Sector')) {{
                    b.classList.remove('active');
                }}
            }});
            updateVisualization();
        }}
        
        function filterSector(sector) {{
            currentSector = sector;
            document.querySelectorAll('#sector-filters .filter-btn, .sidebar > div:nth-child(2) > .filter-btn:first-child')
                .forEach(b => {{
                    if (b.textContent === sector || (sector === 'all' && b.textContent === 'All Sectors')) {{
                        b.classList.add('active');
                    }} else {{
                        b.classList.remove('active');
                    }}
                }});
            updateVisualization();
        }}
        
        function updateVisualization() {{
            let filteredNodes = currentPeriod === 'all'
                ? DATA.nodes
                : DATA.nodes.filter(n => n.periods.includes(currentPeriod));
            
            if (currentSector !== 'all') {{
                filteredNodes = filteredNodes.filter(n => n.sector === currentSector);
            }}
            
            const nodeIds = new Set(filteredNodes.map(n => n.id));
            const filteredEdges = DATA.edges.filter(e =>
                nodeIds.has(e.source.id || e.source) && nodeIds.has(e.target.id || e.target) &&
                (currentPeriod === 'all' || e.periods.includes(currentPeriod))
            );
            
            // Update stats
            document.getElementById('stat-nodes').textContent = filteredNodes.length;
            document.getElementById('stat-edges').textContent = filteredEdges.length;
            document.getElementById('stat-degree').textContent =
                filteredNodes.length > 0 ? (filteredEdges.length * 2 / filteredNodes.length).toFixed(1) : 0;
            
            // Update links
            link = link.data(filteredEdges, d => `${{d.source.id || d.source}}-${{d.target.id || d.target}}`)
                .join(enter => enter.append('line').attr('class', 'link'));
            
            // Update nodes
            node = node.data(filteredNodes, d => d.id)
                .join(enter => {{
                    const g = enter.append('g').attr('class', 'node')
                        .call(d3.drag()
                            .on('start', dragStart)
                            .on('drag', dragging)
                            .on('end', dragEnd));
                    
                    g.append('circle')
                        .attr('r', d => Math.max(1, Math.sqrt(d.mentions) * 0.12))
                        .attr('fill', d => sectorColors[d.sector]);
                    
                    g.append('text')
                        .attr('dx', d => Math.max(1, Math.sqrt(d.mentions) * 0.12) + 3)
                        .attr('dy', 3)
                        .text(d => d.label.length > 25 ? d.label.substring(0, 22) + '...' : d.label)
                        .style('opacity', d => d.mentions > 10000 ? 1 : 0);
                    
                    g.on('mouseover', (e, d) => {{
                        tooltip.html(`
                            <strong>${{d.label}}</strong><br>
                            Sector: ${{d.sector}}<br>
                            State/Private: ${{d.state_private}}<br>
                            Type: ${{d.actor_type}}<br>
                            Mentions: ${{d.mentions.toLocaleString()}}
                        `).style('left', (e.pageX + 15) + 'px')
                          .style('top', (e.pageY - 28) + 'px')
                          .classed('visible', true);
                    }}).on('mouseout', () => tooltip.classed('visible', false));
                    
                    return g;
                }});
            
            simulation.nodes(filteredNodes);
            simulation.force('link').links(filteredEdges);
            simulation.alpha(1).restart();
            
            let tickCount = 0;
            simulation.on('tick', () => {{
                if (tickCount++ % 2 === 0) {{
                    link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
                        .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
                    node.attr('transform', d => `translate(${{d.x}},${{d.y}})`);
                }}
            }});
        }}
        
        function dragStart(event) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }}
        
        function dragging(event) {{
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }}
        
        function dragEnd(event) {{
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }}
        
        init();
    </script>
</body>
</html>
'''

with open('interactive_visuals/3_network_by_sector.html', 'w', encoding='utf-8') as f:
    f.write(html_sector)
print("  ✓ Created: interactive_visuals/3_network_by_sector.html")

# Create similar visualizations for other attributes...
print("\n✅ Created network visualization by sector!")
print("   Open interactive_visuals/3_network_by_sector.html")



