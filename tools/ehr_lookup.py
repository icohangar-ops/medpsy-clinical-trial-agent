"""
EHR lookup tool — simulates FHIR-compatible patient record retrieval.
For hackathon demo purposes. In production, connect to Epic/Cerner FHIR API.
"""

import json


def ehr_lookup_patient(
    patient_id: str,
    include_labs: bool = True,
    include_medications: bool = True,
    include_notes: bool = True,
) -> str:
    """
    Retrieve patient data from an EHR system.

    Args:
        patient_id: Patient identifier (MRN)
        include_labs: Include lab results
        include_medications: Include medication history
        include_notes: Include clinical notes

    Returns:
        JSON string with patient data
    """
    # Demo data for the hackathon
    demo_patients = {
        "P001": {
            "id": "P001",
            "age": 55,
            "gender": "female",
            "diagnosis": "Invasive ductal carcinoma, left breast",
            "biomarkers": {
                "ER": "positive (90%)",
                "PR": "positive (70%)",
                "HER2": "negative (1+)",
                "Ki-67": "20%",
            },
            "staging": "cT2N1M0 (Stage IIB)",
            "ecog": 0,
            "labs": {
                "CBC": "WBC 5.2, Hgb 12.1, Plt 245",
                "CMP": "normal",
                "CA 15-3": "32 U/mL (elevated)",
            },
            "medications": ["Letrozole 2.5mg daily"],
            "notes": "Post-menopausal. Diagnosed 3 weeks ago. Scheduled for lumpectomy.",
        },
        "P002": {
            "id": "P002",
            "age": 68,
            "gender": "male",
            "diagnosis": "Metastatic castration-resistant prostate cancer",
            "biomarkers": {
                "PSA": "145 ng/mL",
                "AR": "positive",
                "MSI": "stable",
                "TMB": "4 mut/Mb",
            },
            "staging": "cT3bN1M1 (Stage IV)",
            "ecog": 1,
            "labs": {
                "CBC": "WBC 4.8, Hgb 10.2, Plt 198",
                "CMP": "ALP 185, LDH 320",
                "PSA": "145 ng/mL",
            },
            "medications": [
                "Abiraterone 1000mg daily",
                "Prednisone 5mg BID",
                "Denosumab 120mg monthly",
            ],
            "notes": "Progressed on docetaxel. Currently on second-line therapy.",
        },
    }

    if patient_id in demo_patients:
        patient = demo_patients[patient_id].copy()
        if not include_labs:
            patient.pop("labs", None)
        if not include_medications:
            patient.pop("medications", None)
        if not include_notes:
            patient.pop("notes", None)
        return json.dumps({"patient": patient, "source": "EHR (FHIR R4)"}, indent=2)

    return json.dumps(
        {"error": f"Patient {patient_id} not found", "available": list(demo_patients.keys())}
    )


TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "ehr_lookup_patient",
        "description": "Retrieve patient demographics, diagnoses, labs, and medications from EHR",
        "parameters": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "Patient MRN or ID",
                },
                "include_labs": {
                    "type": "boolean",
                    "description": "Whether to include lab results",
                },
                "include_medications": {
                    "type": "boolean",
                    "description": "Whether to include medication history",
                },
                "include_notes": {
                    "type": "boolean",
                    "description": "Whether to include clinical notes",
                },
            },
            "required": ["patient_id"],
        },
    },
}
