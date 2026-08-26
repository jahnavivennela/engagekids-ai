"""
pdf_export.py — turns a worksheet's already-built HTML string into a
ready-to-print PDF, so the educator gets one download button instead of
downloading HTML and printing/saving-as-PDF from their browser.

Uses WeasyPrint, which understands the flexbox-based WORKSHEET_CSS
(display: flex, @page rules, border-image gradients) that
worksheet_generator.py already embeds in every worksheet's HTML — no
separate print stylesheet needed, the PDF should look like the on-screen
preview.

DEPLOYMENT NOTE: WeasyPrint needs system libraries (Pango, Cairo,
GDK-PixBuf) in addition to the pip package. On Streamlit Community Cloud,
add a packages.txt file (see packages.txt in this same folder) so those
get installed via apt before the app starts. Running locally on Linux/Mac,
install the same libraries once via your OS package manager
(e.g. `apt install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0
libcairo2`, or `brew install pango` on Mac).
"""

from weasyprint import HTML


def html_to_pdf(html_content: str) -> bytes:
    """Renders a worksheet's full HTML string (as produced by
    _render_worksheet_html in worksheet_generator.py) to PDF bytes.

    No base_url is needed since worksheet HTML is fully self-contained —
    images are already embedded as data: URIs (see image_gen.py's
    image_path_to_data_uri) and CSS is inlined in a <style> tag, so there
    are no external files for WeasyPrint to resolve."""
    return HTML(string=html_content).write_pdf()