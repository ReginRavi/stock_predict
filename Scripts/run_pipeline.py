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

def run_cmd(args: list, cwd: str = None) -> int:
    """Run a command line list and return the exit status code."""
    print(f"🚀 Executing: {' '.join(args)}")
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=cwd)
    
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
        
    # 3. Convert generated CSV output to Markdown and save
    csv_path = Path(args.output_csv) if args.output_csv else (scripts_dir / "output" / f"peg_ratios_{date.today().isoformat()}.csv")
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
                headers = ["Company Name", "Stock P/E", "Dividend Yield (%)", "Profit Growth 3Y (%)", "PEG Ratio 3Y", "PEGY Ratio 3Y", "Market Cap (Cr)"]
                
                md_lines = []
                md_lines.append(f"# Stock Analysis Report - {date.today().isoformat()}")
                md_lines.append(f"\nGenerated automatically by the stock analysis pipeline.")
                md_lines.append(f"\n| {' | '.join(headers)} |")
                md_lines.append(f"| {' | '.join(['---'] * len(headers))} |")
                
                for r in rows:
                    row_vals = [
                        r.get("Company Name", ""),
                        r.get("Stock P/E", ""),
                        r.get("Dividend Yield (%)", ""),
                        r.get("Profit Growth 3Y (%)", ""),
                        r.get("PEG Ratio 3Y", ""),
                        r.get("PEGY Ratio 3Y", ""),
                        r.get("Market Cap (Cr)", "")
                    ]
                    md_lines.append(f"| {' | '.join(row_vals)} |")
                
                md_content = "\n".join(md_lines) + "\n"
                md_path.write_text(md_content, encoding="utf-8")
                print(f"💾 Saved markdown report to: {md_path.resolve()}")
            else:
                print("⚠️ Warning: CSV file is empty, cannot generate Markdown report.")
        except Exception as e:
            print(f"❌ Error generating markdown report: {e}")
    else:
        print(f"⚠️ Warning: CSV file not found, cannot generate Markdown report.")
        
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
                    push_rc = run_cmd(["git", "push"], cwd=str(repo_root))
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
