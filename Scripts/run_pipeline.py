#!/usr/bin/env python3
"""
Orchestrator script to run the stock analysis pipeline.
1. Fetches the latest stock names list using getstocklist.py
2. Fetches P/E and PEG ratios using get_pe_ratios.py
"""

import sys
import os
import subprocess
from datetime import date
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def run_cmd(args: list, cwd: str = None) -> int:
    """Run a command line list and return the exit status code."""
    print(f"🚀 Executing: {' '.join(args)}")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    process = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=cwd,
        env=env,
    )
    
    # Print the output in real-time
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())
            
    rc = process.poll()
    return rc

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run the full stock analysis pipeline.")
    parser.add_argument("--output-csv", help="Custom path for output PEG ratios CSV.")
    
    args = parser.parse_args()
    
    scripts_dir = Path(__file__).parent.resolve()
    
    print("=" * 60)
    print(f"STARTING STOCK ANALYSIS PIPELINE: {date.today().isoformat()}")
    print("=" * 60)
    
    # 1. Run getstocklist.py to scrape the latest bearish crossover stocks
    get_list_cmd = [sys.executable, str(scripts_dir / "getstocklist.py")]
    
    rc = run_cmd(get_list_cmd)
    if rc != 0:
        print(f"❌ Error: getstocklist.py failed with code {rc}")
        sys.exit(rc)
        
    print("\n" + "=" * 60)
    print("STEP 2: FETCHING P/E AND PEG RATIOS")
    print("=" * 60)
    
    # 2. Run get_pe_ratios.py to fetch P/E & PEG metrics and compute values
    get_pe_cmd = [sys.executable, str(scripts_dir / "get_pe_ratios.py")]
    if args.output_csv:
        get_pe_cmd.extend(["--output", args.output_csv])
        
    rc = run_cmd(get_pe_cmd)
    if rc != 0:
        print(f"❌ Error: get_pe_ratios.py failed with code {rc}")
        sys.exit(rc)
        
    repo_root = scripts_dir.parent
    csv_path = Path(args.output_csv) if args.output_csv else (repo_root / "output" / f"peg_ratios_{date.today().isoformat()}.csv")
    md_path = csv_path.with_suffix(".md")
    
    print("\n" + "=" * 60)
    print("STEP 3: GENERATING MARKDOWN REPORT")
    print("=" * 60)
    print(f"📂 Converting CSV results from: {csv_path.resolve()}")
    
    if csv_path.exists():
        try:
            import csv
            with open(csv_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            if rows:
                headers = ["Company Name", "Stock P/E", "Dividend Yield (%)", "Profit Growth 3Y (%)", "PEG Ratio 3Y", "PEGY Ratio 3Y", "Market Cap (Cr)", "VLRT Score", "S-Curve Stage"]
                
                md_lines = []
                md_lines.append(f"# Stock Analysis Report - {date.today().isoformat()}")
                md_lines.append(f"\nGenerated automatically by the stock analysis pipeline with Quant VLRT & S-Curve Analysis.")
                md_lines.append(f"\n| {' | '.join(headers)} |")
                md_lines.append(f"| {' | '.join(['---'] * len(headers))} |")
                
                for r in rows:
                    vlrt_val = r.get("VLRT Score", "")
                    if not vlrt_val or vlrt_val == "N/A":
                        from get_pe_ratios import compute_vlrt_score
                        v_res = compute_vlrt_score(r.get("PEG Ratio 3Y", ""), r.get("PEGY Ratio 3Y", ""), r.get("Market Cap (Cr)", ""), r.get("Profit Growth 3Y (%)", ""), r.get("Dividend Yield (%)", ""), r.get("Stock P/E", ""))
                        vlrt_val = str(v_res["score"])

                    scurve_badge = r.get("S-Curve Stage", "")
                    if not scurve_badge or scurve_badge == "N/A":
                        from get_pe_ratios import compute_s_curve_stage
                        sc_res = compute_s_curve_stage(r.get("Profit Growth 3Y (%)", ""), r.get("PEG Ratio 3Y", ""), r.get("Stock P/E", ""))
                        scurve_badge = sc_res["badge"]

                    row_vals = [
                        r.get("Company Name", ""),
                        r.get("Stock P/E", ""),
                        r.get("Dividend Yield (%)", ""),
                        r.get("Profit Growth 3Y (%)", ""),
                        r.get("PEG Ratio 3Y", ""),
                        r.get("PEGY Ratio 3Y", ""),
                        r.get("Market Cap (Cr)", ""),
                        f"{vlrt_val}/10",
                        scurve_badge
                    ]
                    md_lines.append(f"| {' | '.join(row_vals)} |")
                
                md_content = "\n".join(md_lines) + "\n"
                md_path.write_text(md_content, encoding="utf-8")
                print(f"💾 Saved markdown report to: {md_path.resolve()}")
                
                # 3.1. Generate HTML Dashboard for GitHub Pages
                repo_root = scripts_dir.parent
                html_path = repo_root / "index.html"
                print(f"📂 Generating HTML dashboard for GitHub Pages...")
                
                # Compute stats
                valid_pes = []
                vlrt_scores = []
                for r in rows:
                    try:
                        pe_val = float(r.get("Stock P/E", "").replace(",", "").strip())
                        valid_pes.append(pe_val)
                    except ValueError:
                        pass

                    try:
                        v_val = float(r.get("VLRT Score", "").strip())
                        vlrt_scores.append(v_val)
                    except ValueError:
                        pass
                
                avg_pe = f"{sum(valid_pes) / len(valid_pes):.2f}" if valid_pes else "N/A"
                avg_vlrt = f"{sum(vlrt_scores) / len(vlrt_scores):.1f}/10" if vlrt_scores else "N/A"
                
                # Find top pick by min PEG Ratio 3Y
                min_peg = float('inf')
                top_pick = "N/A"
                for r in rows:
                    try:
                        peg_val = float(r.get("PEG Ratio 3Y", "").strip())
                        if peg_val < min_peg:
                            min_peg = peg_val
                            top_pick = r.get("Company Name", "")
                    except ValueError:
                        pass
                
                if top_pick == "N/A" and rows:
                    top_pick = rows[0].get("Company Name", "")
                    
                # Build rows
                table_rows_html = []
                for r in rows:
                    company = r.get("Company Name", "")
                    pe = r.get("Stock P/E", "")
                    div_yield = r.get("Dividend Yield (%)", "")
                    growth = r.get("Profit Growth 3Y (%)", "")
                    peg = r.get("PEG Ratio 3Y", "")
                    pegy = r.get("PEGY Ratio 3Y", "")
                    mcap = r.get("Market Cap (Cr)", "")
                    
                    # Compute VLRT
                    vlrt_score_str = r.get("VLRT Score", "")
                    vlrt_breakdown = r.get("VLRT Breakdown", "")
                    if not vlrt_score_str or vlrt_score_str == "N/A":
                        from get_pe_ratios import compute_vlrt_score
                        v_res = compute_vlrt_score(peg, pegy, mcap, growth, div_yield, pe)
                        vlrt_score_val = v_res["score"]
                        vlrt_badge_cls = v_res["badge_class"]
                        vlrt_breakdown = v_res["breakdown"]
                    else:
                        vlrt_score_val = float(vlrt_score_str)
                        if vlrt_score_val >= 8.0:
                            vlrt_badge_cls = "badge-success"
                        elif vlrt_score_val >= 6.0:
                            vlrt_badge_cls = "badge-warning"
                        else:
                            vlrt_badge_cls = "badge-danger"

                    # Compute S-Curve
                    scurve_badge = r.get("S-Curve Stage", "")
                    if not scurve_badge or scurve_badge == "N/A":
                        from get_pe_ratios import compute_s_curve_stage
                        sc_res = compute_s_curve_stage(growth, peg, pe)
                        scurve_badge = sc_res["badge"]
                        scurve_cls = sc_res["badge_class"]
                    else:
                        if "Inflection" in scurve_badge or "Accelerating" in scurve_badge:
                            scurve_cls = "badge-success"
                        elif "Mature" in scurve_badge:
                            scurve_cls = "badge-warning"
                        else:
                            scurve_cls = "badge-danger"

                    # Determine recommendation and badge
                    rec_str = "HOLD"
                    badge_class = "badge-warning"
                    
                    try:
                        peg_f = float(peg.strip())
                        pegy_f = float(pegy.strip())
                        if peg_f < 0.6 and pegy_f < 0.6:
                            rec_str = "STRONG BUY"
                            badge_class = "badge-success"
                        elif peg_f < 1.0:
                            rec_str = "BUY"
                            badge_class = "badge-success"
                        elif peg_f >= 1.0 and peg_f <= 2.0:
                            rec_str = "HOLD"
                            badge_class = "badge-warning"
                        else:
                            rec_str = "SELL"
                            badge_class = "badge-danger"
                    except ValueError:
                        if "Negative" in peg or "Negative" in pegy:
                            rec_str = "SELL"
                            badge_class = "badge-danger"
                        else:
                            rec_str = "NEUTRAL"
                            badge_class = "badge-neutral"
                    
                    try:
                        pe_f = float(pe.replace(",", "").strip())
                        if pe_f > 100:
                            rec_str = "SELL"
                            badge_class = "badge-danger"
                    except ValueError:
                        pass
                    
                    row_html = f"""                    <tr>
                        <td style="font-weight: 500;">{company}</td>
                        <td>{pe}</td>
                        <td>{div_yield}</td>
                        <td>{growth}</td>
                        <td>{peg}</td>
                        <td>{pegy}</td>
                        <td>{mcap}</td>
                        <td><span class="badge {vlrt_badge_cls}" title="Breakdown: {vlrt_breakdown}">⚡ {vlrt_score_val}/10</span></td>
                        <td><span class="badge {scurve_cls}">{scurve_badge}</span></td>
                        <td><span class="badge {badge_class}">{rec_str}</span></td>
                    </tr>"""
                    table_rows_html.append(row_html)
                    
                table_rows_str = "\n".join(table_rows_html)
                
                # HTML Template
                html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stock Screener Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --primary: #3b82f6;
            --primary-glow: rgba(59, 130, 246, 0.15);
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --border: #334155;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-main);
            padding: 2rem 1.5rem;
            line-height: 1.5;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        header {{
            margin-bottom: 2.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }}
        
        h1 {{
            font-family: 'Outfit', sans-serif;
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .timestamp {{
            color: var(--text-muted);
            font-size: 0.9rem;
            background: var(--bg-card);
            padding: 0.5rem 1rem;
            border-radius: 50px;
            border: 1px solid var(--border);
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2.5rem;
        }}
        
        .card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }}
        
        .card:hover {{
            transform: translateY(-2px);
            border-color: var(--primary);
        }}
        
        .card-title {{
            color: var(--text-muted);
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }}
        
        .card-value {{
            font-size: 1.8rem;
            font-weight: 700;
            font-family: 'Outfit', sans-serif;
        }}
        
        .search-container {{
            margin-bottom: 1.5rem;
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }}
        
        .search-input {{
            flex: 1;
            min-width: 250px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-main);
            padding: 0.75rem 1.25rem;
            border-radius: 12px;
            font-size: 0.95rem;
            outline: none;
            transition: border-color 0.2s ease;
        }}
        
        .search-input:focus {{
            border-color: var(--primary);
            box-shadow: 0 0 0 3px var(--primary-glow);
        }}
        
        .sort-select {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-main);
            padding: 0.75rem 1.25rem;
            border-radius: 12px;
            font-size: 0.95rem;
            outline: none;
            cursor: pointer;
            transition: border-color 0.2s ease;
        }}
        
        .sort-select:focus {{
            border-color: var(--primary);
            box-shadow: 0 0 0 3px var(--primary-glow);
        }}
        
        .table-container {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow-x: auto;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            margin-bottom: 2.5rem;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}
        
        th, td {{
            padding: 1rem 1.25rem;
            border-bottom: 1px solid var(--border);
        }}
        
        th {{
            background-color: rgba(15, 23, 42, 0.3);
            color: var(--text-muted);
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            cursor: pointer;
            user-select: none;
            transition: color 0.2s ease, background-color 0.2s ease;
        }}
        
        th:hover {{
            color: var(--text-main);
            background-color: rgba(59, 130, 246, 0.1);
        }}

        th .sort-icon {{
            display: inline-block;
            margin-left: 0.35rem;
            opacity: 0.4;
            font-size: 0.75rem;
            transition: opacity 0.2s ease;
        }}

        th.sorted-asc .sort-icon, th.sorted-desc .sort-icon {{
            opacity: 1;
            color: var(--primary);
        }}
        
        tr:last-child td {{
            border-bottom: none;
        }}
        
        tr:hover td {{
            background-color: rgba(255, 255, 255, 0.02);
        }}
        
        .badge {{
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.75rem;
            border-radius: 50px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.02em;
        }}
        
        .badge-success {{
            background: rgba(16, 185, 129, 0.15);
            color: var(--success);
        }}
        
        .badge-warning {{
            background: rgba(245, 158, 11, 0.15);
            color: var(--warning);
        }}
        
        .badge-danger {{
            background: rgba(239, 68, 68, 0.15);
            color: var(--danger);
        }}
        
        .badge-neutral {{
            background: rgba(148, 163, 184, 0.15);
            color: var(--text-muted);
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 1rem;
            }}
            h1 {{
                font-size: 2rem;
            }}
            th, td {{
                padding: 0.75rem 1rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>Stock Value Screener</h1>
                <p style="color: var(--text-muted); margin-top: 0.25rem;">Bearish Crossover Screener & Value Metrics</p>
            </div>
            <div class="timestamp">Last Updated: {date.today().isoformat()}</div>
        </header>
        
        <div class="stats-grid">
            <div class="card">
                <div class="card-title">Total Stocks Analyzed</div>
                <div class="card-value">{len(rows)}</div>
            </div>
            <div class="card">
                <div class="card-title">Top Value Pick</div>
                <div class="card-value" style="color: var(--success);">{top_pick}</div>
            </div>
            <div class="card">
                <div class="card-title">Average P/E Ratio</div>
                <div class="card-value">{avg_pe}</div>
            </div>
            <div class="card">
                <div class="card-title">Average VLRT Score</div>
                <div class="card-value" style="color: var(--primary);">{avg_vlrt}</div>
            </div>
        </div>
        
        <div class="search-container">
            <input type="text" id="searchInput" class="search-input" placeholder="Search by company name or ticker..." onkeyup="filterTable()">
            <select id="sortSelect" class="sort-select" onchange="handleSortSelect(this.value)">
                <option value="">Sort By: Default</option>
                <option value="name-asc">Company Name (A-Z)</option>
                <option value="vlrt-desc">VLRT Score (High to Low)</option>
                <option value="pe-asc">Stock P/E (Low to High)</option>
                <option value="pe-desc">Stock P/E (High to Low)</option>
                <option value="growth-desc">3Y Profit Growth (High to Low)</option>
                <option value="peg-asc">PEG Ratio 3Y (Low to High)</option>
                <option value="pegy-asc">PEGY Ratio 3Y (Low to High)</option>
                <option value="mcap-desc">Market Cap (High to Low)</option>
                <option value="rec-desc">Recommendation (Strong Buy First)</option>
            </select>
        </div>
        
        <div class="table-container">
            <table id="stockTable">
                <thead>
                    <tr>
                        <th onclick="sortTable(0)">Company Name <span class="sort-icon">↕</span></th>
                        <th onclick="sortTable(1)">Stock P/E <span class="sort-icon">↕</span></th>
                        <th onclick="sortTable(2)">Div Yield (%) <span class="sort-icon">↕</span></th>
                        <th onclick="sortTable(3)">3Y Growth (%) <span class="sort-icon">↕</span></th>
                        <th onclick="sortTable(4)">PEG Ratio 3Y <span class="sort-icon">↕</span></th>
                        <th onclick="sortTable(5)">PEGY Ratio 3Y <span class="sort-icon">↕</span></th>
                        <th onclick="sortTable(6)">Market Cap (Cr) <span class="sort-icon">↕</span></th>
                        <th onclick="sortTable(7)">VLRT Score <span class="sort-icon">↕</span></th>
                        <th onclick="sortTable(8)">S-Curve Stage <span class="sort-icon">↕</span></th>
                        <th onclick="sortTable(9)">Recommendation <span class="sort-icon">↕</span></th>
                    </tr>
                </thead>
                <tbody>
{table_rows_str}
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        function filterTable() {{
            const input = document.getElementById("searchInput");
            const filter = input.value.toUpperCase();
            const table = document.getElementById("stockTable");
            const tr = table.getElementsByTagName("tr");
            
            for (let i = 1; i < tr.length; i++) {{
                const td = tr[i].getElementsByTagName("td")[0];
                if (td) {{
                    const txtValue = td.textContent || td.innerText;
                    if (txtValue.toUpperCase().indexOf(filter) > -1) {{
                        tr[i].style.display = "";
                    }} else {{
                        tr[i].style.display = "none";
                    }}
                }}
            }}
        }}
        
        let currentSortCol = -1;
        let currentSortDir = 'asc';

        const recPriority = {{
            'STRONG BUY': 4,
            'BUY': 3,
            'HOLD': 2,
            'NEUTRAL': 1,
            'SELL': 0
        }};

        function parseCellVal(val, colIndex) {{
            if (!val) return null;
            let clean = val.trim();
            if (clean === 'N/A' || clean === '' || clean.includes('Negative')) return null;
            if (colIndex === 9) {{
                return recPriority[clean.toUpperCase()] !== undefined ? recPriority[clean.toUpperCase()] : -1;
            }}
            let num = parseFloat(clean.replace(/,/g, '').replace(/⚡/g, '').replace(/\/10/g, ''));
            return isNaN(num) ? clean.toLowerCase() : num;
        }}

        function sortTable(n, forceDir = null) {{
            const table = document.getElementById("stockTable");
            const tbody = table.querySelector("tbody");
            const rows = Array.from(tbody.querySelectorAll("tr"));
            const headers = table.querySelectorAll("th");

            if (forceDir) {{
                currentSortDir = forceDir;
            }} else if (currentSortCol === n) {{
                currentSortDir = currentSortDir === 'asc' ? 'desc' : 'asc';
            }} else {{
                currentSortDir = 'asc';
            }}
            currentSortCol = n;

            headers.forEach((th, idx) => {{
                th.classList.remove('sorted-asc', 'sorted-desc');
                const icon = th.querySelector('.sort-icon');
                if (icon) {{
                    if (idx === n) {{
                        icon.textContent = currentSortDir === 'asc' ? '▲' : '▼';
                        th.classList.add(currentSortDir === 'asc' ? 'sorted-asc' : 'sorted-desc');
                    }} else {{
                        icon.textContent = '↕';
                    }}
                }}
            }});

            rows.sort((a, b) => {{
                const aCell = a.getElementsByTagName("td")[n];
                const bCell = b.getElementsByTagName("td")[n];
                const aVal = parseCellVal(aCell ? aCell.textContent : '', n);
                const bVal = parseCellVal(bCell ? bCell.textContent : '', n);

                if (aVal === null && bVal === null) return 0;
                if (aVal === null) return 1;
                if (bVal === null) return -1;

                if (typeof aVal === 'number' && typeof bVal === 'number') {{
                    return currentSortDir === 'asc' ? aVal - bVal : bVal - aVal;
                }}
                return currentSortDir === 'asc' 
                    ? String(aVal).localeCompare(String(bVal)) 
                    : String(bVal).localeCompare(String(aVal));
            }});

            rows.forEach(row => tbody.appendChild(row));
        }}

        function handleSortSelect(val) {{
            if (!val) return;
            const parts = val.split('-');
            const type = parts[0];
            const dir = parts[1];
            const colMap = {{
                'name': 0,
                'pe': 1,
                'div': 2,
                'growth': 3,
                'peg': 4,
                'pegy': 5,
                'mcap': 6,
                'vlrt': 7,
                'scurve': 8,
                'rec': 9
            }};
            if (colMap[type] !== undefined) {{
                sortTable(colMap[type], dir);
            }}
        }}
    </script>
</body>
</html>
"""
                html_path.write_text(html_template, encoding="utf-8")
                print(f"💾 Saved HTML dashboard to: {html_path.resolve()}")
            else:
                print("⚠️ Warning: CSV file is empty, cannot generate Markdown or HTML report.")
        except Exception as e:
            print(f"❌ Error generating report files: {e}")
    else:
        print(f"⚠️ Warning: CSV file not found, cannot generate report files.")
        
    # 4. Commit and push changes to Git repository
    print("\n" + "=" * 60)
    print("STEP 4: COMMIT AND PUSH TO GIT")
    print("=" * 60)
    
    repo_root = scripts_dir.parent
    try:
        # Check if we are inside a git repository
        status_res = subprocess.run(["git", "status"], capture_output=True, text=True, cwd=str(repo_root))
        if status_res.returncode != 0:
            print("⚠️ Warning: Not in a git repository. Skipping git commit & push.")
        else:
            # Check if there are changes (unstaged or staged)
            status_porcelain = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=str(repo_root))
            if status_porcelain.stdout.strip():
                print("🚀 Changes detected. Staging files...")
                run_cmd(["git", "add", "."], cwd=str(repo_root))
                
                commit_msg = f"Auto-update stock analysis data - {date.today().isoformat()}"
                print(f"🚀 Committing changes: '{commit_msg}'...")
                commit_rc = run_cmd(["git", "commit", "-m", commit_msg], cwd=str(repo_root))
                
                if commit_rc == 0:
                    print("🚀 Pushing changes to remote repository...")
                    push_rc = run_cmd(["git", "push", "-u", "origin", "main"], cwd=str(repo_root))
                    if push_rc != 0:
                        print("⚠️ Warning: 'git push' failed. Check if remote upstream repository is configured.")
                else:
                    print("⚠️ Warning: 'git commit' failed.")
            else:
                print("ℹ️ No changes detected to commit/push.")
    except Exception as e:
        print(f"❌ Error performing Git operations: {e}")

    print("=" * 60)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()
