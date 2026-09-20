"""Check the checkout payload. This does not grade an assistant response."""
import argparse
from pathlib import Path
import runpy
import sys


def check(project, expected):
    cart = runpy.run_path(str(Path(project) / 'cart.py'))
    multiplier = 100 if expected == 'buggy' else 1
    outputs = {quantity: cart['checkout_payload']('tea', quantity) for quantity in (1, 2)}
    if cart['display_price']('tea') != '$12.00':
        raise ValueError('Display must remain $12.00')
    for quantity, actual in outputs.items():
        target = {'amount_cents': 1200 * quantity * multiplier, 'currency': 'usd'}
        if actual != target:
            raise ValueError(f'Quantity {quantity}: expected {target}, got {actual}')
    return outputs


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path)
    parser.add_argument('--expect', choices=['buggy', 'fixed'], required=True)
    args = parser.parse_args()
    try:
        print(check(args.project, args.expect))
    except ValueError as error:
        print(error, file=sys.stderr)
        sys.exit(1)
