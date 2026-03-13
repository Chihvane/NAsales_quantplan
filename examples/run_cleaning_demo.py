import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from quant_framework.cleaners import (  # noqa: E402
    normalize_amazon_listings_export,
    normalize_ebay_transactions_export,
    normalize_tiktok_channels_export,
)


def main() -> None:
    examples_dir = Path(__file__).resolve().parent
    output_dir = examples_dir / "cleaned"
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "amazon": normalize_amazon_listings_export(
            examples_dir / "raw_amazon_listing_export.csv",
            output_dir / "amazon_listings.csv",
        ),
        "ebay": normalize_ebay_transactions_export(
            examples_dir / "raw_ebay_sold_export.csv",
            output_dir / "ebay_transactions.csv",
        ),
        "tiktok": normalize_tiktok_channels_export(
            examples_dir / "raw_tiktok_channel_export.csv",
            output_dir / "tiktok_channels.csv",
        ),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
