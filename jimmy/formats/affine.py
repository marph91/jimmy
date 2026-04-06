"""Convert Affine notes to the intermediate format."""

from pathlib import Path
import sqlite3

import pycrdt

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.links
import jimmy.md_lib.tables


def convert_table(block):
    # ordering - key: ID, value: order
    column_order = {}
    row_order = {}
    for key, value in block.items():
        if key.endswith(".order"):
            if key.startswith("prop:columns"):
                column_order[key.split(".")[1]] = value
            else:
                row_order[key.split(".")[1]] = value

    column_order = dict(sorted(column_order.items(), key=lambda item: item[1]))
    column_order = {key: index for index, key in enumerate(column_order.keys())}
    row_order = dict(sorted(row_order.items(), key=lambda item: item[1]))
    row_order = {key: index for index, key in enumerate(row_order.keys())}

    # sort cells into the dummy table according to the ordering
    table = [["" for _ in range(len(column_order))] for _ in range(len(row_order))]
    for key, value in block.items():
        if key.startswith("prop:cells"):
            row_col = key.split(".")[1]
            row, col = row_col.split(":")
            table[row_order[row]][column_order[col]] = str(value)

    # create markdown table
    table_md = jimmy.md_lib.tables.MarkdownTable()
    table_md.header_rows = [[""] * len(column_order)]
    table_md.data_rows = table
    return table_md.create_md()


