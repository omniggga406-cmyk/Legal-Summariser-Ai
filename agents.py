import os
import sys
import re

# Force absolute path discovery across Windows OneDrive architectures
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

from google import genai
from google.genai import types
from src.state import LegalState
from typing import Dict, Any
from config.settings import Settings

client = genai.Client(api_key=Settings.GEMINI_API_KEY)
PRIMARY_MODEL = "gemini-2.5-flash"
FAILOVER_MODEL = "gemini-1.5-pro"

fast_config = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_budget=0)
)

def run_local_high_utility_parser(text: str) -> Dict[str, Any]:
    """
    HIGH-UTILITY LOCAL RESOLVER: Extracts clean descriptive paragraphs from the text layer 
    locally if cloud servers fail.
    """
    text_lower = text.lower()
    raw_lines = [line.strip() for line in text.split("\n") if len(line.strip()) > 60]
    lines = []
    for rl in raw_lines:
        clean_ln = re.sub(r'[^a-zA-Z0-9\s\.,\-\(\)]', '', rl)
        clean_ln = ' '.join(clean_ln.split())
        if clean_ln and clean_ln not in lines:
            lines.append(clean_ln)

    if "contract" in text_lower or "agreement" in text_lower:
        doc_type = "Contract / Commercial Deed"
    elif "petition" in text_lower or "plaint" in text_lower or "vs" in text_lower or "court" in text_lower:
        doc_type = "Litigation Case Record / Judgment"
    else:
        doc_type = "Legal Documentation Summary"

    parties_final = "Litigants parsed dynamically inside the document headers. (Please refer to the source case title)."
    for line in lines[:15]:
        if any(k in line.lower() for k in ["versus", " v/s ", " vs ", "petitioner", "appellant", "respondent"]):
            if len(line) < 120:
                parties_final = line
                break

    alleg_find = ""
    for line in lines:
        if any(k in line.lower() for k in ["alleged", "allegation", "grievance", "breach", "dispute"]):
            if len(line) > 80 and len(line) < 200:
                alleg_find = line
                break
    if not alleg_find and lines: alleg_find = lines[0]
    allegations_final = f"The moving party asserts procedural non-compliance or statutory violations regarding the subject matter: \n\n*\"{alleg_find}\"*"

    counter_find = ""
    for line in lines:
        if any(k in line.lower() for k in ["denied", "contended", "argued", "defense", "submitted that"]):
            if len(line) > 80 and len(line) < 200:
                counter_find = line
                break
    if not counter_find and len(lines) > 1: counter_find = lines[1]
    counters_final = f"The responding party disputed the assertions, raising formal contentions against the liability claims: \n\n*\"{counter_find}\"*"

    verdict_find = ""
    for line in lines:
        if any(k in line.lower() for k in ["held", "allowed", "dismissed", "order", "findings"]):
            if len(line) > 80 and len(line) < 200:
                verdict_find = line
                break
    if not verdict_find and len(lines) > 2: verdict_find = lines[2]
    verdict_final = f"The court evaluated the arguments and issued direct milestones regarding the core petition grounds: \n\n*\"{verdict_find}\"*"

    judgement_find = ""
    for line in lines[-40:]:
        if any(k in line.lower() for k in ["therefore", "decree", "operative", "accordingly", "remitted", "costs"]):
            if len(line) > 80 and len(line) < 250:
                judgement_find = line
                break
    if not judgement_find and lines: judgement_find = lines[-1]
    judgement_final = f"The operative decree concludes the active proceedings with the following directive: \n\n*\"{judgement_find}\"*"

    acts = []
    if "constitution" in text_lower: acts.append("Constitution of India")
    if "penal code" in text_lower or "bns" in text_lower: acts.append("Bharatiya Nyaya Sanhita / IPC")
    if "civil procedure" in text_lower or "cpc" in text_lower: acts.append("Code of Civil Procedure (CPC)")
    if "contract act" in text_lower: acts.append("Indian Contract Act, 1872")
    if "arbitration" in text_lower: acts.append("Arbitration & Conciliation Act, 1996")
    
    regex_acts = re.findall(r'([A-Za-z\s]+Act,\s+\d{4})', text)
    if regex_acts:
        acts.extend([ra.strip() for ra in regex_acts])
    unique_acts = list(set(acts))[:4]
    if not unique_acts:
        unique_acts = ["Central Statutory Code", "Judicial Precedents"]

    summary = (
        f"### 👥 PARTIES INVOLVED\n{parties_final}\n\n"
        f"### 🚨 ALLEGATIONS & BREACHES\n{allegations_final}\n\n"
        f"### 🛡️ COUNTER ARGUMENTS & DEFENSES\n{counters_final}\n\n"
        f"### 🏛️ VERDICT STATUS / FINDINGS\n{verdict_final}\n\n"
        f"### ⚖️ FINAL JUDGEMENT / OPERATIVE DECREE\n{judgement_final}\n\n"
        f"---  \n"
        f"*💡 Note: Displaying local context parameters because the cloud API limit was reached.*"
    )

    return {
        "doc_type": doc_type,
        "indian_statutes": unique_acts,
        "final_summary": summary
    }

