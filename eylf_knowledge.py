from pathlib import Path
from pypdf import PdfReader


PDF_PATH = Path("knowledge/EYLF-2022-V2.0.pdf")


def extract_eylf_text():
    reader = PdfReader(PDF_PATH)

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        pages.append({
            "page": page_number,
            "text": text
        })

    return pages


# Known EYLF V2.0 section headings — used to auto-split the text.
# If a heading below doesn't match your PDF's exact wording, tweak it
# after checking the printed output from Step 1.
SECTION_HEADINGS = [
    ("Principle", "Secure, respectful and reciprocal relationships"),
    ("Principle", "Partnerships"),
    ("Principle", "Respect for diversity"),
    ("Principle", "Aboriginal and Torres Strait Islander perspectives"),
    ("Principle", "Equity, inclusion and high expectations"),
    ("Principle", "Sustainability"),
    ("Principle", "Critical reflection and ongoing professional learning"),
    ("Principle", "Collaborative leadership and teamwork"),
    ("Practice", "Holistic, integrated and interconnected approaches"),
    ("Practice", "Responsiveness to children"),
    ("Practice", "Play-based learning and intentionality"),
    ("Practice", "Learning environments"),
    ("Practice", "Cultural responsiveness"),
    ("Practice", "Continuity of learning and transitions"),
    ("Practice", "Assessment and evaluation"),
    ("Outcome", "Children have a strong sense of identity"),
    ("Outcome", "Children are connected with and contribute to their world"),
    ("Outcome", "Children have a strong sense of wellbeing"),
    ("Outcome", "Children are confident and involved learners"),
    ("Outcome", "Children are effective communicators"),
]


def chunk_by_section(pages):
    """Join all page text together, then split it wherever a known
    heading appears. Returns a list of {section, subsection, page, text}.
    """
    full_text = ""
    page_offsets = []  # (char_index_where_page_starts, page_number)
    for p in pages:
        page_offsets.append((len(full_text), p["page"]))
        full_text += p["text"] + "\n"

    def page_for_offset(offset):
        page_num = page_offsets[0][1]
        for start, num in page_offsets:
            if start <= offset:
                page_num = num
            else:
                break
        return page_num

    # Find where each heading occurs in the full text
    found = []
    for section_type, heading in SECTION_HEADINGS:
        idx = full_text.find(heading)
        if idx != -1:
            found.append((idx, section_type, heading))
        else:
            print(f"WARNING: heading not found, check wording: {heading}")

    found.sort(key=lambda x: x[0])

    chunks = []
    for i, (idx, section_type, heading) in enumerate(found):
        end = found[i + 1][0] if i + 1 < len(found) else len(full_text)
        chunks.append({
            "section": section_type,
            "subsection": heading,
            "page": page_for_offset(idx),
            "text": full_text[idx:end].strip()
        })

    return chunks


# Keywords mapped to the EYLF chunks most relevant to that topic.
# When an educator's input contains one of these words, we pull in
# the matching subsection(s).
KEYWORD_MAP = {
    "sensory": ["Responsiveness to children", "Learning environments"],
    "communication": ["Children are effective communicators", "Responsiveness to children"],
    "verbal": ["Children are effective communicators"],
    "physical": ["Equity, inclusion and high expectations", "Learning environments"],
    "mobility": ["Equity, inclusion and high expectations", "Learning environments"],
    "cultural": ["Respect for diversity", "Cultural responsiveness",
                 "Aboriginal and Torres Strait Islander perspectives"],
    "diversity": ["Respect for diversity", "Equity, inclusion and high expectations"],
    "wellbeing": ["Children have a strong sense of wellbeing"],
    "identity": ["Children have a strong sense of identity"],
    "confidence": ["Children are confident and involved learners"],
    "quiet": ["Learning environments", "Responsiveness to children"],
    "additional needs": ["Equity, inclusion and high expectations", "Responsiveness to children"],
}


def retrieve_relevant_chunks(context_text, chunks, inclusion_guidelines_path):
    """context_text: whatever the educator typed (age, theme, notes about
    the group). Returns a dict with matched EYLF chunks and the full
    inclusion guidelines text, ready to drop into your prompt.
    """
    context_lower = context_text.lower()

    matched_subsections = set()
    for keyword, subsections in KEYWORD_MAP.items():
        if keyword in context_lower:
            matched_subsections.update(subsections)

    # Always include the core equity/inclusion principle even with no keyword hit
    matched_subsections.add("Equity, inclusion and high expectations")

    matched_chunks = [c for c in chunks if c["subsection"] in matched_subsections]

    with open(inclusion_guidelines_path, "r", encoding="utf-8") as f:
        inclusion_text = f.read()

    return {
        "eylf_chunks": matched_chunks,
        "inclusion_guidelines": inclusion_text
    }


def format_for_prompt(retrieved):
    """Turns the retrieved dict into plain text ready to paste into
    your activity-suggester prompt."""
    eylf_section = "\n\n".join(
        f"[{c['section']}: {c['subsection']}]\n{c['text'][:400]}"
        for c in retrieved["eylf_chunks"]
    )
    return (
        f"RELEVANT EYLF INFORMATION:\n{eylf_section}\n\n"
        f"RELEVANT INCLUSION GUIDANCE:\n{retrieved['inclusion_guidelines']}"
    )


if __name__ == "__main__":
    pages = extract_eylf_text()
    print(f"Total pages: {len(pages)}")

    chunks = chunk_by_section(pages)
    print(f"Total chunks found: {len(chunks)}\n")

    # Test the retrieval with a sample educator input
    sample_context = "4-year-old group, flower theme, one child has limited verbal communication"
    retrieved = retrieve_relevant_chunks(
        sample_context, chunks, "knowledge/inclusion_guidelines.txt"
    )
    print("--- MATCHED CHUNKS ---")
    for c in retrieved["eylf_chunks"]:
        print(f"- {c['section']}: {c['subsection']}")

    print("\n--- PROMPT-READY TEXT (first 800 chars) ---")
    print(format_for_prompt(retrieved)[:800])