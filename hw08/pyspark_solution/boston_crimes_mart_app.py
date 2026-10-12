from __future__ import annotations

import logging
from collections.abc import Sequence

from boston_crimes_mart.config import AppConfig
from boston_crimes_mart.context import AppContext


def main(argv: Sequence[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    config = AppConfig.from_args(argv)
    with AppContext(config) as ctx:
        ctx.pipeline.execute(config.crimes_path, config.offense_codes_path, config.output_path)


if __name__ == "__main__":
    main()
