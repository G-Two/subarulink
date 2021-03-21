"""Tests for subarulink CLI."""
import sys
from unittest.mock import patch

import subarulink.app.cli as cli


def test_no_args():
    testargs = ["subarulink"]
    with patch.object(sys, "argv", testargs), patch("argparse.ArgumentParser.print_help") as mock_print_help:
        cli.main()
    assert mock_print_help.call_count == 1


# TODO: More tests
