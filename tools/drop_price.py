"""Drop a price in the store feed. Run this in a second terminal during step 1.

  python tools/drop_price.py               Sparx shoe → ₹849
  python tools/drop_price.py CMPS-BLK-41 899
  python tools/drop_price.py --reset       all prices back above budget
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lab import feed  # noqa: E402

if "--reset" in sys.argv:
    feed.reset_feed()
    print("Feed reset: all prices above budget.")
else:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    sku = args[0] if args else "SPRX-BLK-09"
    price = int(args[1]) if len(args) > 1 else 849
    feed.drop_price(sku, price)
    print(f"{sku} → ₹{price}")
