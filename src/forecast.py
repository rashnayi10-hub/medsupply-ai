"""One-day-ahead demand forecast with time-aware validation.

Run after pip install -r requirements.txt. Training rows may only use
observations strictly earlier than the date being predicted.
"""
from __future__ import annotations
import argparse
import csv
import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from statistics import mean

ROOT=Path(__file__).resolve().parents[1]

def load_history(path):
    groups=defaultdict(list)
    with Path(path).open(newline="",encoding="utf-8") as f:
        for row in csv.DictReader(f):
            q=int(row["units_used"])
            if q < 0: raise ValueError("Negative demand")
            groups[(row["hospital_id"],row["medicine_id"])].append(
                (date.fromisoformat(row["date"]),q))
    for key in groups:
        groups[key].sort()
        dates=[d for d,_ in groups[key]]
        if len(dates)!=len(set(dates)): raise ValueError(f"Duplicate demand date: {key}")
    return groups

def features(points,window=3):
    rows=[]
    for i in range(window,len(points)):
        day,value=points[i]
        past=[q for _,q in points[i-window:i]]
        rows.append((day, [*past, mean(past), day.weekday()],value))
    return rows

def evaluate(path,holdout=5):
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_absolute_error
    groups=load_history(path)
    output=[]
    for key,points in sorted(groups.items()):
        rows=features(points)
        if len(rows)<holdout+5:
            raise ValueError(f"Need more history for {key}; minimum {holdout+8} days")
        train,test=rows[:-holdout],rows[-holdout:]
        model=RandomForestRegressor(n_estimators=100,random_state=42,min_samples_leaf=2)
        model.fit([r[1] for r in train],[r[2] for r in train])
        y=[r[2] for r in test]
        p=model.predict([r[1] for r in test])
        baseline=[r[1][3] for r in test]  # 3-day trailing mean
        output.append({"hospital_id":key[0],"medicine_id":key[1],
            "test_days":len(test),"model_mae":round(mean_absolute_error(y,p),3),
            "baseline_mae":round(mean_absolute_error(y,baseline),3),
            "next_day_forecast":round(float(model.predict([features(points+[
                (points[-1][0]+timedelta(days=1),0)])[-1][1]])[0]),2)})
    return output

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--history",type=Path,default=ROOT/"data"/"forecast_history.csv")
    p.add_argument("--output",type=Path,default=ROOT/"output"/"forecast_metrics.json")
    args=p.parse_args()
    report=evaluate(args.history)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))

if __name__=="__main__": main()
