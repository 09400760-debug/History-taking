from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
import random


@dataclass
class RubricSection:
    key: str
    label: str
    max_marks: int
    always_core: bool = False
    usually_core: bool = False
    activation_tags: Set[str] = field(default_factory=set)
    min_age_months: Optional[int] = None
    max_age_months: Optional[int] = None
    guidance: str = ""


RUBRIC_SECTIONS: Dict[str, RubricSection] = {
    "main_complaint": RubricSection(
        key="main_complaint",
        label="Main Complaint & Development of Symptoms",
        max_marks=25,
        always_core=True,
        guidance=(
            "Assess whether the student explored onset, duration, progression, severity, associated "
            "symptoms, triggers, relieving factors, and impact on feeding, sleep, play, function, "
            "or daily life. Strong performance should include at least 3 relevant follow-up questions."
        ),
    ),
    "danger_signs": RubricSection(
        key="danger_signs",
        label="Danger Signs",
        max_marks=2,
        always_core=True,
        guidance=(
            "Assess whether the student screened for important danger signs. Examples include "
            "convulsions, lethargy, poor feeding, vomiting everything, severe dehydration, reduced "
            "urine output, severe respiratory distress, and altered consciousness."
        ),
    ),
    "involved_system": RubricSection(
        key="involved_system",
        label="Involved System Focused History",
        max_marks=5,
        usually_core=True,
        guidance="Assess the depth and relevance of system-focused questions related to the presenting problem.",
    ),
    "other_systems": RubricSection(
        key="other_systems",
        label="Other Systems Enquiry",
        max_marks=3,
        usually_core=True,
        guidance=(
            "Assess whether the student screened appropriately across other systems, including weight loss, "
            "sleep, urinary and bowel habits, or other relevant non-primary system concerns."
        ),
    ),
    "birth_history": RubricSection(
        key="birth_history",
        label="Birth History",
        max_marks=5,
        activation_tags={"neonate", "infant", "development", "failure_to_thrive", "congenital", "seizure", "cardiac"},
        max_age_months=24,
        guidance=(
            "Activate especially in neonates, infants, developmental cases, congenital cases, poor growth, "
            "or seizures. Assess antenatal, perinatal, neonatal history, maternal illness, HIV/syphilis testing, "
            "and relevant PMTCT details."
        ),
    ),
    "immunisation": RubricSection(
        key="immunisation",
        label="Immunization",
        max_marks=3,
        activation_tags={"infectious", "fever", "respiratory", "rash", "cns", "infant"},
        max_age_months=60,
        guidance=(
            "Activate in younger children and many infectious or fever presentations. Assess whether the student "
            "checked immunisation status or asked to review the Road to Health card."
        ),
    ),
    "nutrition": RubricSection(
        key="nutrition",
        label="Nutrition",
        max_marks=3,
        activation_tags={"infant", "diarrhoea", "vomiting", "failure_to_thrive", "malnutrition", "nutrition", "infectious", "cardiac"},
        max_age_months=72,
        guidance=(
            "Activate in infants, feeding cases, diarrhoea/vomiting, malnutrition, poor growth, and cardiac "
            "failure-to-thrive cases. Assess breastfeeding, fluid intake, solids, missed meals, feeding practices, "
            "and relevant allergies or dietary issues."
        ),
    ),
    "past_history": RubricSection(
        key="past_history",
        label="Past Medical, Surgical, Medications & Allergies History",
        max_marks=5,
        usually_core=True,
        guidance=(
            "Assess whether the student asked about past medical history, prior admissions, surgery, medications, "
            "allergies, and traditional therapies."
        ),
    ),
    "family_history": RubricSection(
        key="family_history",
        label="Family Medical History",
        max_marks=3,
        usually_core=True,
        guidance=(
            "Assess whether the student asked about family illnesses, similar conditions, chronic disease, "
            "and TB exposure where relevant."
        ),
    ),
    "development": RubricSection(
        key="development",
        label="Developmental Milestones",
        max_marks=3,
        activation_tags={"development", "neurology", "failure_to_thrive", "chronic", "cerebral_palsy"},
        max_age_months=72,
        guidance=(
            "Activate in younger children and especially neurological, developmental, chronic, or poor-growth cases. "
            "Assess gross motor, fine motor, language, and social development."
        ),
    ),
    "social_history": RubricSection(
        key="social_history",
        label="Social History & Travel",
        max_marks=3,
        activation_tags={"infectious", "tb", "chronic", "environment", "diarrhoea", "respiratory", "renal", "nutrition"},
        guidance=(
            "Assess dwelling, who lives at home, siblings, social circumstances, school or crèche attendance, "
            "environmental risk, and travel where relevant."
        ),
    ),
    "assessment": RubricSection(
        key="assessment",
        label="Assessment from History",
        max_marks=20,
        always_core=True,
        guidance=(
            "Assess whether the student gave a logical summary and differential diagnosis, including at least one "
            "reasonable alternative differential."
        ),
    ),
    "empathy": RubricSection(
        key="empathy",
        label="Empathy",
        max_marks=5,
        always_core=True,
        guidance="Assess whether the student acknowledged caregiver emotion, listened actively, and responded supportively.",
    ),
    "communication": RubricSection(
        key="communication",
        label="Interview Technique, Communication Skills & Overall Impression",
        max_marks=15,
        always_core=True,
        guidance=(
            "Assess organisation, clarity, logical flow, open questioning where appropriate, summarising, "
            "professionalism, and overall interview quality."
        ),
    ),
}


