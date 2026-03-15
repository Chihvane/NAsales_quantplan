from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from quant_framework.ph_ugreen_case import run_ph_ugreen_case


class PhilippinesUGREENCaseTests(unittest.TestCase):
    def test_run_case_builds_reports_and_period_coverage(self) -> None:
        records = [
            {
                "数据期间": "09/01/2025 - 09/30/2025",
                "主播ID": 64923682,
                "序号": 1,
                "直播名称": "UGREEN 9.1 Sale",
                "直播开始时间": "2025-09-01 16:59",
                "时长": "02:00:00",
                "有参与观众数": 1265,
                "评论": 65,
                "加入购物车次数": 362,
                "平均观看时长": "00:03:16",
                "观众人数": 4121,
                "订单数(已下订单)": 45,
                "订单数(已确认订单)": 43,
                "已售商品数(已下订单)": 67,
                "已售商品数(已确认订单)": 65,
                "销售金额(已下订单)": "₱18,600.03",
                "销售金额(已确认订单)": "₱18,260.03",
            },
            {
                "数据期间": "09/01/2025 - 09/30/2025",
                "主播ID": 64923682,
                "序号": 2,
                "直播名称": "UGREEN 9.2 Sale",
                "直播开始时间": "2025-09-02 17:20",
                "时长": "02:00:00",
                "有参与观众数": 1930,
                "评论": 51,
                "加入购物车次数": 268,
                "平均观看时长": "00:01:52",
                "观众人数": 8332,
                "订单数(已下订单)": 39,
                "订单数(已确认订单)": 37,
                "已售商品数(已下订单)": 46,
                "已售商品数(已确认订单)": 44,
                "销售金额(已下订单)": "₱13,900.00",
                "销售金额(已确认订单)": "₱13,641.00",
            },
            {
                "数据期间": "10/01/2025 - 10/31/2025",
                "主播ID": 64923682,
                "序号": 3,
                "直播名称": "UGREEN 10.1 Mega Sale",
                "直播开始时间": "2025-10-01 18:30",
                "时长": "03:00:00",
                "有参与观众数": 1800,
                "评论": 74,
                "加入购物车次数": 410,
                "平均观看时长": "00:02:00",
                "观众人数": 9200,
                "订单数(已下订单)": 60,
                "订单数(已确认订单)": 56,
                "已售商品数(已下订单)": 88,
                "已售商品数(已确认订单)": 84,
                "销售金额(已下订单)": "₱35,120.25",
                "销售金额(已确认订单)": "₱33,880.25",
            },
            {
                "数据期间": "11/01/2025 - 11/30/2025",
                "主播ID": 64923682,
                "序号": 4,
                "直播名称": "UGREEN 11.1 Big Sale",
                "直播开始时间": "2025-11-01 19:10",
                "时长": "02:30:00",
                "有参与观众数": 2100,
                "评论": 84,
                "加入购物车次数": 470,
                "平均观看时长": "00:02:12",
                "观众人数": 10800,
                "订单数(已下订单)": 72,
                "订单数(已确认订单)": 69,
                "已售商品数(已下订单)": 98,
                "已售商品数(已确认订单)": 95,
                "销售金额(已下订单)": "₱45,900.40",
                "销售金额(已确认订单)": "₱44,120.40",
            },
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            excel_path = temp_path / "ugreen_ph_case.xlsx"
            output_dir = temp_path / "output"
            pd.DataFrame.from_records(records).to_excel(excel_path, index=False)

            result = run_ph_ugreen_case(excel_path, output_dir)

            summary = json.loads(Path(result["summary_json"]).read_text(encoding="utf-8"))
            self.assertEqual(summary["market_code"], "PH")
            self.assertEqual(summary["channel"], "TikTok Shop")
            self.assertEqual(
                summary["source_profile"]["covered_months"],
                ["2025-09", "2025-10", "2025-11"],
            )
            self.assertEqual(len(summary["source_profile"]["covered_periods"]), 3)
            self.assertTrue(summary["case_id"].endswith("2025-09_to_2025-11"))
            self.assertTrue(Path(result["part4_report_json"]).exists())
            self.assertTrue(Path(result["part5_report_json"]).exists())


if __name__ == "__main__":
    unittest.main()
