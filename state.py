from typing import TypedDict, List, Dict, Any

class LegalState(TypedDict):
    """
    State-bus architecture designed to capture explicit judicial criteria 
    for Indian case analysis workflows.
    """
    raw_text: str                          # Whole parsed string text layers from the PDF
    doc_type: str                          # Document categorization classification
    indian_statutes: List[str]             # List of Acts, Sections, or Codes invoked
    final_summary: str                     # Clean unified markdown brief containing all targets
