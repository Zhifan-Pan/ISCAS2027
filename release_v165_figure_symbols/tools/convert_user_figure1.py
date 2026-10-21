"""Convert the exact user-supplied SVG to vector PDF; do not alter artwork."""
from pathlib import Path
import argparse
import datetime as dt
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET

import gi
gi.require_version('Rsvg', '2.0')
from gi.repository import Rsvg
import cairo


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--svg', type=Path, required=True)
    parser.add_argument('--source-dir', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    assert not args.receipt.exists(), 'Preserve previous conversion receipts.'
    content = args.svg.read_bytes()
    root = ET.fromstring(content)
    width, height = float(root.attrib['width']), float(root.attrib['height'])
    copied = args.source_dir / 'figures/Figure1_Vector.svg'
    output = copied.with_suffix('.pdf')
    copied.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.svg, copied)
    handle = Rsvg.Handle.new_from_file(str(copied))
    surface = cairo.PDFSurface(str(output), width * 0.75, height * 0.75)
    context = cairo.Context(surface)
    context.scale(0.75, 0.75)
    viewport = Rsvg.Rectangle()
    viewport.x = viewport.y = 0
    viewport.width, viewport.height = width, height
    assert handle.render_document(context, viewport)
    surface.finish()
    assert copied.read_bytes() == content
    receipt = {
        'created_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'source_svg': str(args.svg.resolve()),
        'source_svg_sha256': sha(args.svg),
        'copied_svg': str(copied),
        'vector_pdf': str(output),
        'vector_pdf_sha256': sha(output),
        'SVG_pixels': [width, height],
        'PDF_points': [width * 0.75, height * 0.75],
        'renderer': 'librsvg through PyGObject; cairo PDFSurface',
        'artwork_modified': False,
        'scientific_runs': 0,
    }
    args.receipt.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
