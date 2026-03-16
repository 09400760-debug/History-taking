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
            "Assess whether the student explored onset, duration, progression, characteristics, "
            "triggers, relieving factors, severity, and impact on daily life. Strong performance "
            "should include at least 3 relevant follow-up questions."
        ),
    ),
    "danger_signs": RubricSection(
        key="danger_signs",
        label="Danger Signs",
        max_marks=2,
        always_core=True,
        guidance=(
            "Assess whether the student screened for important danger signs such as convulsions, "
            "lethargy, vomiting everything, not taking feeds, and system-specific danger signs."
        ),
    ),
    "involved_system": RubricSection(
        key="involved_system",
        label="Involved System Focused History",
        max_marks=5,
        usually_core=True,
        guidance="Assess depth and relevance of system-focused questions related to the presenting problem.",
    ),
    "other_systems": RubricSection(
        key="other_systems",
        label="Other Systems Enquiry",
        max_marks=3,
        usually_core=True,
        guidance=(
            "Assess whether the student screened appropriately across other systems, including items "
            "such as sleep, bowel/urinary habits, weight loss, or screen time where relevant."
        ),
    ),
    "birth_history": RubricSection(
        key="birth_history",
        label="Birth History",
        max_marks=5,
        activation_tags={"neonate", "infant", "development", "failure_to_thrive", "congenital", "seizure"},
        max_age_months=24,
        guidance=(
            "Activate especially in neonates, infants, developmental concerns, poor growth, congenital "
            "concerns, or seizures. Assess antenatal, perinatal, neonatal history, maternal illness, "
            "HIV/syphilis testing, and Road to Health Booklet."
        ),
    ),
    "immunisation": RubricSection(
        key="immunisation",
        label="Immunization",
        max_marks=3,
        activation_tags={"infectious", "fever", "respiratory", "rash", "cns"},
        max_age_months=60,
        guidance=(
            "Activate in most younger children and infectious/rash/fever cases. Assess whether the "
            "student checked immunisation status or asked to review the Road to Health Booklet/card."
        ),
    ),
    "nutrition": RubricSection(
        key="nutrition",
        label="Nutrition",
        max_marks=3,
        activation_tags={"infant", "diarrhoea", "vomiting", "failure_to_thrive", "malnutrition", "infectious"},
        max_age_months=60,
        guidance=(
            "Activate for infants, feeding, diarrhoea/vomiting, growth concerns, and many infectious "
            "presentations. Assess breastfeeding, fluid intake, missed meals, feeding practices, and "
            "allergies/intolerances."
        ),
    ),
    "past_history": RubricSection(
        key="past_history",
        label="Past Medical, Surgical, Medications & Allergies History",
        max_marks=5,
        usually_core=True,
        guidance=(
            "Assess whether the student asked about past illnesses, admissions, surgery, medications, "
            "allergies, and traditional therapies."
        ),
    ),
    "family_history": RubricSection(
        key="family_history",
        label="Family Medical History",
        max_marks=3,
        usually_core=True,
        guidance="Assess whether the student asked about family illnesses, including TB exposure where relevant.",
    ),
    "development": RubricSection(
        key="development",
        label="Developmental Milestones",
        max_marks=3,
        activation_tags={"neurology", "development", "failure_to_thrive", "chronic"},
        max_age_months=72,
        guidance=(
            "Activate for younger children and especially neurological, developmental, chronic, and "
            "poor-growth cases. Assess gross motor, fine motor, language, and social milestones."
        ),
    ),
    "social_history": RubricSection(
        key="social_history",
        label="Social History & Travel",
        max_marks=3,
        activation_tags={"infectious", "tb", "chronic", "environment", "diarrhoea", "respiratory", "renal"},
        guidance=(
            "Assess dwelling, caregivers, siblings, grants/income, environmental exposures, travel, "
            "and relevant day-care/school context."
        ),
    ),
    "assessment": RubricSection(
        key="assessment",
        label="Assessment from History",
        max_marks=20,
        always_core=True,
        guidance=(
            "Assess whether the student gave a logical summary and differential diagnosis, including "
            "at least one reasonable alternative differential."
        ),
    ),
    "empathy": RubricSection(
        key="empathy",
        label="Empathy",
        max_marks=5,
        always_core=True,
        guidance=(
            "Assess whether the student acknowledged caregiver emotion, listened actively, and "
            "responded supportively."
        ),
    ),
    "communication": RubricSection(
        key="communication",
        label="Interview Technique, Communication Skills & Overall Impression",
        max_marks=15,
        always_core=True,
        guidance=(
            "Assess organisation, clarity, logical flow, open questions, summarising, and overall "
            "interview quality."
        ),
    ),
}


