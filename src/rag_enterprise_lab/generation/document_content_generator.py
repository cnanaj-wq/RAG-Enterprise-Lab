"""Génération déterministe de contenu physique synthétique, pour les 7
formats requis, sans dépendance supplémentaire (stdlib + `zipfile` pour les
formats Office Open XML). Le contenu est minimal mais structurellement
valide dans chaque format — suffisant pour l'upload/parsing Phase 3, pas
destiné à un rendu visuel soigné.
"""

import csv
import io
import zipfile
from xml.sax.saxutils import escape as xml_escape

from rag_enterprise_lab.domain.documents import DocumentManifestEntry
from rag_enterprise_lab.generation.document_format_rules import (
    FORMAT_CONTENT_TYPES,
    format_for,
)


def _metadata_lines(entry: DocumentManifestEntry) -> list[str]:
    return [
        entry.title,
        f"document_id: {entry.document_id}",
        f"document_type: {entry.document_type}",
        f"domain: {entry.domain.value}",
        f"version: {entry.version}",
        f"status: {entry.status.value}",
        f"classification: {entry.classification.value}",
        f"valid_from: {entry.valid_from}",
        f"valid_to: {entry.valid_to}",
        f"owner: {entry.owner}",
        "Document synthetique genere par RAG Enterprise Lab. Aucune donnee reelle.",
    ]


def _generate_markdown(entry: DocumentManifestEntry) -> bytes:
    lines = [f"# {entry.title}", ""] + [f"- {line}" for line in _metadata_lines(entry)[1:]]
    return "\n".join(lines).encode("utf-8")


def _generate_html(entry: DocumentManifestEntry) -> bytes:
    items = "".join(f"<li>{xml_escape(line)}</li>" for line in _metadata_lines(entry)[1:])
    html = (
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\">"
        f"<title>{xml_escape(entry.title)}</title></head>"
        f"<body><h1>{xml_escape(entry.title)}</h1><ul>{items}</ul></body></html>"
    )
    return html.encode("utf-8")


def _generate_csv(entry: DocumentManifestEntry) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["field", "value"])
    writer.writerow(["title", entry.title])
    writer.writerow(["document_id", entry.document_id])
    writer.writerow(["document_type", entry.document_type])
    writer.writerow(["status", entry.status.value])
    writer.writerow(["classification", entry.classification.value])
    writer.writerow(["owner", entry.owner])
    return buffer.getvalue().encode("utf-8")


def _pdf_escape(text: str) -> str:
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def _generate_pdf(entry: DocumentManifestEntry) -> bytes:
    lines = [_pdf_escape(line) for line in _metadata_lines(entry)]
    content_ops = ["BT", "/F1 11 Tf", "72 740 Td", "14 TL"]
    for i, line in enumerate(lines):
        if i > 0:
            content_ops.append("T*")
        content_ops.append(f"({line}) Tj")
    content_ops.append("ET")
    stream = "\n".join(content_ops).encode("latin-1", errors="replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        (b"<< /Length %d >>\nstream\n" % len(stream)) + stream + b"\nendstream",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode("ascii")
        out += obj
        out += b"\nendobj\n"

    xref_offset = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode("ascii")
    out += b"0000000000 65535 f \n"
    for off in offsets[1:]:
        out += f"{off:010d} 00000 n \n".encode("ascii")
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF"
    ).encode("ascii")
    return bytes(out)


# Horodatage ZIP fixe : zipfile.writestr(name, ...) embarque l'heure système
# courante par défaut, ce qui rend les octets DOCX/XLSX/PPTX non
# déterministes d'un appel à l'autre (et casse l'idempotence côté R2, basée
# sur le checksum du contenu). 1980-01-01 est le plus ancien horodatage
# valide au format ZIP DOS.
_ZIP_FIXED_DATE_TIME = (1980, 1, 1, 0, 0, 0)