COMMON_SA_CASE_BANK: List[Dict[str, Any]] = [
    # Respiratory
    {
        "id": "resp_001",
        "title": "Childhood pneumonia",
        "age_label": "2-year-old",
        "age_months": 24,
        "system": "Respiratory",
        "tags": {"infectious", "respiratory", "fever"},
        "context": "A 2-year-old child has cough, fever, and fast breathing for 3 days.",
        "expected_diagnosis": "Childhood pneumonia",
        "expected_differentials": [
            "Bronchiolitis",
            "Viral lower respiratory tract infection",
            "Acute asthma / wheeze-associated illness",
        ],
    },
    {
        "id": "resp_002",
        "title": "Bronchiolitis",
        "age_label": "6-month-old",
        "age_months": 6,
        "system": "Respiratory",
        "tags": {"infectious", "respiratory", "infant"},
        "context": "A 6-month-old infant has cough, difficulty breathing, poor feeding, and noisy breathing over 2 days.",
        "expected_diagnosis": "Bronchiolitis",
        "expected_differentials": [
            "Pneumonia",
            "Acute viral wheeze",
            "Congestive cardiac failure",
        ],
    },
    {
        "id": "resp_003",
        "title": "Stridor / viral croup",
        "age_label": "2-year-old",
        "age_months": 24,
        "system": "Respiratory",
        "tags": {"infectious", "respiratory", "fever"},
        "context": "A 2-year-old has a barking cough, noisy breathing, and fever after a viral illness.",
        "expected_diagnosis": "Viral croup",
        "expected_differentials": [
            "Epiglottitis",
            "Foreign body aspiration",
            "Bacterial tracheitis",
        ],
    },
    {
        "id": "resp_004",
        "title": "Pulmonary TB exposure with symptoms",
        "age_label": "5-year-old",
        "age_months": 60,
        "system": "Respiratory",
        "tags": {"infectious", "tb", "respiratory", "chronic"},
        "context": "A 5-year-old has chronic cough, weight loss, night sweats, and a household TB contact.",
        "expected_diagnosis": "Pulmonary tuberculosis",
        "expected_differentials": [
            "Chronic pneumonia",
            "HIV-related chronic lung disease",
            "Asthma",
        ],
    },
    {
        "id": "resp_005",
        "title": "Acute asthma exacerbation",
        "age_label": "8-year-old",
        "age_months": 96,
        "system": "Respiratory",
        "tags": {"respiratory", "chronic"},
        "context": "An 8-year-old with known asthma has worsening cough, wheeze, and shortness of breath since last night.",
        "expected_diagnosis": "Acute asthma exacerbation",
        "expected_differentials": [
            "Pneumonia",
            "Foreign body aspiration",
            "Viral-induced wheeze",
        ],
    },
    {
        "id": "resp_006",
        "title": "Pertussis",
        "age_label": "6-month-old",
        "age_months": 6,
        "system": "Respiratory",
        "tags": {"infectious", "respiratory", "infant", "fever"},
        "context": "A 6-month-old has severe coughing bouts and vomiting after coughing.",
        "expected_diagnosis": "Pertussis",
        "expected_differentials": [
            "Bronchiolitis",
            "Pneumonia",
            "Foreign body aspiration",
        ],
    },
    {
        "id": "resp_007",
        "title": "Foreign body aspiration",
        "age_label": "1-year-old",
        "age_months": 12,
        "system": "Respiratory",
        "tags": {"respiratory", "acute"},
        "context": "A 1-year-old developed sudden coughing and wheezing while playing.",
        "expected_diagnosis": "Foreign body aspiration",
        "expected_differentials": [
            "Acute asthma / wheeze",
            "Bronchiolitis",
            "Pneumonia",
        ],
    },

    # Gastrointestinal
    {
        "id": "gi_001",
        "title": "Acute gastroenteritis with dehydration",
        "age_label": "1-year-old",
        "age_months": 12,
        "system": "Gastrointestinal",
        "tags": {"infectious", "diarrhoea", "vomiting", "infant"},
        "context": "A 1-year-old has diarrhoea and vomiting for 2 days, reduced urine output, and poor oral intake.",
        "expected_diagnosis": "Acute gastroenteritis with dehydration",
        "expected_differentials": [
            "Sepsis",
            "Urinary tract infection",
            "Intussusception",
        ],
    },
    {
        "id": "gi_002",
        "title": "Dysentery",
        "age_label": "4-year-old",
        "age_months": 48,
        "system": "Gastrointestinal",
        "tags": {"infectious", "diarrhoea", "fever"},
        "context": "A 4-year-old has bloody diarrhoea, abdominal pain, and fever since yesterday.",
        "expected_diagnosis": "Dysentery",
        "expected_differentials": [
            "Severe bacterial gastroenteritis",
            "Inflammatory bowel disease",
            "Meckel diverticulum with bleeding",
        ],
    },
    {
        "id": "gi_003",
        "title": "Constipation with overflow symptoms",
        "age_label": "6-year-old",
        "age_months": 72,
        "system": "Gastrointestinal",
        "tags": {"gastrointestinal", "chronic"},
        "context": "A 6-year-old has abdominal pain, infrequent hard stools, and occasional soiling of underwear.",
        "expected_diagnosis": "Constipation with overflow soiling",
        "expected_differentials": [
            "Functional abdominal pain",
            "Hirschsprung disease",
            "Coeliac disease",
        ],
    },
    {
        "id": "gi_004",
        "title": "Acute hepatitis / jaundice-type presentation",
        "age_label": "9-year-old",
        "age_months": 108,
        "system": "Gastrointestinal",
        "tags": {"infectious", "gastrointestinal"},
        "context": "A 9-year-old has yellow eyes, dark urine, poor appetite, and tiredness.",
        "expected_diagnosis": "Acute hepatitis",
        "expected_differentials": [
            "Haemolysis",
            "Obstructive jaundice",
            "Drug-induced liver injury",
        ],
    },
    {
        "id": "gi_005",
        "title": "Appendicitis concern",
        "age_label": "10-year-old",
        "age_months": 120,
        "system": "Gastrointestinal",
        "tags": {"gastrointestinal", "fever", "vomiting"},
        "context": "A 10-year-old has worsening abdominal pain, fever, and vomiting since yesterday.",
        "expected_diagnosis": "Acute appendicitis",
        "expected_differentials": [
            "Mesenteric adenitis",
            "Gastroenteritis",
            "Urinary tract infection",
        ],
    },
    {
        "id": "gi_006",
        "title": "Gastro-oesophageal reflux with failure to thrive",
        "age_label": "4-month-old",
        "age_months": 4,
        "system": "Gastrointestinal",
        "tags": {"infant", "vomiting", "failure_to_thrive"},
        "context": "A 4-month-old frequently vomits after feeds and is not gaining weight well.",
        "expected_diagnosis": "Gastro-oesophageal reflux disease",
        "expected_differentials": [
            "Cow's milk protein allergy",
            "Pyloric stenosis",
            "Congenital heart disease",
        ],
    },

    # Neurological
    {
        "id": "neuro_001",
        "title": "Febrile seizure",
        "age_label": "18-month-old",
        "age_months": 18,
        "system": "Neurological",
        "tags": {"fever", "neurology", "infectious", "seizure"},
        "context": "An 18-month-old had a convulsion with fever today after 2 days of upper respiratory symptoms.",
        "expected_diagnosis": "Febrile seizure",
        "expected_differentials": [
            "Meningitis / encephalitis",
            "Epilepsy",
            "Electrolyte disturbance",
        ],
    },
    {
        "id": "neuro_002",
        "title": "Meningitis / meningoencephalitis concern",
        "age_label": "6-year-old",
        "age_months": 72,
        "system": "Neurological",
        "tags": {"infectious", "cns", "fever", "neurology"},
        "context": "A 6-year-old has fever, headache, vomiting, and increasing drowsiness.",
        "expected_diagnosis": "Meningitis / meningoencephalitis",
        "expected_differentials": [
            "Severe malaria depending on setting",
            "Brain abscess",
            "Raised intracranial pressure from another cause",
        ],
    },
    {
        "id": "neuro_003",
        "title": "Headache / migraine-type presentation",
        "age_label": "12-year-old",
        "age_months": 144,
        "system": "Neurological",
        "tags": {"neurology", "chronic"},
        "context": "A 12-year-old has recurrent headaches, sometimes with nausea and light sensitivity.",
        "expected_diagnosis": "Migraine",
        "expected_differentials": [
            "Tension headache",
            "Raised intracranial pressure",
            "Refractive error / visual strain",
        ],
    },
    {
        "id": "neuro_004",
        "title": "Epilepsy follow-up history",
        "age_label": "9-year-old",
        "age_months": 108,
        "system": "Neurological",
        "tags": {"neurology", "seizure", "chronic"},
        "context": "A 9-year-old with recurrent seizures is on chronic medication.",
        "expected_diagnosis": "Epilepsy",
        "expected_differentials": [
            "Breakthrough seizures from poor adherence",
            "Space-occupying lesion",
            "Metabolic cause of seizures",
        ],
    },
    {
        "id": "neuro_005",
        "title": "Possible raised ICP / brain tumour red flags",
        "age_label": "11-year-old",
        "age_months": 132,
        "system": "Neurological",
        "tags": {"neurology", "vomiting", "chronic"},
        "context": "An 11-year-old has early morning headaches, vomiting, and worsening school performance.",
        "expected_diagnosis": "Raised intracranial pressure / possible brain tumour",
        "expected_differentials": [
            "Migraine",
            "Chronic meningitis",
            "Idiopathic intracranial hypertension",
        ],
    },
    {
        "id": "neuro_006",
        "title": "Cerebral palsy functional history",
        "age_label": "5-year-old",
        "age_months": 60,
        "system": "Neurological",
        "tags": {"neurology", "development", "chronic", "cerebral_palsy"},
        "context": "A 5-year-old has stiffness, delayed walking, and functional difficulties at home.",
        "expected_diagnosis": "Cerebral palsy",
        "expected_differentials": [
            "Neuromuscular disorder",
            "Developmental delay from another cause",
            "Chronic encephalopathy",
        ],
    },

    # Renal
    {
        "id": "renal_001",
        "title": "Urinary tract infection",
        "age_label": "2-year-old",
        "age_months": 24,
        "system": "Renal",
        "tags": {"renal", "infectious", "fever", "vomiting"},
        "context": "A 2-year-old has fever, vomiting, irritability, and pain when passing urine.",
        "expected_diagnosis": "Urinary tract infection",
        "expected_differentials": [
            "Pyelonephritis",
            "Gastroenteritis",
            "Sepsis",
        ],
    },
    {
        "id": "renal_002",
        "title": "Pyelonephritis",
        "age_label": "6-year-old",
        "age_months": 72,
        "system": "Renal",
        "tags": {"renal", "infectious", "fever"},
        "context": "A 6-year-old girl has high fever, flank pain, vomiting, and burning when passing urine.",
        "expected_diagnosis": "Pyelonephritis",
        "expected_differentials": [
            "Lower urinary tract infection",
            "Appendicitis",
            "Acute glomerulonephritis",
        ],
    },
    {
        "id": "renal_003",
        "title": "Nephrotic syndrome",
        "age_label": "4-year-old",
        "age_months": 48,
        "system": "Renal",
        "tags": {"renal", "chronic"},
        "context": "A 4-year-old's face has looked puffy for a few days, and now the feet are also swollen.",
        "expected_diagnosis": "Nephrotic syndrome",
        "expected_differentials": [
            "Nephritic syndrome",
            "Cardiac failure",
            "Protein-losing enteropathy",
        ],
    },
    {
        "id": "renal_004",
        "title": "Acute nephritic syndrome",
        "age_label": "7-year-old",
        "age_months": 84,
        "system": "Renal",
        "tags": {"renal", "chronic"},
        "context": "A 7-year-old has cola-coloured urine, puffy eyes, and reduced urine output.",
        "expected_diagnosis": "Acute nephritic syndrome",
        "expected_differentials": [
            "Nephrotic syndrome",
            "Urinary tract infection",
            "Haemoglobinuria",
        ],
    },

    # General / other
    {
        "id": "gen_001",
        "title": "Possible neonatal sepsis",
        "age_label": "10-day-old",
        "age_months": 0,
        "system": "General Paediatrics",
        "tags": {"infectious", "neonate", "infant"},
        "context": "A 10-day-old baby is feeding poorly, sleepier than usual, and feels hot.",
        "expected_diagnosis": "Neonatal sepsis",
        "expected_differentials": [
            "Meningitis",
            "Urinary tract infection",
            "Congenital heart disease",
        ],
    },
    {
        "id": "gen_002",
        "title": "HIV-related recurrent infection / failure to thrive",
        "age_label": "18-month-old",
        "age_months": 18,
        "system": "General Paediatrics",
        "tags": {"infectious", "chronic", "failure_to_thrive", "infant"},
        "context": "An 18-month-old has poor weight gain, recurrent chest infections, oral thrush, and chronic diarrhoea.",
        "expected_diagnosis": "Possible HIV-related chronic illness / failure to thrive",
        "expected_differentials": [
            "Tuberculosis",
            "Primary immunodeficiency",
            "Severe malnutrition",
        ],
    },
    {
        "id": "gen_003",
        "title": "Severe acute malnutrition",
        "age_label": "14-month-old",
        "age_months": 14,
        "system": "General Paediatrics",
        "tags": {"malnutrition", "failure_to_thrive", "infectious", "infant", "nutrition"},
        "context": "A 14-month-old has visible weight loss, swelling of the feet, poor appetite, and recurrent diarrhoea.",
        "expected_diagnosis": "Severe acute malnutrition",
        "expected_differentials": [
            "Nephrotic syndrome",
            "Chronic HIV-related illness",
            "Protein-losing enteropathy",
        ],
    },
    {
        "id": "gen_004",
        "title": "Acyanotic congenital heart disease / heart failure symptoms",
        "age_label": "4-month-old",
        "age_months": 4,
        "system": "Cardiovascular",
        "tags": {"cardiac", "failure_to_thrive", "infant", "chronic", "congenital"},
        "context": "A 4-month-old baby sweats during feeds, breathes fast, and is not gaining weight well.",
        "expected_diagnosis": "Acyanotic congenital heart disease with cardiac failure",
        "expected_differentials": [
            "Chronic lung disease",
            "Severe reflux with failure to thrive",
            "Chronic infection",
        ],
    },
    {
        "id": "gen_005",
        "title": "Cyanotic congenital heart disease / Tetralogy of Fallot",
        "age_label": "2-year-old",
        "age_months": 24,
        "system": "Cardiovascular",
        "tags": {"cardiac", "chronic", "congenital"},
        "context": "A 2-year-old has episodes of becoming very blue, especially when upset, and squats afterwards.",
        "expected_diagnosis": "Tetralogy of Fallot / cyanotic congenital heart disease",
        "expected_differentials": [
            "Other cyanotic congenital heart disease",
            "Severe pulmonary disease",
            "Breath-holding spells",
        ],
    },
    {
        "id": "gen_006",
        "title": "Rickets",
        "age_label": "4-year-old",
        "age_months": 48,
        "system": "Musculoskeletal",
        "tags": {"chronic", "nutrition", "musculoskeletal"},
        "context": "A 4-year-old has bowed legs, delayed walking confidence, and weakness.",
        "expected_diagnosis": "Rickets",
        "expected_differentials": [
            "Blount disease",
            "Neuromuscular disorder",
            "Cerebral palsy",
        ],
    },
    {
        "id": "gen_007",
        "title": "Congenital syphilis",
        "age_label": "1-month-old",
        "age_months": 1,
        "system": "General Paediatrics",
        "tags": {"infectious", "neonate", "infant", "congenital"},
        "context": "A 1-month-old has persistent snuffles, poor feeding, and a rash.",
        "expected_diagnosis": "Congenital syphilis",
        "expected_differentials": [
            "Neonatal sepsis",
            "Congenital viral infection",
            "Allergic / dermatological condition with poor feeding",
        ],
    },
]