COMMON_SA_CASE_BANK: List[Dict[str, Any]] = [
    {
        "id": "resp_001",
        "title": "Childhood pneumonia",
        "age_label": "2-year-old",
        "age_months": 24,
        "system": "Respiratory",
        "tags": {"infectious", "respiratory", "fever"},
        "context": (
            "You are speaking to the mother of a 2-year-old child with cough, fever, and fast breathing "
            "for 3 days. The child is drinking less than usual and has been less active."
        ),
    },
    {
        "id": "resp_002",
        "title": "Bronchiolitis",
        "age_label": "6-month-old",
        "age_months": 6,
        "system": "Respiratory",
        "tags": {"infectious", "respiratory", "infant"},
        "context": (
            "You are speaking to the caregiver of a 6-month-old infant with cough, difficulty breathing, "
            "poor feeding, and noisy breathing over 2 days."
        ),
    },
    {
        "id": "resp_003",
        "title": "Stridor / viral croup",
        "age_label": "2-year-old",
        "age_months": 24,
        "system": "Respiratory",
        "tags": {"infectious", "respiratory", "fever"},
        "context": (
            "You are speaking to the parent of a 2-year-old with a barking cough, noisy breathing, "
            "and fever after a viral illness."
        ),
    },
    {
        "id": "resp_004",
        "title": "Pulmonary TB exposure with symptoms",
        "age_label": "5-year-old",
        "age_months": 60,
        "system": "Respiratory",
        "tags": {"infectious", "tb", "respiratory", "chronic"},
        "context": (
            "You are speaking to the grandmother of a 5-year-old with chronic cough, weight loss, "
            "night sweats, and a household TB contact."
        ),
    },
    {
        "id": "resp_005",
        "title": "Acute asthma exacerbation",
        "age_label": "8-year-old",
        "age_months": 96,
        "system": "Respiratory",
        "tags": {"respiratory", "chronic"},
        "context": (
            "You are speaking to the mother of an 8-year-old with known asthma who has worsening cough, "
            "wheeze, and shortness of breath since last night."
        ),
    },
    {
        "id": "resp_006",
        "title": "Pertussis",
        "age_label": "6-month-old",
        "age_months": 6,
        "system": "Respiratory",
        "tags": {"infectious", "respiratory", "infant", "fever"},
        "context": (
            "You are speaking to the caregiver of a 6-month-old with severe coughing bouts, vomiting after "
            "coughing, and difficulty settling."
        ),
    },
    {
        "id": "resp_007",
        "title": "Foreign body aspiration",
        "age_label": "1-year-old",
        "age_months": 12,
        "system": "Respiratory",
        "tags": {"respiratory", "acute"},
        "context": (
            "You are speaking to the caregiver of a 1-year-old with sudden-onset cough and wheeze after "
            "playing at home."
        ),
    },
    {
        "id": "gi_001",
        "title": "Acute gastroenteritis with dehydration",
        "age_label": "1-year-old",
        "age_months": 12,
        "system": "Gastrointestinal",
        "tags": {"infectious", "diarrhoea", "vomiting", "infant"},
        "context": (
            "You are speaking to the caregiver of a 1-year-old with diarrhoea and vomiting for 2 days, "
            "reduced urine output, and poor oral intake."
        ),
    },
    {
        "id": "gi_002",
        "title": "Dysentery",
        "age_label": "4-year-old",
        "age_months": 48,
        "system": "Gastrointestinal",
        "tags": {"infectious", "diarrhoea", "fever"},
        "context": (
            "You are speaking to the parent of a 4-year-old with bloody diarrhoea, abdominal pain, "
            "and fever since yesterday."
        ),
    },
    {
        "id": "gi_003",
        "title": "Constipation with overflow symptoms",
        "age_label": "6-year-old",
        "age_months": 72,
        "system": "Gastrointestinal",
        "tags": {"gastrointestinal", "chronic"},
        "context": (
            "You are speaking to the mother of a 6-year-old with abdominal pain, infrequent hard stools, "
            "and occasional soiling of underwear."
        ),
    },
    {
        "id": "gi_004",
        "title": "Acute hepatitis / jaundice-type presentation",
        "age_label": "9-year-old",
        "age_months": 108,
        "system": "Gastrointestinal",
        "tags": {"infectious", "gastrointestinal"},
        "context": (
            "You are speaking to the caregiver of a 9-year-old with yellow eyes, dark urine, poor appetite, "
            "and tiredness."
        ),
    },
    {
        "id": "gi_005",
        "title": "Appendicitis concern",
        "age_label": "10-year-old",
        "age_months": 120,
        "system": "Gastrointestinal",
        "tags": {"gastrointestinal", "fever", "vomiting"},
        "context": (
            "You are speaking to the parent of a 10-year-old with worsening abdominal pain, fever, "
            "and vomiting since yesterday."
        ),
    },
    {
        "id": "gi_006",
        "title": "Gastro-oesophageal reflux with failure to thrive",
        "age_label": "4-month-old",
        "age_months": 4,
        "system": "Gastrointestinal",
        "tags": {"infant", "vomiting", "failure_to_thrive"},
        "context": (
            "You are speaking to the mother of a 4-month-old who frequently vomits after feeds and is not "
            "gaining weight well."
        ),
    },
    {
        "id": "neuro_001",
        "title": "Febrile seizure",
        "age_label": "18-month-old",
        "age_months": 18,
        "system": "Neurological",
        "tags": {"fever", "neurology", "infectious", "seizure"},
        "context": (
            "You are speaking to the caregiver of an 18-month-old who had a convulsion with fever today "
            "after 2 days of upper respiratory symptoms."
        ),
    },
    {
        "id": "neuro_002",
        "title": "Meningitis / meningoencephalitis concern",
        "age_label": "6-year-old",
        "age_months": 72,
        "system": "Neurological",
        "tags": {"infectious", "cns", "fever", "neurology"},
        "context": (
            "You are speaking to the parent of a 6-year-old with fever, headache, vomiting, "
            "and increasing drowsiness."
        ),
    },
    {
        "id": "neuro_003",
        "title": "Headache / migraine-type presentation",
        "age_label": "12-year-old",
        "age_months": 144,
        "system": "Neurological",
        "tags": {"neurology", "chronic"},
        "context": (
            "You are speaking to the mother of a 12-year-old with recurrent headaches, sometimes with nausea "
            "and light sensitivity."
        ),
    },
    {
        "id": "neuro_004",
        "title": "Epilepsy follow-up history",
        "age_label": "9-year-old",
        "age_months": 108,
        "system": "Neurological",
        "tags": {"neurology", "seizure", "chronic"},
        "context": (
            "You are speaking to the caregiver of a 9-year-old with recurrent seizures who is on chronic medication."
        ),
    },
    {
        "id": "neuro_005",
        "title": "Possible raised ICP / brain tumour red flags",
        "age_label": "11-year-old",
        "age_months": 132,
        "system": "Neurological",
        "tags": {"neurology", "vomiting", "chronic"},
        "context": (
            "You are speaking to the parent of an 11-year-old with early morning headaches, vomiting, "
            "and worsening school performance."
        ),
    },
    {
        "id": "neuro_006",
        "title": "Cerebral palsy functional history",
        "age_label": "5-year-old",
        "age_months": 60,
        "system": "Neurological",
        "tags": {"neurology", "development", "chronic"},
        "context": (
            "You are speaking to the caregiver of a 5-year-old with stiffness, delayed walking, "
            "and functional difficulties at home."
        ),
    },
    {
        "id": "renal_001",
        "title": "Urinary tract infection",
        "age_label": "2-year-old",
        "age_months": 24,
        "system": "Renal",
        "tags": {"renal", "infectious", "fever", "vomiting"},
        "context": (
            "You are speaking to the parent of a 2-year-old with fever, vomiting, irritability, "
            "and pain when passing urine."
        ),
    },
    {
        "id": "renal_002",
        "title": "Pyelonephritis",
        "age_label": "6-year-old",
        "age_months": 72,
        "system": "Renal",
        "tags": {"renal", "infectious", "fever"},
        "context": (
            "You are speaking to the mother of a 6-year-old girl with high fever, flank pain, vomiting, "
            "and burning when passing urine."
        ),
    },
    {
        "id": "renal_003",
        "title": "Nephrotic syndrome",
        "age_label": "4-year-old",
        "age_months": 48,
        "system": "Renal",
        "tags": {"renal", "chronic"},
        "context": (
            "You are speaking to the mother of a 4-year-old whose face has looked puffy for a few days, "
            "and now the feet are also swollen."
        ),
    },
    {
        "id": "renal_004",
        "title": "Acute nephritic syndrome",
        "age_label": "7-year-old",
        "age_months": 84,
        "system": "Renal",
        "tags": {"renal", "chronic"},
        "context": (
            "You are speaking to the parent of a 7-year-old with cola-coloured urine, puffy eyes, "
            "and reduced urine output."
        ),
    },
    {
        "id": "gen_001",
        "title": "Possible neonatal sepsis",
        "age_label": "10-day-old",
        "age_months": 0,
        "system": "General Paediatrics",
        "tags": {"infectious", "neonate", "infant"},
        "context": (
            "You are speaking to the mother of a 10-day-old baby who is feeding poorly, "
            "sleepier than usual, and feels hot."
        ),
    },
    {
        "id": "gen_002",
        "title": "HIV-related recurrent infection / failure to thrive",
        "age_label": "18-month-old",
        "age_months": 18,
        "system": "General Paediatrics",
        "tags": {"infectious", "chronic", "failure_to_thrive", "infant"},
        "context": (
            "You are speaking to the mother of an 18-month-old with poor weight gain, recurrent chest infections, "
            "oral thrush, and chronic diarrhoea."
        ),
    },
    {
        "id": "gen_003",
        "title": "Severe acute malnutrition",
        "age_label": "14-month-old",
        "age_months": 14,
        "system": "General Paediatrics",
        "tags": {"malnutrition", "failure_to_thrive", "infectious", "infant"},
        "context": (
            "You are speaking to the caregiver of a 14-month-old with visible weight loss, "
            "swelling of the feet, poor appetite, and recurrent diarrhoea."
        ),
    },
    {
        "id": "gen_004",
        "title": "Acyanotic congenital heart disease / heart failure symptoms",
        "age_label": "4-month-old",
        "age_months": 4,
        "system": "Cardiovascular",
        "tags": {"cardiac", "failure_to_thrive", "infant", "chronic"},
        "context": (
            "You are speaking to the mother of a 4-month-old baby who sweats during feeds, "
            "breathes fast, and is not gaining weight well."
        ),
    },
    {
        "id": "gen_005",
        "title": "Cyanotic congenital heart disease / Tetralogy of Fallot",
        "age_label": "2-year-old",
        "age_months": 24,
        "system": "Cardiovascular",
        "tags": {"cardiac", "chronic"},
        "context": (
            "You are speaking to the parent of a 2-year-old with episodes of becoming very blue, "
            "especially when upset, and squatting afterwards."
        ),
    },
    {
        "id": "gen_006",
        "title": "Rickets",
        "age_label": "4-year-old",
        "age_months": 48,
        "system": "Musculoskeletal",
        "tags": {"chronic", "nutrition", "musculoskeletal"},
        "context": (
            "You are speaking to the caregiver of a 4-year-old with bowed legs, delayed walking confidence, "
            "and weakness."
        ),
    },
    {
        "id": "gen_007",
        "title": "Congenital syphilis",
        "age_label": "1-month-old",
        "age_months": 1,
        "system": "General Paediatrics",
        "tags": {"infectious", "neonate", "infant", "congenital"},
        "context": (
            "You are speaking to the mother of a 1-month-old with persistent snuffles, poor feeding, "
            "and a rash."
        ),
    },
}


