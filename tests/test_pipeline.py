import tempfile
import unittest
from pathlib import Path
from src.pipeline import load_csv, generate_report, run
ROOT=Path(__file__).resolve().parents[1]

class PipelineTests(unittest.TestCase):
    def test_risk_calculation(self):
        inventory=[{"hospital_id":"A","medicine_id":"M","medicine_name":"Test",
                    "on_hand":"3","reorder_point":"5","lead_time_days":"2"}]
        demand=[{"hospital_id":"A","medicine_id":"M","units_used":"3"}]
        result=generate_report(inventory,demand)
        self.assertEqual(result[0]["at_stockout_risk"],1)

    def test_negative_stock_rejected(self):
        with self.assertRaises(ValueError):
            generate_report([{"hospital_id":"A","medicine_id":"M","medicine_name":"X",
                "on_hand":"-1","reorder_point":"5","lead_time_days":"2"}],[])

    def test_duplicate_inventory_rejected(self):
        row={"hospital_id":"A","medicine_id":"M","medicine_name":"X",
             "on_hand":"6","reorder_point":"5","lead_time_days":"2"}
        with self.assertRaises(ValueError):
            generate_report([row,row],[])

    def test_end_to_end(self):
        with tempfile.TemporaryDirectory() as d:
            result=run(ROOT/"data",Path(d))
            self.assertEqual(result["inventory_records"],6)
            self.assertTrue((Path(d)/"inventory.db").exists())

if __name__=="__main__":unittest.main()