DEFAULT_CAREGIVER_BY_CASE: Dict[str, tuple] = {
    "Childhood pneumonia": ("female", "mother", "Thandeka", "Sipho", "male"),
    "Bronchiolitis": ("female", "mother", "Lerato", "Amahle", "female"),
    "Stridor / viral croup": ("female", "mother", "Nomsa", "Kabelo", "male"),
    "Pulmonary TB exposure with symptoms": ("female", "grandmother", "Gogo Nandi", "Sanele", "male"),
    "Acute asthma exacerbation": ("female", "mother", "Ayanda", "Neo", "male"),
    "Pertussis": ("female", "mother", "Busi", "Anele", "female"),
    "Foreign body aspiration": ("female", "mother", "Zinhle", "Musa", "male"),
    "Acute gastroenteritis with dehydration": ("female", "mother", "Palesa", "Lethabo", "male"),
    "Dysentery": ("male", "father", "Sizwe", "Aphiwe", "female"),
    "Constipation with overflow symptoms": ("female", "mother", "Nokuthula", "Mvelo", "male"),
    "Acute hepatitis / jaundice-type presentation": ("female", "mother", "Zola", "Tumi", "male"),
    "Appendicitis concern": ("female", "mother", "Khanyi", "Mia", "female"),
    "Gastro-oesophageal reflux with failure to thrive": ("female", "mother", "Pretty", "Lulu", "female"),
    "Febrile seizure": ("female", "mother", "Zanele", "Lwazi", "male"),
    "Meningitis / meningoencephalitis concern": ("male", "father", "Mandla", "Asanda", "female"),
    "Headache / migraine-type presentation": ("female", "mother", "Nandi", "Yanga", "female"),
    "Epilepsy follow-up history": ("female", "aunt", "Nomfundo", "Sibusiso", "male"),
    "Possible raised ICP / brain tumour red flags": ("female", "mother", "Fikile", "Karabo", "male"),
    "Cerebral palsy functional history": ("female", "mother", "Ntombi", "Luyolo", "male"),
    "Urinary tract infection": ("female", "mother", "Refilwe", "Naledi", "female"),
    "Pyelonephritis": ("female", "mother", "Mpho", "Boitumelo", "female"),
    "Nephrotic syndrome": ("female", "mother", "Dudu", "Samkelo", "male"),
    "Acute nephritic syndrome": ("male", "father", "Vusi", "Kwanele", "female"),
    "Possible neonatal sepsis": ("female", "mother", "Sibongile", "Baby Aphiwe", "female"),
    "HIV-related recurrent infection / failure to thrive": ("female", "mother", "Hlengiwe", "Siyabonga", "male"),
    "Severe acute malnutrition": ("female", "grandmother", "Gogo Thoko", "Bokang", "male"),
    "Acyanotic congenital heart disease / heart failure symptoms": ("female", "mother", "Mbali", "Enzo", "male"),
    "Cyanotic congenital heart disease / Tetralogy of Fallot": ("female", "mother", "Zama", "Tshepiso", "male"),
    "Rickets": ("female", "mother", "Puleng", "Asemahle", "female"),
    "Congenital syphilis": ("female", "mother", "Thembi", "Baby Sethu", "male"),
}


