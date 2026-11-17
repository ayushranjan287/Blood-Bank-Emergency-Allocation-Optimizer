from datetime import date
from algorithms.merge_sort import merge_sort


# Simplified red blood cell compatibility rules
COMPATIBILITY = {
    "O-": ["O-"],
    "O+": ["O-", "O+"],
    "A-": ["O-", "A-"],
    "A+": ["O-", "O+", "A-", "A+"],
    "B-": ["O-", "B-"],
    "B+": ["O-", "O+", "B-", "B+"],
    "AB-": ["O-", "A-", "B-", "AB-"],
    "AB+": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]
}


def allocate_blood(patient, units):

    patient_group = patient["blood_group"]

    compatible_groups = COMPATIBILITY.get(patient_group, [])

    # Select available and non-expired compatible units
    compatible_units = [
        unit for unit in units
        if unit["blood_group"] in compatible_groups
        and unit["status"] == "Available"
        and unit["expiry_date"] >= date.today().isoformat()
    ]

    # No compatible blood unit found
    if not compatible_units:
        return None

    # Sort compatible units by expiry date
    sorted_units = merge_sort(compatible_units)

    # Greedy choice: select the earliest-expiring unit
    selected_unit = sorted_units[0]

    return selected_unit