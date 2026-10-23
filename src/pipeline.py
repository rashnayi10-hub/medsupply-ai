"""Inventory ETL and stockout screening for synthetic hospital records."""
from __future__ import annotations
import argparse
import csv
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def generate_report(inventory, daily_demand):
    histories = defaultdict(list)
    for row in daily_demand:
        quantity = int(row["units_used"])
        if quantity < 0:
            raise ValueError("Consumption cannot be negative")
        histories[(row["hospital_id"],row["medicine_id"])].append(quantity)
    results = []
    seen = set()
    for row in inventory:
        key = (row["hospital_id"],row["medicine_id"])
        if key in seen:
            raise ValueError(f"Duplicate inventory key: {key}")
        seen.add(key)
        on_hand = int(row["on_hand"])
        lead = int(row["lead_time_days"])
        reorder = int(row["reorder_point"])
        if on_hand < 0 or lead < 0 or reorder < 0:
            raise ValueError("Inventory values cannot be negative")
        quantities = histories.get(key, [])
        average = sum(quantities)/len(quantities) if quantities else 0
        coverage = on_hand/average if average else None
        risk = bool(average > 0 and coverage <= lead) or on_hand <= reorder
        results.append({"hospital_id":key[0],"medicine_id":key[1],
            "medicine_name":row["medicine_name"],"on_hand":on_hand,
            "avg_daily_demand":round(average,2),
            "days_of_supply":round(coverage,2) if coverage is not None else None,
            "lead_time_days":lead,"at_stockout_risk":int(risk)})
    return results

def run(data_dir=ROOT/"data", output_dir=ROOT/"output"):
    inventory = load_csv(Path(data_dir)/"inventory.csv")
    demand = load_csv(Path(data_dir)/"daily_demand.csv")
    results = generate_report(inventory,demand)
    output_dir=Path(output_dir)
    output_dir.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(output_dir/"inventory.db") as db:
        db.execute("""CREATE TABLE IF NOT EXISTS inventory_risk (
            hospital_id TEXT, medicine_id TEXT, medicine_name TEXT, on_hand INTEGER,
            avg_daily_demand REAL, days_of_supply REAL, lead_time_days INTEGER,
            at_stockout_risk INTEGER, PRIMARY KEY(hospital_id,medicine_id))""")
        db.executemany("""INSERT INTO inventory_risk VALUES
          (:hospital_id,:medicine_id,:medicine_name,:on_hand,:avg_daily_demand,
          :days_of_supply,:lead_time_days,:at_stockout_risk)
          ON CONFLICT(hospital_id,medicine_id) DO UPDATE SET
          on_hand=excluded.on_hand,avg_daily_demand=excluded.avg_daily_demand,
          days_of_supply=excluded.days_of_supply,at_stockout_risk=excluded.at_stockout_risk""",results)
    with (output_dir/"risk_report.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(results[0]) if results else [
            "hospital_id","medicine_id","medicine_name","on_hand",
            "avg_daily_demand","days_of_supply","lead_time_days","at_stockout_risk"])
        writer.writeheader()
        writer.writerows(results)
    metrics={"inventory_records":len(results),"stockout_risk_flags":sum(r["at_stockout_risk"] for r in results)}
    (output_dir/"metrics.json").write_text(json.dumps(metrics,indent=2),encoding="utf-8")
    return metrics

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--data-dir",type=Path,default=ROOT/"data")
    parser.add_argument("--output-dir",type=Path,default=ROOT/"output")
    args=parser.parse_args()
    print(json.dumps(run(args.data_dir,args.output_dir),indent=2))