CASE_SOCIALS: Dict[str, Dict[str, str]] = {
    "Respiratory": {
        "siblings": "He has one older sibling at home.",
        "residence": "We live in Soweto in a brick house with family.",
        "birth_place": "He was born at Chris Hani Baragwanath Academic Hospital.",
        "household_structure": "At home it is me, the child, one sibling, and his grandmother.",
        "school_or_daycare": "He attends crèche during the week.",
        "caregiver_occupation": "I work as a shop assistant.",
    },
    "Gastrointestinal": {
        "siblings": "She has two siblings, both older.",
        "residence": "We live in Alexandra in a family home.",
        "birth_place": "She was born at Rahima Moosa Mother and Child Hospital.",
        "household_structure": "At home it is me, the child, two siblings, and their father.",
        "school_or_daycare": "She goes to crèche on weekdays.",
        "caregiver_occupation": "I do domestic work.",
    },
    "Neurological": {
        "siblings": "He has one younger sister.",
        "residence": "We live in Tembisa with family.",
        "birth_place": "He was born at Tembisa Hospital.",
        "household_structure": "At home it is me, the child, his sister, and his grandmother.",
        "school_or_daycare": "He is in Grade 3 at school.",
        "caregiver_occupation": "I work in a supermarket.",
    },
    "Renal": {
        "siblings": "She has one older brother.",
        "residence": "We live in Katlehong in a family house.",
        "birth_place": "She was born at Thelle Mogoerane Regional Hospital.",
        "household_structure": "At home it is me, the child, her brother, and their aunt.",
        "school_or_daycare": "She is in Grade 1 at school.",
        "caregiver_occupation": "I work as a cashier.",
    },
    "Cardiovascular": {
        "siblings": "He is the first child.",
        "residence": "We live in Johannesburg South in a flat.",
        "birth_place": "He was born at Charlotte Maxeke Johannesburg Academic Hospital.",
        "household_structure": "At home it is me, the baby, and his father.",
        "school_or_daycare": "He is not yet in school.",
        "caregiver_occupation": "I am currently at home with the baby.",
    },
    "Musculoskeletal": {
        "siblings": "She has one older sister.",
        "residence": "We live in Diepsloot with family.",
        "birth_place": "She was born at Leratong Hospital.",
        "household_structure": "At home it is me, the child, her sister, and their grandmother.",
        "school_or_daycare": "She attends preschool.",
        "caregiver_occupation": "I sell clothes from home.",
    },
    "General Paediatrics": {
        "siblings": "The baby has no siblings.",
        "residence": "We live in Orange Farm with family.",
        "birth_place": "The baby was born at a public hospital in Johannesburg.",
        "household_structure": "At home it is me, the baby, and family members.",
        "school_or_daycare": "The baby is not yet in school.",
        "caregiver_occupation": "I am currently at home with the baby.",
    },
}


