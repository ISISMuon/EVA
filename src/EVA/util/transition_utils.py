import json
import re
from EVA.util.path_handler import get_path

# load iupac to spec notation conversion table
with open(get_path("src/EVA/databases/names/iupac_table_sorted.json"), "r") as file:
    IUPAC_TABLE = json.load(file)
with open(get_path("src/EVA/databases/names/IUPAC_to_spec_shell_table.json"), "r") as file:
    shell_name_to_num = json.load(file)
with open(get_path("src/EVA/databases/names/fine_splitting_table.json"), "r") as file:
    fine_splitting_naming = json.load(file)

# generate inverted table
SPEC_TABLE = {v: k for k, v in IUPAC_TABLE.items()}
num_to_shell_name = {v: k for k, v in shell_name_to_num.items()}
num_to_fine_splitting = {v: k for k, v in fine_splitting_naming.items()}

def to_spec(iupac_name: str) -> str:
    """
    Args:
        iupac_name: transition name in iupac notation

    Returns:
        transition name in spectroscopic notation
    """
    return SPEC_TABLE[iupac_name]

def spec_single_to_IUPAC(shell: str):
    # Regex to split "4f5/2" into n="4", l="f", j="5/2" for example
    match = re.match(r"(\d+)([spdfghijk])(\d+/\d+)", shell)
    if not match:
        raise ValueError(f"Invalid spectroscopic string: {shell}")
    n, l, j = match.groups()  
    # Map back to IUPAC
    iupac_letter = num_to_shell_name[int(n)]
    iupac_number = num_to_fine_splitting[str(l)+str(j)]
    return f"{iupac_letter}{iupac_number}"

def to_iupac(transition: str) -> str:
    shell1, shell2 = transition.split("-")
    shell1_iupac = spec_single_to_IUPAC(shell1)
    shell2_iupac = spec_single_to_IUPAC(shell2)
    return f"{shell2_iupac}-{shell1_iupac}"

def is_primary(transition: str, notation:str = "spec") -> bool:
    """
    Args:
        transition: transition name
        notation: which notation is used for transition name (default is "spec", valid options are "spec, "iupac")

    Returns:
        Boolean indicating whether transition is primary or not.

    Checks if transition is primary or not by:

    * converting to IUPAC notation if not already

    * splitting transition name by "-", e.g. "K1-L2" -> ["K1", "L2"]

    * converting letter to integer using ord()

    * subtract the letters and check the difference - if difference is 1, letters are sequential and
    therefore transition is primary
    """
    if notation != "iupac":
        transition = to_iupac(transition) # this is easier to do on iupac notation

    e1, e2 = transition.split("-")  # split transition name
    return ord(e2[0]) - ord(e1[0]) == 1  # convert letter to integer and subtract
    # if letters are sequential their difference is 1
