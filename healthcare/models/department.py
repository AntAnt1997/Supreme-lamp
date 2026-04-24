"""Department and specialty models – covers the entire healthcare system."""

from sqlalchemy import Column, Integer, String, Text, Boolean

from healthcare.models.base import Base, TimestampMixin

# ── Master list of all departments in a full-service healthcare system ─────────
ALL_DEPARTMENTS = [
    # Primary Care
    {"name": "Primary Care", "category": "primary_care", "description": "General health maintenance and preventive care."},
    {"name": "Internal Medicine", "category": "primary_care", "description": "Adult disease diagnosis and non-surgical treatment."},
    {"name": "Family Medicine", "category": "primary_care", "description": "Comprehensive care for all ages."},
    {"name": "Urgent Care", "category": "primary_care", "description": "Walk-in care for non-life-threatening conditions."},
    {"name": "Geriatrics", "category": "primary_care", "description": "Healthcare for elderly patients."},
    {"name": "Adolescent Medicine", "category": "primary_care", "description": "Care for teenagers and young adults."},
    # Dentistry
    {"name": "General Dentistry", "category": "dentistry", "description": "Routine dental exams, cleanings, and fillings."},
    {"name": "Orthodontics", "category": "dentistry", "description": "Braces, aligners, and bite correction."},
    {"name": "Oral Surgery", "category": "dentistry", "description": "Extractions, implants, and jaw surgery."},
    {"name": "Pediatric Dentistry", "category": "dentistry", "description": "Dental care for children."},
    {"name": "Periodontics", "category": "dentistry", "description": "Gum disease treatment and prevention."},
    {"name": "Endodontics", "category": "dentistry", "description": "Root canals and pulp therapy."},
    {"name": "Prosthodontics", "category": "dentistry", "description": "Crowns, bridges, dentures, and implants."},
    # Emergency & Critical Care
    {"name": "Emergency Medicine", "category": "emergency", "description": "Immediate treatment for life-threatening emergencies."},
    {"name": "Intensive Care Unit", "category": "emergency", "description": "Critical care for seriously ill patients."},
    {"name": "Trauma Surgery", "category": "emergency", "description": "Surgical care for traumatic injuries."},
    # Cardiovascular
    {"name": "Cardiology", "category": "cardiovascular", "description": "Heart and blood vessel disorders."},
    {"name": "Cardiac Surgery", "category": "cardiovascular", "description": "Open-heart and bypass surgeries."},
    {"name": "Vascular Surgery", "category": "cardiovascular", "description": "Surgical treatment of blood vessel diseases."},
    # Neurology & Spine
    {"name": "Neurology", "category": "neurology", "description": "Brain, spinal cord, and nervous system disorders."},
    {"name": "Neurosurgery", "category": "neurology", "description": "Surgical treatment of neurological conditions."},
    {"name": "Spine Surgery", "category": "neurology", "description": "Surgical treatment of spinal disorders."},
    # Oncology
    {"name": "Medical Oncology", "category": "oncology", "description": "Cancer diagnosis and chemotherapy."},
    {"name": "Radiation Oncology", "category": "oncology", "description": "Radiation therapy for cancer treatment."},
    {"name": "Surgical Oncology", "category": "oncology", "description": "Surgical removal of tumors."},
    {"name": "Hematology", "category": "oncology", "description": "Blood disorders and blood cancers."},
    # Orthopedics & Musculoskeletal
    {"name": "Orthopedic Surgery", "category": "orthopedics", "description": "Bones, joints, and musculoskeletal surgery."},
    {"name": "Sports Medicine", "category": "orthopedics", "description": "Sports-related injuries and performance."},
    {"name": "Rheumatology", "category": "orthopedics", "description": "Autoimmune and inflammatory joint diseases."},
    {"name": "Podiatry", "category": "orthopedics", "description": "Foot and ankle care."},
    {"name": "Hand Surgery", "category": "orthopedics", "description": "Surgical care for hand and wrist conditions."},
    # Dermatology
    {"name": "Dermatology", "category": "dermatology", "description": "Skin, hair, and nail conditions."},
    {"name": "Plastic Surgery", "category": "dermatology", "description": "Reconstructive and cosmetic surgical procedures."},
    # Women's Health
    {"name": "OB/GYN", "category": "womens_health", "description": "Obstetrics, gynecology, and reproductive health."},
    {"name": "Maternal-Fetal Medicine", "category": "womens_health", "description": "High-risk pregnancies and fetal care."},
    {"name": "Reproductive Endocrinology", "category": "womens_health", "description": "Fertility treatments and hormonal disorders."},
    {"name": "Urogynecology", "category": "womens_health", "description": "Female pelvic floor disorders."},
    # Pediatrics
    {"name": "Pediatrics", "category": "pediatrics", "description": "Comprehensive medical care for children."},
    {"name": "Neonatology", "category": "pediatrics", "description": "Medical care for newborns, especially premature infants."},
    {"name": "Pediatric Cardiology", "category": "pediatrics", "description": "Heart conditions in children."},
    {"name": "Pediatric Surgery", "category": "pediatrics", "description": "Surgical care for infants and children."},
    # Behavioral & Mental Health
    {"name": "Psychiatry", "category": "behavioral_health", "description": "Mental health diagnosis and medication management."},
    {"name": "Psychology", "category": "behavioral_health", "description": "Psychotherapy and behavioral health counseling."},
    {"name": "Addiction Medicine", "category": "behavioral_health", "description": "Treatment for substance use disorders."},
    {"name": "Neuropsychology", "category": "behavioral_health", "description": "Cognitive and behavioral assessments."},
    # Imaging & Diagnostics
    {"name": "Radiology", "category": "diagnostics", "description": "X-rays, CT scans, MRIs, and imaging interpretation."},
    {"name": "Interventional Radiology", "category": "diagnostics", "description": "Minimally invasive image-guided procedures."},
    {"name": "Nuclear Medicine", "category": "diagnostics", "description": "Radioactive tracers for diagnosis and treatment."},
    {"name": "Pathology", "category": "diagnostics", "description": "Laboratory analysis of tissues and body fluids."},
    {"name": "Clinical Laboratory", "category": "diagnostics", "description": "Blood tests, cultures, and lab diagnostics."},
    # Surgery
    {"name": "General Surgery", "category": "surgery", "description": "Abdominal, breast, and general surgical procedures."},
    {"name": "Bariatric Surgery", "category": "surgery", "description": "Weight-loss and metabolic surgeries."},
    {"name": "Colorectal Surgery", "category": "surgery", "description": "Colon, rectal, and anal surgical treatments."},
    {"name": "Thoracic Surgery", "category": "surgery", "description": "Chest and lung surgical procedures."},
    {"name": "Transplant Surgery", "category": "surgery", "description": "Organ transplant procedures and follow-up care."},
    {"name": "Minimally Invasive Surgery", "category": "surgery", "description": "Laparoscopic and robotic-assisted surgeries."},
    # Rehabilitation
    {"name": "Physical Therapy", "category": "rehabilitation", "description": "Movement rehabilitation and injury recovery."},
    {"name": "Occupational Therapy", "category": "rehabilitation", "description": "Daily living skills and work rehabilitation."},
    {"name": "Speech Therapy", "category": "rehabilitation", "description": "Speech, language, and swallowing disorders."},
    {"name": "Cardiac Rehabilitation", "category": "rehabilitation", "description": "Recovery programs following heart procedures."},
    {"name": "Pain Management", "category": "rehabilitation", "description": "Chronic and acute pain treatment."},
    # Sensory & Specialty
    {"name": "Ophthalmology", "category": "specialty", "description": "Eye diseases, vision disorders, and surgery."},
    {"name": "Optometry", "category": "specialty", "description": "Vision testing and corrective lenses."},
    {"name": "ENT / Otolaryngology", "category": "specialty", "description": "Ear, nose, and throat disorders."},
    {"name": "Urology", "category": "specialty", "description": "Urinary tract and male reproductive health."},
    {"name": "Nephrology", "category": "specialty", "description": "Kidney diseases and dialysis."},
    {"name": "Endocrinology", "category": "specialty", "description": "Hormonal and metabolic disorders including diabetes."},
    {"name": "Gastroenterology", "category": "specialty", "description": "Digestive system disorders and endoscopy."},
    {"name": "Hepatology", "category": "specialty", "description": "Liver, gallbladder, and bile duct diseases."},
    {"name": "Pulmonology", "category": "specialty", "description": "Lung and respiratory diseases."},
    {"name": "Infectious Disease", "category": "specialty", "description": "Bacterial, viral, and parasitic infections."},
    {"name": "Allergy & Immunology", "category": "specialty", "description": "Allergies, asthma, and immune system disorders."},
    # Supportive & Ancillary Services
    {"name": "Pharmacy", "category": "ancillary", "description": "Prescription dispensing and medication counseling."},
    {"name": "Nutrition & Dietetics", "category": "ancillary", "description": "Clinical nutrition and dietary therapy."},
    {"name": "Social Work", "category": "ancillary", "description": "Psychosocial support and community resources."},
    {"name": "Case Management", "category": "ancillary", "description": "Care coordination and discharge planning."},
    {"name": "Palliative Care", "category": "ancillary", "description": "Comfort-focused care for serious illness."},
    {"name": "Hospice", "category": "ancillary", "description": "End-of-life care and support."},
    {"name": "Sleep Medicine", "category": "ancillary", "description": "Sleep disorders including apnea and insomnia."},
    {"name": "Wound Care", "category": "ancillary", "description": "Chronic wound treatment and hyperbaric therapy."},
    {"name": "Telehealth", "category": "ancillary", "description": "Virtual visits across all specialties."},
]


class Department(Base, TimestampMixin):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False, unique=True, index=True)
    category = Column(String(60), nullable=False, index=True)
    description = Column(Text, nullable=True)
    floor_location = Column(String(100), nullable=True)
    phone = Column(String(30), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<Department {self.name}>"


class Specialty(Base, TimestampMixin):
    """A specialist credential / sub-specialty that can be linked to providers."""
    __tablename__ = "specialties"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Specialty {self.name}>"