def _age_matches(section: RubricSection, age_months: int) -> bool:
    if section.min_age_months is not None and age_months < section.min_age_months:
        return False
    if section.max_age_months is not None and age_months > section.max_age_months:
        return False
    return True


def get_active_rubric(case_data: Dict[str, Any]) -> List[RubricSection]:
    age_months = int(case_data.get("age_months", 60))
    case_tags = set(case_data.get("tags", set()))

    active_sections: List[RubricSection] = []

    for section in RUBRIC_SECTIONS.values():
        if section.always_core:
            active_sections.append(section)
            continue

        if section.usually_core:
            active_sections.append(section)
            continue

        if section.activation_tags and (section.activation_tags & case_tags) and _age_matches(section, age_months):
            active_sections.append(section)

    return active_sections


def get_active_rubric_summary(case_data: Dict[str, Any]) -> Dict[str, Any]:
    active = get_active_rubric(case_data)
    total_possible = sum(section.max_marks for section in active)

    return {
        "sections": [
            {
                "key": section.key,
                "label": section.label,
                "max_marks": section.max_marks,
                "guidance": section.guidance,
            }
            for section in active
        ],
        "raw_total_possible": total_possible,
    }


def renormalise_score(raw_score: float, raw_total_possible: float) -> float:
    if raw_total_possible <= 0:
        return 0.0
    return round((raw_score / raw_total_possible) * 100, 1)


