import tempfile
import unittest
from pathlib import Path
from src.forecast import load_history,features

ROOT=Path(__file__).resolve().parents[1]

class ForecastTests(unittest.TestCase):
    def test_history_sorted(self):
        groups=load_history(ROOT/"data"/"forecast_history.csv")
        self.assertTrue(groups)
        for points in groups.values():
            self.assertEqual(points,sorted(points))

    def test_feature_no_future_leakage(self):
        from datetime import date,timedelta
        start=date(2026,1,1)
        points=[(start+timedelta(days=i),i) for i in range(6)]
        result=features(points)
        self.assertEqual(result[0][1][:3],[0,1,2])
        self.assertEqual(result[0][2],3)

    def test_negative_demand_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"bad.csv"
            p.write_text("hospital_id,medicine_id,date,units_used\nH,M,2026-01-01,-5\n")
            with self.assertRaises(ValueError):
                load_history(p)

if __name__=="__main__":unittest.main()