class Converter(converter.BaseConverter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # we need a resource folder to avoid writing files to the source folder
        self.resource_folder = common.get_temp_folder()

    @common.catch_all_exceptions
    def convert_note(
        self,
        page: dict,
        metas: dict,
        blobs_by_key: dict,
        all_tags: dict,
        parent_notebook: imf.Notebook,
    ):  # pylint: disable=too-many-arguments,too-many-positional-arguments
        page_id = page.get("id")
        title = page.get("title", page_id or common.unique_title())
        self.logger.debug(f'Converting note "{title}"')

        note_imf = imf.Note(
            title=title,
            source_application=self.format,
            original_id=page_id,
        )

        if (doc_bytes := metas.get(page_id)) is None:
            self.logger.warning("no snapshot found")
            return

        doc: pycrdt.Doc = pycrdt.Doc()
        doc.apply_update(doc_bytes)

        if not (blocks_map := doc.get("blocks", type=pycrdt.Map)):
            self.logger.warning("no blocks found")
            return
        # find the root block "affine:page"
        root = None
        for bid, bdata in blocks_map.items():
            if bdata.get("sys:flavour") == "affine:page":
                root = bid
                break
        if root is None:
            self.logger.warning(f"No root affine:page found for page {title} ({page_id})")
            return

        # Handle attachments: map sourceId -> filename, and extract matching blobs
        for _bid, block in blocks_map.items():
            # Images: prop:sourceId references a blob.key
            src_id = block.get("prop:sourceId")
            if src_id and src_id in blobs_by_key:
                ext = common.guess_suffix(blobs_by_key[src_id]["mime"])

                # write resource to filesystem
                resource_path = self.resource_folder / f"{src_id}{ext}"
                resource_path = common.get_unique_path(resource_path, blobs_by_key[src_id]["data"])
                resource_path.write_bytes(blobs_by_key[src_id]["data"])

                # link resource to markdown note
                note_imf.resources.append(
                    imf.Resource(resource_path, original_text=f"![{src_id}]({src_id})")
                )

        note_lines, note_imf.note_links = self.extract_blocks(blocks_map, root)
        note_imf.body = "\n\n".join(note_lines)

        tag_ids = page.get("tags", [])
        note_imf.tags = [all_tags[tid] for tid in tag_ids if tid in all_tags]

        if (created_ms := page.get("createDate")) is not None:
            note_imf.created = common.timestamp_to_datetime(created_ms / 1000)
        if (updated_ms := page.get("updatedAt")) is not None:
            note_imf.updated = common.timestamp_to_datetime(updated_ms / 1000)

        parent_notebook.child_notes.append(note_imf)

    def extract_blocks(self, blocks: dict, block_id: str, depth=0):
        block = blocks.get(block_id, {})
        block_flavor = block.get("sys:flavour")
        block_type = block.get("prop:type")
        lines = []
        note_links = []
        match block_flavor:
            case "affine:database":
                # TODO: How to convert database block?
                lines.append(f'Affine Database "{block["prop:title"]}"')
            case "affine:embed-synced-doc":
                note_link = jimmy.md_lib.links.make_link(
                    "note_link", str(block.get("prop:pageId", ""))
                )
                note_links.append(imf.NoteLink(note_link, str(block.get("prop:pageId", "")), ""))
                lines.append(note_link)
            case "affine:bookmark" | "affine:embed-youtube":
                lines.append(
                    jimmy.md_lib.links.make_link(
                        str(block.get("prop:title", "")), str(block.get("prop:url", ""))
                    )
                )
            case "affine:edgeless-text":
                pass  # nothing to do
            case "affine:frame":
                # TODO
                text = str(block.get("prop:title", ""))
                if (description := block.get("prop:description")) is not None:
                    text += f": {description}"
                lines.append(text)
            case "affine:image":
                image_id = block.get("prop:sourceId")
                lines.append(f"![{image_id}]({image_id})")
            case "affine:latex":
                lines.append(f"${block.get('prop:latex', '')}$")
            case "affine:list":
                match block_type:
                    case "bulleted":
                        text = block.get("prop:text", "")
                        lines.append("    " * depth + f"- {text}")
                    case "numbered":
                        text = block.get("prop:text", "")
                        lines.append("    " * depth + f"1. {text}")
                    case "todo":
                        checked = block.get("prop:checked", False)
                        text = block.get("prop:text", "")
                        lines.append("    " * depth + f"- [{'x' if checked else ' '}] {text}")
                    case _:
                        self.logger.warning(f'Unexpected list block type "{block_type}"')
            case "affine:note":
                # TODO: What is a "note"?
                pass
            case "affine:page":
                lines.append(f"# {block['prop:title']}")
            case "affine:paragraph":
                match block_type:
                    case "h1" | "h2" | "h3" | "h4" | "h5" | "h6":
                        text = block.get("prop:text", "")
                        lines.append(f"{'#' * int(block_type[-1])} {text}")
                    case "text":
                        lines.append(str(block.get("prop:text", "")))
                    case _:
                        self.logger.warning(f'Unexpected paragraph block type "{block_type}"')
            case "affine:surface":
                # TODO: How to convert whiteboard surface block?
                # https://docs.affine.pro/blocksuite-wip/architecture#document-structure
                # At least remove empty elements.
                if block["prop:elements"].get("value", {}):
                    lines.append("Affine Surface")
            case "affine:table":
                lines.append(convert_table(block))
            case _:
                self.logger.warning(f'Unexpected block flavor "{block_flavor}"')
        # Recurse children
        for child_id in block.get("sys:children", []):
            depth_increment = int(block_flavor == "affine:list")
            child_lines, child_note_links = self.extract_blocks(
                blocks, child_id, depth=depth + depth_increment
            )
            lines.extend(child_lines)
            note_links.extend(child_note_links)
        return lines, note_links

    def convert(self, file_or_folder: Path):
        conn = sqlite3.connect(str(file_or_folder))
        cur = conn.cursor()
        cur.execute("SELECT doc_id, data FROM snapshots")
        metas = dict(cur.fetchall())

        # Load the blobs table (for attachments)
        try:
            cur.execute("SELECT key, data, mime, size FROM blobs")
            blobs_by_key = {
                key: {"data": data, "mime": mime, "size": size}
                for key, data, mime, size in cur.fetchall()
            }
        except sqlite3.OperationalError:
            blobs_by_key = {}

        # Find the meta doc (workspace), which has the page list and tags
        meta = None
        for _doc_id, raw in metas.items():
            doc: pycrdt.Doc = pycrdt.Doc()
            doc.apply_update(raw)

            if "meta" in list(doc.keys()):
                meta = doc.get("meta", type=pycrdt.Map)
                break
        else:
            self.logger.error("No workspace meta found in Affine backup")
            return

        root_notebook = imf.Notebook(meta["name"])
        self.root_notebook.child_notebooks.append(root_notebook)

        # first pass: collect tags
        all_tags = {}
        for page in meta.get("pages", []):
            for tag in page.get("tags", []):
                # Assume tag = {"id": "...", "name": "..."}
                if isinstance(tag, dict) and "id" in tag:
                    all_tags[tag["id"]] = imf.Tag(tag.get("name", ""), tag["id"])

        # second pass: create notes
        pages = meta.get("pages", [])
        for page in pages:
            self.convert_note(page, metas, blobs_by_key, all_tags, parent_notebook=root_notebook)