def _zip_write(parts: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, content in parts.items():  # ordre d'insertion du dict = déterministe
            info = zipfile.ZipInfo(filename=path, date_time=_ZIP_FIXED_DATE_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, content)
    return buffer.getvalue()


def _generate_docx(entry: DocumentManifestEntry) -> bytes:
    body = "".join(
        f'<w:p><w:r><w:t xml:space="preserve">{xml_escape(line)}</w:t></w:r></w:p>'
        for line in _metadata_lines(entry)
    )
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{body}</w:body></w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/></Relationships>'
    )
    return _zip_write(
        {
            "[Content_Types].xml": content_types,
            "_rels/.rels": rels,
            "word/document.xml": document_xml,
        }
    )


def _generate_xlsx(entry: DocumentManifestEntry) -> bytes:
    rows = [("field", "value")] + [
        tuple(line.split(": ", 1)) if ": " in line else (line, "")
        for line in _metadata_lines(entry)[1:]
    ]
    sheet_rows = []
    for r, (field, value) in enumerate(rows, start=1):
        cell_a = f'<c r="A{r}" t="inlineStr"><is><t>{xml_escape(field)}</t></is></c>'
        cell_b = f'<c r="B{r}" t="inlineStr"><is><t>{xml_escape(str(value))}</t></is></c>'
        sheet_rows.append(f'<row r="{r}">{cell_a}{cell_b}</row>')

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>"
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/></Relationships>'
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/></Relationships>'
    )
    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{''.join(sheet_rows)}</sheetData></worksheet>"
    )
    return _zip_write(
        {
            "[Content_Types].xml": content_types,
            "_rels/.rels": root_rels,
            "xl/workbook.xml": workbook_xml,
            "xl/_rels/workbook.xml.rels": workbook_rels,
            "xl/worksheets/sheet1.xml": sheet_xml,
        }
    )


def _generate_pptx(entry: DocumentManifestEntry) -> bytes:
    paragraphs = "".join(
        f"<a:p><a:r><a:t>{xml_escape(line)}</a:t></a:r></a:p>" for line in _metadata_lines(entry)
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/ppt/presentation.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
        '<Override PartName="/ppt/slides/slide1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        "</Types>"
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="ppt/presentation.xml"/></Relationships>'
    )
    presentation_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<p:sldIdLst><p:sldId id="256" r:id="rId1"/></p:sldIdLst>'
        '<p:sldSz cx="9144000" cy="6858000"/></p:presentation>'
    )
    presentation_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" '
        'Target="slides/slide1.xml"/></Relationships>'
    )
    slide_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
        "<p:cSld><p:spTree>"
        '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
        "<p:grpSpPr/>"
        "<p:sp>"
        '<p:nvSpPr><p:cNvPr id="2" name="Content"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
        "<p:spPr/>"
        f"<p:txBody><a:bodyPr/><a:lstStyle/>{paragraphs}</p:txBody>"
        "</p:sp>"
        "</p:spTree></p:cSld></p:sld>"
    )
    return _zip_write(
        {
            "[Content_Types].xml": content_types,
            "_rels/.rels": root_rels,
            "ppt/presentation.xml": presentation_xml,
            "ppt/_rels/presentation.xml.rels": presentation_rels,
            "ppt/slides/slide1.xml": slide_xml,
        }
    )


_GENERATORS = {
    "md": _generate_markdown,
    "html": _generate_html,
    "csv": _generate_csv,
    "pdf": _generate_pdf,
    "docx": _generate_docx,
    "xlsx": _generate_xlsx,
    "pptx": _generate_pptx,
}


def generate_content(entry: DocumentManifestEntry) -> tuple[bytes, str, str]:
    """Retourne (contenu, content_type, extension) pour une entrée manifest,
    de façon purement déterministe (aucun aléa, aucun accès réseau)."""
    extension = format_for(entry.document_id, entry.document_type)
    payload = _GENERATORS[extension](entry)
    return payload, FORMAT_CONTENT_TYPES[extension], extension
