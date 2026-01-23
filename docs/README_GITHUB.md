# Russian Elite Network Analysis - Interactive Dashboard

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live%20Demo-blue?style=for-the-badge&logo=github)](https://yourusername.github.io/ScrapeTestSNA/)

An interactive web dashboard for exploring Russian elite networks across four critical geopolitical periods (2012-2024). This project analyzes the RDIF/Dmitriev network structure, revealing stable domestic cores and flexible international peripheries.

## 🌐 Live Demo

Visit the interactive dashboard: **[https://yourusername.github.io/ScrapeTestSNA/](https://yourusername.github.io/ScrapeTestSNA/)**

## 📊 Features

- **Interactive Period Switching**: Navigate between Pre-Crimea, Post-Crimea, COVID-19, and War periods
- **Semantic Community Analysis**: Visualize meaningful community structures with interpretable labels
- **Download Capabilities**: Download individual visualizations and comprehensive reports
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Real-time Statistics**: View network metrics for each period
- **Keyboard Navigation**: Use arrow keys to switch between periods

## 🎯 Key Insights

### Network Structure Evolution
- **Pre-Crimea (2012-2014)**: 67 entities, 166 connections, 6 communities
- **Post-Crimea (2014-2020)**: 240 entities, 1,162 connections, 6 communities  
- **COVID-19 (2020-2022)**: 75 entities, 163 connections, 6 communities
- **War Period (2022-2024)**: 57 entities, 193 connections, 3 communities

### Research Findings
1. **Institutional Persistence**: Core financial institutions maintain central positions across all periods
2. **Adaptive Clustering**: New communities emerge in response to external shocks
3. **Network Flexibility**: International partnerships adapt while domestic core remains stable
4. **Bridge Actors**: Dmitriev and RDIF consistently act as institutional brokers

## 🛠️ Technical Implementation

### Visualization Technology
- **Plotly.js**: Interactive network visualizations
- **NetworkX**: Community detection and network analysis
- **Louvain Algorithm**: Community structure identification
- **Semantic Labeling**: Meaningful community interpretation

### Data Processing
- **Named Entity Recognition**: Automated entity extraction
- **Fuzzy Matching**: Entity deduplication and standardization
- **Temporal Analysis**: Cross-period network evolution
- **Co-occurrence Networks**: Entity relationship mapping

## 📁 Repository Structure

```
ScrapeTestSNA/
├── index.html                              # Main dashboard
├── semantic_communities_pre_crimea.html    # Pre-Crimea visualization
├── semantic_communities_post_crimea.html   # Post-Crimea visualization
├── semantic_communities_covid.html         # COVID period visualization
├── semantic_communities_war.html           # War period visualization
├── community_insights_report.html          # Comprehensive analysis report
├── community_evolution_analysis.html       # Cross-period evolution
├── README.md                              # This file
└── assets/                                # Additional resources
    ├── network_flow_diagram.png
    ├── network_density_analysis.png
    └── stylized_network_core_periphery.png
```

## 🚀 Getting Started

### View Online
Simply visit the [live demo](https://yourusername.github.io/ScrapeTestSNA/) to explore the interactive dashboard.

### Run Locally
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ScrapeTestSNA.git
   cd ScrapeTestSNA
   ```

2. Open `index.html` in your web browser or serve with a local server:
   ```bash
   python -m http.server 8000
   # Then visit http://localhost:8000
   ```

## 📖 Research Context

This analysis is part of ongoing research on Russian elite networks conducted at the Centre for East European and International Studies (ZOiS). The project examines how institutional networks adapt to geopolitical pressures while maintaining core stability.

### Key Research Questions
- How do elite networks maintain stability during crises?
- What role do institutional brokers play in network adaptation?
- How do international partnerships evolve under sanctions and conflicts?

## 👥 Research Team

- **Principal Investigator**: Aran Bagdasarian (Harvard College)
- **Supervisor**: Dr. Sebastian Hoppe (ZOiS Berlin)
- **Institution**: Centre for East European and International Studies

## 📄 Citation

If you use this work in your research, please cite:

```bibtex
@misc{bagdasarian2024russian,
  title={Russian Elite Network Analysis: Stability and Adaptation in the RDIF Network},
  author={Bagdasarian, Aran and Hoppe, Sebastian},
  year={2024},
  institution={Centre for East European and International Studies (ZOiS)},
  url={https://github.com/yourusername/ScrapeTestSNA}
}
```

## 🔄 Updates

- **Latest**: Enhanced semantic community labeling and interactive dashboard
- **Previous**: Core-periphery structure analysis and temporal evolution tracking

## 📧 Contact

For questions about this research:
- **Aran Bagdasarian**: abagdasarian@college.harvard.edu
- **Dr. Sebastian Hoppe**: sebastian.hoppe@zois-berlin.de

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*This research contributes to understanding elite network dynamics in authoritarian contexts and the role of institutional brokers in maintaining stability during geopolitical crises.*