def _enrich_case(case: Dict[str, Any]) -> Dict[str, Any]:
    enriched = dict(case)

    gender, role, caregiver_name, child_name, child_sex = DEFAULT_CAREGIVER_BY_CASE.get(
        enriched["title"],
        ("female", "mother", "Zanele", "Musa", "male"),
    )

    socials = CASE_SOCIALS.get(enriched["system"], CASE_SOCIALS.get("General Paediatrics", {}))
    child_age = enriched["age_label"].replace("-old", "")

    enriched["caregiver_gender"] = gender
    enriched["caregiver_role"] = role
    enriched["caregiver_name"] = caregiver_name
    enriched["child_name"] = child_name
    enriched["child_age"] = child_age
    enriched["child_sex"] = child_sex
    enriched["presenting_complaint"] = enriched["title"]
    enriched["case_summary"] = enriched["context"]
    enriched["opening_line"] = f"Hello doctor, I'm {caregiver_name}, {child_name}'s {role}."
    enriched["siblings"] = socials.get("siblings", "The child has siblings at home.")
    enriched["residence"] = socials.get("residence", "We live with family in Johannesburg.")
    enriched["birth_place"] = socials.get("birth_place", "The child was born at a public hospital.")
    enriched["household_structure"] = socials.get("household_structure", "We live with family at home.")
    enriched["school_or_daycare"] = socials.get("school_or_daycare", "The child attends school or crèche.")
    enriched["caregiver_occupation"] = socials.get("caregiver_occupation", "I work nearby.")

    return enriched


