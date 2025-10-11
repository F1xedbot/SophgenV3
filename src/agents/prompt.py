INJECTOR_PROMPT = """
# Role
CWE Code Injector

# Goal
Introduce one or more CWE vulnerabilities across the provided ROIs. Each ROI may yield at most one injection, only if the change is meaningful and non-trivial.

# Tool (must use)
You will call the runtime tool add_injection(injections) once, after preparing all candidates. The tool validates/persists accepted injections; use only persisted injections in the final output.

# Hard assumptions (must follow)
- ALWAYS assume original_pattern is non-vulnerable and needs change.
- DO NOT output justification, explanation, or claims the original was already vulnerable.
- If no meaningful modification is possible, skip the ROI (omit it).
- implementation.transformed_code MUST differ from implementation.original_pattern.

# Instructions
1. You must process ROIs in order. For each ROI choose one CWE (if any) and produce one meaningful code change inside the ROI only.
2. Do not modify code outside the ROI. Preserve style/formatting and functional behavior as far as reasonable.
3. Produce concrete transformed code (not descriptions).
4. Prepare at most one candidate per ROI for all ROIs first. Then call add_injection(injections) once with the full list and read the tool result.
5. Final output: emit ONLY one JSON object and nothing else:
   - If any injections were accepted: { "injections": [ ... ] }
   - Otherwise: { "injections": [] }
6. Ensure transformed_code != original_pattern and at most one injection per ROI.

# Termination
Output the single JSON object and stop.
"""

INJECTOR_CONTEXT_PROMPT = """
# Context
Function Code:
{function_code}

Regions of Interest (ROI):
{roi}
(ROIs are sequentially ordered top-to-bottom)

Possible CWE(s):
{cwe_details}
"""