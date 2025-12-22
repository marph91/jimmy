"""Helper functions for Markdown tables."""

import dataclasses
import logging

LOGGER = logging.getLogger("jimmy")


@dataclasses.dataclass
class MarkdownTable:
    """Construct a Markdown table from lists."""

    header_rows: list[list[str]] = dataclasses.field(default_factory=list)
    data_rows: list[list[str]] = dataclasses.field(default_factory=list)
    caption: str = ""

    def create_md(self) -> str:
        # column sanity check
        columns = [len(row) for row in self.header_rows + self.data_rows]
        if len(set(columns)) not in (0, 1):
            LOGGER.warning(f"Amount of columns differs: {columns}")

        def create_md_row(cells: list[str]) -> str:
            return "| " + " | ".join(cells) + " |"

        rows_md = []
        for row in self.header_rows:
            rows_md.append(create_md_row(row))
        if self.header_rows:
            separator = ["---"] * len(self.header_rows[0])
            rows_md.append(create_md_row(separator))
        for row in self.data_rows:
            rows_md.append(create_md_row(row))

        caption = self.caption + "\n\n" if self.caption else ""
        return caption + "\n".join(rows_md)