def choose_case(
    requested_system: Optional[str] = None,
    requested_title: Optional[str] = None,
) -> Dict[str, Any]:
    candidates = COMMON_SA_CASE_BANK

    if requested_system and requested_system.lower() != "random":
        filtered = [case for case in candidates if case["system"].lower() == requested_system.lower()]
        if filtered:
            candidates = filtered

    if requested_title:
        matches = [case for case in candidates if requested_title.lower() in case["title"].lower()]
        if matches:
            candidates = matches

    return _enrich_case(random.choice(candidates))


def build_assessor_schema(case_data: Dict[str, Any]) -> Dict[str, Any]:
    active = get_active_rubric(case_data)
    raw_total = sum(section.max_marks for section in active)

    return {
        "case_metadata": {
            "case_id": case_data.get("id"),
            "title": case_data.get("title"),
            "age_label": case_data.get("age_label"),
            "age_months": case_data.get("age_months"),
            "system": case_data.get("system"),
            "tags": sorted(list(case_data.get("tags", []))),
            "context": case_data.get("context"),
            "expected_diagnosis": case_data.get("expected_diagnosis"),
            "expected_differentials": case_data.get("expected_differentials", []),
        },
        "rubric": {
            "scoring_model": "dynamic_case_activated_rubric",
            "raw_total_possible": raw_total,
            "final_total_after_renormalisation": 100,
            "sections": [
                {
                    "key": section.key,
                    "label": section.label,
                    "max_marks": section.max_marks,
                    "guidance": section.guidance,
                }
                for section in active
            ],
        },
    }