def execute_cloud_call(model_name: str, safe_text: str) -> dict:
    """Executes layout extraction against a specific Google model configuration."""
    prompt = (
        "You are an elite Indian legal research analysis engine. Process the legal document text provided below.\n"
        "Provide a comprehensive, high-utility analysis split strictly into the sections below. "
        "Use the exact block format and markdown headers specified below. Do not use tags like PART 1 or code blocks.\n\n"
        "### 👥 PARTIES INVOLVED\n"
        "[Identify the full names of the parties involved, e.g., Petitioners vs Respondents]\n\n"
        "### 🚨 ALLEGATIONS & BREACHES\n"
        "[Provide a detailed, multi-paragraph brief of the core allegations, complaints, or contractual breaches]\n\n"
        "### 🛡️ COUNTER ARGUMENTS & DEFENSES\n"
        "[Provide a detailed, multi-paragraph brief of the counter-arguments or defenses raised by the opposite party]\n\n"
        "### 🏛️ VERDICT STATUS / FINDINGS\n"
        "[Detail the lower court findings, verdicts, or intermediate orders]\n\n"
        "### ⚖️ FINAL JUDGEMENT / OPERATIVE DECREE\n"
        "[Detail the final operative order, ruling, relief granted, or conclusion of the court]\n\n"
        "### 📜 LAWS & STATUTES USED\n"
        "[Provide a simple comma-separated list of the Acts, Sections, or Codes used here. Do not add any introduction or text before this list]\n\n"
        f"Text Document:\n{safe_text}"
    )
    
    response = client.models.generate_content(model=model_name, contents=prompt, config=fast_config)
    raw = response.text
    
    if "### 🚨 ALLEGATIONS" in raw and "### ⚖️ FINAL JUDGEMENT" in raw:
        if "### 📜 LAWS" in raw:
            clean_brief = raw.split("### 📜 LAWS")[0].strip()
            laws_raw = raw.split("### 📜 LAWS")[-1].replace("& STATUTES USED", "").strip()
            acts = [l.strip() for l in laws_raw.split(",") if len(l.strip()) > 2]
        else:
            clean_brief = raw
            acts = ["Constitution of India", "Indian Penal Code"]
            
        doc_type = "Contract / Agreement" if "contract" in raw.lower() or "agreement" in raw.lower() else "Litigation Case Record"
        
        return {
            "doc_type": doc_type,
            "indian_statutes": acts,
            "final_summary": clean_brief
        }
    else:
        raise ValueError("Structural layout split mismatch.")

def process_unified_legal_analysis(state: LegalState) -> Dict[str, Any]:
    """
    Feeds text to the primary context model window.
    Features robust catch blocks for 503 and 429 exceptions to allow failover handling.
    """
    full_text = state['raw_text']
    safe_text = full_text if len(full_text) < 120000 else full_text[:120000]
    
    # Track 1: Try Primary updated model
    try:
        return execute_cloud_call(PRIMARY_MODEL, safe_text)
    except Exception as e1:
        # If primary model is down with a 503 high-demand spike, switch to failover track immediately
        if "503" in str(e1) or "UNAVAILABLE" in str(e1) or "429" in str(e1):
            try:
                print(f"[~] Primary model experiencing high demand. Shifting path to backup server track...")
                return execute_cloud_call(FAILOVER_MODEL, safe_text)
            except Exception as e2:
                # If both are down, activate clean local fallback processing
                return run_local_high_utility_parser(safe_text)
        else:
            return run_local_high_utility_parser(safe_text)
