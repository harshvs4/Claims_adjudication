"""
Medical codes skills - ICD-10 and CPT code lookups
"""

# ICD-10 Diagnosis Code Information
ICD10_CODES = {
    'J18.9': {
        'name': 'Pneumonia',
        'category': 'Respiratory',
        'typical_severity': 'moderate',
        'common_procedures': ['99285', '70450', '36415']
    },
    'I21.9': {
        'name': 'Acute Myocardial Infarction',
        'category': 'Cardiovascular',
        'typical_severity': 'severe',
        'common_procedures': ['99291', '93000', '99223']
    },
    'S72.001A': {
        'name': 'Femur Fracture',
        'category': 'Orthopedic',
        'typical_severity': 'severe',
        'common_procedures': ['27447', '99223', '70450']
    },
    'M54.5': {
        'name': 'Low Back Pain',
        'category': 'Musculoskeletal',
        'typical_severity': 'mild',
        'common_procedures': ['99213', '99285']
    },
    'E11.9': {
        'name': 'Type 2 Diabetes',
        'category': 'Endocrine',
        'typical_severity': 'mild',
        'common_procedures': ['99213', '36415']
    },
    'C50.919': {
        'name': 'Breast Cancer',
        'category': 'Oncology',
        'typical_severity': 'severe',
        'common_procedures': ['19120', '99223', '99291']
    },
}

# CPT Procedure Codes
CPT_CODES = {
    '99285': 'Emergency Room Visit - High Complexity',
    '99213': 'Office Visit - Moderate',
    '70450': 'CT Scan - Head',
    '93000': 'Electrocardiogram',
    '36415': 'Blood Draw',
    '99223': 'Hospital Admission',
    '27447': 'Knee Replacement Surgery',
    '47562': 'Laparoscopic Cholecystectomy',
    '19120': 'Breast Excision',
    '99291': 'Critical Care - First Hour',
}


def get_diagnosis_info(icd10_code: str) -> dict:
    """
    Get information about an ICD-10 diagnosis code.
    
    Args:
        icd10_code: ICD-10 code
        
    Returns:
        Dictionary with diagnosis information or None if not found
    """
    return ICD10_CODES.get(icd10_code)


def get_procedure_name(cpt_code: str) -> str:
    """
    Get procedure name from CPT code.
    
    Args:
        cpt_code: CPT procedure code
        
    Returns:
        Procedure name or "Unknown Procedure"
    """
    return CPT_CODES.get(cpt_code, "Unknown Procedure")


def verify_procedure_diagnosis_match(diagnosis_code: str, procedure_codes: list) -> dict:
    """
    Check if procedures are typical for the diagnosis.
    
    Args:
        diagnosis_code: ICD-10 code
        procedure_codes: List of CPT codes
        
    Returns:
        Dictionary with match status and details
    """
    diagnosis_info = get_diagnosis_info(diagnosis_code)
    
    if not diagnosis_info:
        return {
            'match': None,
            'reason': 'Diagnosis code not in reference database'
        }
    
    common_procedures = set(diagnosis_info.get('common_procedures', []))
    actual_procedures = set(procedure_codes)
    
    matches = common_procedures.intersection(actual_procedures)
    
    if len(matches) > 0:
        return {
            'match': True,
            'matching_procedures': list(matches),
            'reason': f'{len(matches)} procedures typical for this diagnosis'
        }
    else:
        return {
            'match': False,
            'matching_procedures': [],
            'reason': 'No procedures match typical treatment for this diagnosis'
        }