def build_history_taking_system_prompt(case_data: Dict[str, Any]) -> str:
    return f"""
You are role-playing a caregiver in a paediatric history-taking practice case in South Africa.

IMPORTANT PURPOSE OF THIS STATION:
- This station is about history-taking and diagnostic reasoning.
- It is NOT a management or counselling station.
- Do not steer the student toward treatment or management questions.

CURRENT CASE:
- Title: {case_data.get("title")}
- Age: {case_data.get("age_label")}
- System: {case_data.get("system")}
- Hidden clinical picture: {case_data.get("context")}

KNOWN FACTS:
- Caregiver name: {case_data.get("caregiver_name")}
- Caregiver role: {case_data.get("caregiver_role")}
- Caregiver occupation: {case_data.get("caregiver_occupation")}
- Child name: {case_data.get("child_name")}
- Child age: {case_data.get("child_age")}
- Child sex: {case_data.get("child_sex")}
- Presenting complaint: {case_data.get("presenting_complaint")}
- Siblings: {case_data.get("siblings")}
- Residence: {case_data.get("residence")}
- Birth place: {case_data.get("birth_place")}
- Household structure: {case_data.get("household_structure")}
- School/daycare: {case_data.get("school_or_daycare")}

ROLEPLAY RULES:
- Start naturally by greeting the student as doctor and briefly introducing yourself and the child.
- Do not volunteer the whole history at once.
- Only reveal information when asked.
- Answer like a real caregiver, not like a textbook.
- Show appropriate concern and realism.
- Keep answers short to moderate.
- If the student asks unclear or jargon-heavy questions, ask for clarification.
- Do not give the diagnosis unless specifically asked what you were told.
- Maintain internal consistency throughout the case.
- Never behave like a clinician or assistant.
- Never ask the student what the problem is with the child.
- Do not shift the interaction toward management.
- Do not ask what treatment is needed, whether the child will be admitted, or what medicines are required unless the student explicitly raises management.
- If the student asks management-focused questions, answer briefly and neutrally, but do not let management become the focus of the station.
""".strip()


def build_assessor_system_prompt(case_data: Dict[str, Any], detailed: bool = False) -> str:
    schema = build_assessor_schema(case_data)
    active_sections = schema["rubric"]["sections"]
    raw_total_possible = schema["rubric"]["raw_total_possible"]

    section_lines = []
    for section in active_sections:
        section_lines.append(f"- {section['label']} ({section['max_marks']}): {section['guidance']}")

    joined_sections = "\n".join(section_lines)

    detail_instruction = (
        "Give fuller section-by-section reasoning and practical educational feedback."
        if detailed
        else
        "Keep the feedback concise, specific, and high-yield."
    )

    expected_differentials = case_data.get("expected_differentials", [])

    return f"""
You are an expert assessor for a paediatric history-taking encounter using a dynamic Wits-style rubric.

THIS STATION TESTS:
- the student's ability to take a thorough relevant history
- their ability to build a diagnostic picture from the history
- their ability to state a likely diagnosis and reasonable differentials

THIS STATION DOES NOT TEST:
- management planning
- treatment counselling
- disposition planning

IMPORTANT:
- Score ONLY the activated sections below.
- Do NOT penalise the student for rubric sections that are not activated for this case.
- Judge only the transcript evidence.
- Do not reward management discussion unless it directly helps diagnostic reasoning.
- After assigning raw section scores, calculate:
  final_score_out_of_100 = (raw_score_total / raw_total_possible) * 100
- Round the final score to 1 decimal place.

TRUE CASE DIAGNOSIS:
{case_data.get("expected_diagnosis")}

IMPORTANT EXPECTED DIFFERENTIAL DIAGNOSES:
{expected_differentials}

CASE:
- Title: {case_data.get("title")}
- Age: {case_data.get("age_label")}
- System: {case_data.get("system")}
- Hidden clinical picture: {case_data.get("context")}

ACTIVATED RUBRIC SECTIONS:
{joined_sections}

RAW TOTAL POSSIBLE:
{raw_total_possible}

OUTPUT RULES:
- Return valid JSON only.
- Include these top-level keys exactly:
  case_summary
  true_case_diagnosis
  important_expected_differentials
  scores
  raw_score_total
  raw_total_possible
  final_score_out_of_100
  strengths
  missed_opportunities
  overall_feedback

FOR EACH SECTION IN scores:
- include score
- include max_marks
- include reasoning

STYLE:
- Be fair, specific, and educational.
- Reward relevant prioritisation and not just checklist behaviour.
- Explicitly comment on how well the student's history supports or misses the true diagnosis and differentials.
- {detail_instruction}
""".strip()


def build_case_display_text(case_data: Dict[str, Any]) -> str:
    return (
        f"{case_data.get('title')} | {case_data.get('age_label')} | "
        f"{case_data.get('system')}\n\n"
        f"{case_data.get('context')}"
    )


if __name__ == "__main__":
    example_case = choose_case(requested_system="Random")
    print(build_case_display_text(example_case))
    print(get_active_rubric_summary(example_case))