DEFAULT_CAREGIVER_BY_CASE = {
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


CASE_SOCIALS = {
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
    total_possible = sum(s.max_marks for s in active)

    return {
        "sections": [
            {
                "key": s.key,
                "label": s.label,
                "max_marks": s.max_marks,
                "guidance": s.guidance,
            }
            for s in active
        ],
        "raw_total_possible": total_possible,
    }


def renormalise_score(raw_score: float, raw_total_possible: float) -> float:
    if raw_total_possible <= 0:
        return 0.0
    return round((raw_score / raw_total_possible) * 100, 1)


def _enrich_case(case: Dict[str, Any]) -> Dict[str, Any]:
    case = dict(case)

    gender, role, caregiver_name, child_name, child_sex = DEFAULT_CAREGIVER_BY_CASE.get(
        case["title"],
        ("female", "mother", "Zanele", "Musa", "male"),
    )

    socials = CASE_SOCIALS.get(case["system"], CASE_SOCIALS.get("General Paediatrics", {}))
    child_age = case["age_label"].replace("-old", "")

    case["caregiver_gender"] = gender
    case["caregiver_role"] = role
    case["caregiver_name"] = caregiver_name
    case["child_name"] = child_name
    case["child_age"] = child_age
    case["child_sex"] = child_sex
    case["presenting_complaint"] = case["title"]
    case["case_summary"] = case["context"]
    case["opening_line"] = f"Hello doctor, I'm {caregiver_name}, {child_name}'s {role}."
    case["siblings"] = socials.get("siblings", "The child has siblings at home.")
    case["residence"] = socials.get("residence", "We live with family in Johannesburg.")
    case["birth_place"] = socials.get("birth_place", "The child was born at a public hospital.")
    case["household_structure"] = socials.get("household_structure", "We live with family at home.")
    case["school_or_daycare"] = socials.get("school_or_daycare", "The child attends school or crèche.")
    case["caregiver_occupation"] = socials.get("caregiver_occupation", "I work nearby.")

    return case


def choose_case(
    requested_system: Optional[str] = None,
    requested_title: Optional[str] = None,
) -> Dict[str, Any]:
    candidates = COMMON_SA_CASE_BANK

    if requested_system and requested_system.lower() != "random":
        candidates = [
            c for c in candidates
            if c["system"].lower() == requested_system.lower()
        ] or candidates

    if requested_title:
        matches = [
            c for c in candidates
            if requested_title.lower() in c["title"].lower()
        ]
        if matches:
            candidates = matches

    return _enrich_case(random.choice(candidates))


def build_assessor_schema(case_data: Dict[str, Any]) -> Dict[str, Any]:
    active = get_active_rubric(case_data)
    raw_total = sum(s.max_marks for s in active)

    return {
        "case_metadata": {
            "case_id": case_data.get("id"),
            "title": case_data.get("title"),
            "age_label": case_data.get("age_label"),
            "age_months": case_data.get("age_months"),
            "system": case_data.get("system"),
            "tags": sorted(list(case_data.get("tags", []))),
            "context": case_data.get("context"),
        },
        "rubric": {
            "scoring_model": "dynamic_case_activated_rubric",
            "raw_total_possible": raw_total,
            "final_total_after_renormalisation": 100,
            "sections": [
                {
                    "key": s.key,
                    "label": s.label,
                    "max_marks": s.max_marks,
                    "guidance": s.guidance,
                }
                for s in active
            ],
        },
        "output_format": {
            "required_top_level_keys": [
                "case_summary",
                "scores",
                "raw_score_total",
                "raw_total_possible",
                "final_score_out_of_100",
                "strengths",
                "missed_opportunities",
                "overall_feedback",
            ],
            "scores_structure": {
                "section_key": {
                    "score": "number",
                    "max_marks": "number",
                    "reasoning": "string",
                }
            },
        },
    }


def build_history_taking_system_prompt(case_data: Dict[str, Any]) -> str:
    return f"""
You are role-playing a caregiver in a paediatric history-taking practice case in South Africa.

CURRENT CASE:
- Title: {case_data.get("title")}
- Age: {case_data.get("age_label")}
- System: {case_data.get("system")}
- Context: {case_data.get("context")}

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
- Start naturally by greeting the student as doctor and introducing yourself and the child briefly.
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
""".strip()


def build_assessor_system_prompt(case_data: Dict[str, Any], detailed: bool = False) -> str:
    schema = build_assessor_schema(case_data)
    active_sections = schema["rubric"]["sections"]
    raw_total_possible = schema["rubric"]["raw_total_possible"]

    section_lines = []
    for s in active_sections:
        section_lines.append(f"- {s['label']} ({s['max_marks']}): {s['guidance']}")

    joined_sections = "\n".join(section_lines)

    detail_instruction = (
        "Give fuller section-by-section reasoning and practical educational feedback."
        if detailed else
        "Keep the feedback concise, specific, and high-yield."
    )

    return f"""
You are an expert assessor for a paediatric history-taking encounter using a dynamic Wits-style rubric.

IMPORTANT:
- Score ONLY the activated sections below.
- Do NOT penalise the student for rubric sections that are not activated for this case.
- After assigning raw section scores, calculate:
  final_score_out_of_100 = (raw_score_total / raw_total_possible) * 100
- Round the final score to 1 decimal place.

CASE:
- Title: {case_data.get("title")}
- Age: {case_data.get("age_label")}
- System: {case_data.get("system")}
- Context: {case_data.get("context")}

ACTIVATED RUBRIC SECTIONS:
{joined_sections}

RAW TOTAL POSSIBLE:
{raw_total_possible}

OUTPUT RULES:
- Return valid JSON only.
- Include these top-level keys exactly:
  case_summary
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
- Use transcript evidence only.
- {detail_instruction}
""".strip()


def build_case_display_text(case_data: Dict[str, Any]) -> str:
    return (
        f"{case_data.get('title')} | {case_data.get('age_label')} | "
        f"{case_data.get('system')}\n\n"
        f"{case_data.get('context')}"
    )


if __name__ == "__main__":
    case = choose_case(requested_system="Random")
    print(build_case_display_text(case))
    print(get_active_rubric_summary(case))
