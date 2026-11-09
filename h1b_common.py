"""Normalizers shared by build.py (offline) and app.py (online).

Anything that turns messy LCA text into a clean key lives here, so the build and the
agent's lookup tools always agree: an employer, title or city normalized at build time
is normalized the same way when a user types it.
"""

import re

# --- Wages ---

# DOL's own annualization factors (full-time = 2080 hours/year).
ANNUAL_FACTOR = {"HOUR": 2080, "WEEK": 52, "BI-WEEKLY": 26, "MONTH": 12, "YEAR": 1}

# Under the wage-weighted selection rule (effective for the FY2027 cap season), each
# registration is entered once per wage level: Level I = 1 entry ... Level IV = 4 entries.
LOTTERY_ENTRIES = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4}


def annualize(value, unit):
    if value is None or unit is None:
        return None
    factor = ANNUAL_FACTOR.get(str(unit).strip().upper())
    return None if factor is None else float(value) * factor


def wage_level(salary: float, thresholds: list[float]) -> int:
    """The highest level (1-4) whose threshold the salary meets; 0 if below Level I."""
    level = 0
    for i, t in enumerate(thresholds, start=1):
        if t is not None and salary >= t:
            level = i
    return level


# --- Employers ---

_SUFFIXES = (
    r"\b(INCORPORATED|INC|LLC|L L C|LLP|L L P|LP|L P|CORPORATION|CORP|COMPANY|CO|LIMITED|LTD|"
    r"PLC|PC|P C|PLLC|NA|N A|GMBH|AG|SA|PVT|PRIVATE|THE)\b"
)


def normalize_employer(name: str | None) -> str:
    if not name:
        return ""
    s = name.upper().replace("&", " AND ")
    s = re.sub(r"[^A-Z0-9 ]+", " ", s)
    s = re.sub(_SUFFIXES, " ", s)
    s = re.sub(r"\bDBA\b.*$", " ", s)  # "X LLC DBA Y" -> X
    return re.sub(r"\s+", " ", s).strip()


# --- Job titles -> role families ---

_ABBREV = [
    (r"\bsr\b\.?", "senior"), (r"\bjr\b\.?", "junior"), (r"\bsnr\b", "senior"),
    (r"\bengr\b|\beng\b|\bengg\b", "engineer"), (r"\bdev\b", "developer"),
    (r"\bml\b", "machine learning"), (r"\bai\b", "artificial intelligence"),
    (r"\bswe\b|\bsde\b", "software engineer"), (r"\bmts\b", "member of technical staff"),
    (r"\bmgr\b", "manager"), (r"\bassoc\b", "associate"), (r"\bmle\b", "machine learning engineer"),
    (r"\bds\b", "data scientist"), (r"\bpm\b", "product manager"), (r"\bqa\b", "quality assurance"),
    (r"\bvp\b", "vice president"), (r"\bdir\b", "director"), (r"\bmgmt\b", "management"),
    (r"\bprog\b", "programmer"), (r"\banlst\b|\banl\b", "analyst"), (r"\bsys\b", "systems"),
]

_SENIORITY = [
    ("intern", r"\bintern(ship)?\b"),
    ("manager", r"\b(manager|director|head of|vice president|lead manager)\b"),
    ("staff_plus", r"\b(staff|principal|distinguished|fellow|architect)\b"),
    ("senior", r"\b(senior|lead|iii|iv|3|4|l5|l6)\b"),
    ("junior", r"\b(junior|associate|entry|graduate|new grad|i|1|l3)\b"),
    ("mid", r"\b(ii|2|l4)\b"),
]

# Order matters: the first match wins, so specific families come before general ones.
ROLE_RULES: list[tuple[str, str]] = [
    ("Forward Deployed", r"forward deploy(ed|ment)"),
    ("AI Engineer (GenAI / LLM)", r"\bgenai\b|gen artificial intelligence|generative artificial intelligence|\bllms?\b|large language model|prompt engineer|\bagentic\b|artificial intelligence agent|"
     r"(applied |founding |senior |staff |lead |principal )?artificial intelligence (engineer|developer|software|solutions?|application|platform|architect|specialist|lead)|"
     r"(engineer|developer),? (generative )?artificial intelligence$"),
    ("Postdoc / Research Associate", r"post ?doc|postdoctoral|research (associate|fellow|assistant)|research scholar|visiting scholar"),
    ("Machine Learning Engineer", r"machine learning (engineer|developer|scientist engineer|ops|platform|infrastructure)|(engineer|developer).{0,25}(computer vision|deep learning|\\bnlp\\b|natural language)|(engineer|developer).{0,25}machine learning|artificial intelligence machine learning|machine learning (lead|architect)|\bmlops\b|deep learning engineer|artificial intelligence engineer|ai/ml engineer|applied (ml|machine learning)|computer vision engineer|\bnlp engineer"),
    ("Research Scientist", r"research scientist|applied scientist|machine learning scientist|research engineer|ai scientist|artificial intelligence scientist"),
    ("Data Scientist", r"data scien|decision scientist|product scientist|machine learning$|statistical model|quantitative scientist"),
    ("Data Engineer", r"data engineer|big data|etl developer|data platform engineer|analytics engineer|data architect"),
    ("Quant", r"\bquant|quantitative (analyst|researcher|developer|trader|strategist)|\balgo(rithmic)? trad"),
    ("Data Analyst", r"data analyst|analytics (analyst|specialist|manager)|business intelligence|\bbi (developer|analyst|engineer)|reporting analyst|insights analyst"),
    ("Product Manager", r"product manager|product owner|program manager, product|technical program manager|\btpm\b|product management"),
    ("DevOps / SRE / Cloud", r"devops|site reliability|\bsre\b|cloud (engineer|architect|developer)|platform engineer|infrastructure engineer|systems? reliability|kubernetes"),
    ("Security Engineer", r"security|cyber|penetration|infosec"),
    ("QA / Test Engineer", r"quality assurance|\btest(ing)? (engineer|analyst|lead|automation)|\bsdet\b|automation test|validation engineer"),
    ("Hardware / Semiconductor Engineer", r"hardware|asic|fpga|silicon|semiconductor|chip design|vlsi|rtl|physical design|layout engineer|design verification|process engineer|firmware"),
    ("Database / Systems Admin", r"database administrator|\bdba\b|systems? administrator|network (engineer|administrator)|sap basis"),
    ("Software Engineer", r"software|developer|programmer|full ?stack|front ?end|back ?end|web (engineer|developer)|mobile (engineer|developer)|\bios\b|android|java|\.net|python|member of technical staff|application engineer|applications? developer|computer (systems )?engineer|systems engineer|technical lead|technology lead|tech lead|salesforce|sap (consultant|developer|abap)|oracle (developer|consultant)|engineer,? (software|development)"),
    ("Business / Systems Analyst", r"business analyst|systems analyst|business systems|functional (analyst|consultant)|requirements analyst|technical analyst|it analyst|programmer analyst"),
    ("Consultant", r"consultant|consulting|advisory"),
    ("Financial Analyst", r"financial analyst|finance analyst|investment (analyst|banking)|credit (risk )?analyst|risk analyst|equity research|associate, investment|portfolio (analyst|manager)|actuar|underwrit"),
    ("Accountant / Auditor", r"accountant|accounting|auditor|audit|\btax\b|controller|cpa"),
    ("Designer", r"designer|\bux\b|\bui\b|user experience|graphic|interaction design"),
    ("Professor / Lecturer", r"professor|lecturer|instructor|faculty|teacher|teaching"),
    ("Physician / Healthcare", r"physician|hospitalist|\bresident\b|surgeon|\bmd\b|medical|nurse|therapist|pharmac|dentist|psychiatr|clinical|radiolog|anesthes|patholog|cardiolog|oncolog|pediatric"),
    ("Mechanical / Civil / Electrical Engineer", r"mechanical|civil|structural|electrical|electronics|manufacturing|industrial engineer|chemical engineer|aerospace|automotive|controls engineer|design engineer|project engineer"),
    ("Lawyer / Legal", r"attorney|lawyer|(legal|general|associate|corporate|patent|tax) counsel\b|\bcounsel$|law clerk|paralegal|\blegal\b"),
    ("Sales / Solutions Engineer", r"(customer|sales|solutions?|pre sales|presales) engineer|customer solutions|technical solutions"),
    ("Project / Program Manager", r"project (manager|lead|leader|coordinator)|program (manager|management)|scrum master|delivery (manager|lead)|technology project"),
    ("IT Architect", r"\barchitect\b"),
    ("Scientist (other)", r"scientist|chemist|biologist|physicist|research and development"),
    ("Supply Chain / Logistics", r"supply chain|logistics|procurement|purchasing|operations analyst"),
    ("Engineer (other)", r"\bengineer"),
    ("Management", r"manager|director|head of|vice president|chief|general manager|president"),
    ("Analyst (other)", r"analyst|specialist|associate"),
]

# Title families too vague to trust when the SOC code says something specific
# ("Engineer II" filed under SOC 15-1252 is a software engineer).
GENERIC_FAMILIES = {"Engineer (other)", "Management", "Analyst (other)", "Consultant"}

# SOC code -> role family, used when the title is vague or unmatched.
SOC_FAMILY = {
    "15-1252": "Software Engineer", "15-1251": "Software Engineer", "15-1253": "QA / Test Engineer",
    "15-1254": "Software Engineer", "15-1255": "Designer", "15-1256": "Software Engineer",
    "15-2051": "Data Scientist", "15-2041": "Data Scientist", "15-1221": "Research Scientist",
    "15-1211": "Business / Systems Analyst", "15-1212": "Security Engineer",
    "15-1241": "DevOps / SRE / Cloud", "15-1242": "Database / Systems Admin",
    "15-1243": "Data Engineer", "15-1244": "Database / Systems Admin",
    "15-2031": "Data Analyst", "15-2011": "Financial Analyst", "13-2051": "Financial Analyst",
    "13-2052": "Financial Analyst", "13-2099": "Financial Analyst", "13-2011": "Accountant / Auditor",
    "13-1111": "Consultant", "13-1161": "Data Analyst", "17-2061": "Hardware / Semiconductor Engineer",
    "17-2072": "Hardware / Semiconductor Engineer", "17-2071": "Mechanical / Civil / Electrical Engineer",
    "17-2141": "Mechanical / Civil / Electrical Engineer", "17-2051": "Mechanical / Civil / Electrical Engineer",
    "17-2112": "Mechanical / Civil / Electrical Engineer", "17-2011": "Mechanical / Civil / Electrical Engineer",
    "17-2041": "Mechanical / Civil / Electrical Engineer", "11-3021": "Management", "11-2021": "Management",
    "11-1021": "Management", "11-9041": "Management", "11-3031": "Management",
    "15-1299": "IT Specialist (other)", "13-1082": "Project / Program Manager", "23-1011": "Lawyer / Legal",
    "41-9031": "Sales / Solutions Engineer", "13-1081": "Supply Chain / Logistics", "11-3071": "Supply Chain / Logistics",
    "19-2031": "Scientist (other)", "19-1021": "Scientist (other)", "19-2012": "Scientist (other)",
    "17-1011": "Architect (buildings)", "17-2199": "Mechanical / Civil / Electrical Engineer",
    "19-1042": "Postdoc / Research Associate", "19-1029": "Postdoc / Research Associate",
}



def normalize_title(title: str | None) -> str:
    if not title:
        return ""
    s = title.lower()
    s = re.sub(r"[\(\)\[\]\{\}\"']", " ", s)
    s = re.sub(r"[-_/|,;:]+", " ", s)
    for pattern, repl in _ABBREV:
        s = re.sub(pattern, repl, s)
    return re.sub(r"\s+", " ", s).strip()


def classify_title(title_norm: str) -> str | None:
    for family, pattern in ROLE_RULES:
        if re.search(pattern, title_norm):
            return family
    return None


def classify(title_norm: str, soc_code: str | None) -> tuple[str, str]:
    """(role_family, how) for one filing: title rules first, the SOC code when the title is vague."""
    family = classify_title(title_norm)
    soc_family = SOC_FAMILY.get((soc_code or "")[:7])
    if soc_family == "Architect (buildings)":
        return soc_family, "soc_code"
    if family and family not in GENERIC_FAMILIES:
        return family, "title_rule"
    if soc_family:
        return soc_family, "soc_code"
    if (soc_code or "").startswith("25-1"):
        return "Professor / Lecturer", "soc_code"
    if (soc_code or "").startswith("29-1"):
        return "Physician / Healthcare", "soc_code"
    if family:
        return family, "title_rule"
    return "Other", "unmatched"


def seniority(title_norm: str) -> str:
    for level, pattern in _SENIORITY:
        if re.search(pattern, title_norm):
            return level
    return "unspecified"


ROLE_FAMILIES = [family for family, _ in ROLE_RULES] + ["Other"]

# What users type -> a role family. Checked before the title rules.
ROLE_ALIASES = {
    "mle": "Machine Learning Engineer", "ml engineer": "Machine Learning Engineer", "ml": "Machine Learning Engineer",
    "mlops": "Machine Learning Engineer", "computer vision": "Machine Learning Engineer", "cv engineer": "Machine Learning Engineer",
    "nlp engineer": "Machine Learning Engineer", "ai/ml engineer": "Machine Learning Engineer",
    "ai engineer": "AI Engineer (GenAI / LLM)", "ai": "AI Engineer (GenAI / LLM)", "genai": "AI Engineer (GenAI / LLM)",
    "gen ai": "AI Engineer (GenAI / LLM)", "genai engineer": "AI Engineer (GenAI / LLM)", "llm engineer": "AI Engineer (GenAI / LLM)",
    "generative ai engineer": "AI Engineer (GenAI / LLM)", "prompt engineer": "AI Engineer (GenAI / LLM)",
    "applied ai engineer": "AI Engineer (GenAI / LLM)", "ai developer": "AI Engineer (GenAI / LLM)",
    "fde": "Forward Deployed", "forward deployed": "Forward Deployed",
    "forward deployed engineer": "Forward Deployed", "forward deployed ai engineer": "Forward Deployed",
    "applied scientist": "Research Scientist", "ai researcher": "Research Scientist", "ai scientist": "Research Scientist",
    "ml scientist": "Research Scientist", "research engineer": "Research Scientist",
    "data science": "Data Scientist", "decision scientist": "Data Scientist", "product data scientist": "Data Scientist",
    "analytics engineer": "Data Engineer", "ml platform engineer": "Machine Learning Engineer",
    "swe": "Software Engineer", "sde": "Software Engineer", "software": "Software Engineer",
    "ds": "Data Scientist",
    "de": "Data Engineer", "quant": "Quant", "pm": "Product Manager", "sre": "DevOps / SRE / Cloud",
    "devops": "DevOps / SRE / Cloud", "analyst": "Data Analyst", "researcher": "Research Scientist",
    "postdoc": "Postdoc / Research Associate", "doctor": "Physician / Healthcare",
}


def role_from_user_text(text: str) -> str | None:
    t = text.strip().lower()
    if t in ROLE_ALIASES:
        return ROLE_ALIASES[t]
    for family in ROLE_FAMILIES:
        if t == family.lower():
            return family
    return classify_title(normalize_title(text))


# --- Places ---

_COUNTY_SUFFIX = r"\b(COUNTY|PARISH|BOROUGH|CITY AND BOROUGH|CENSUS AREA|MUNICIPALITY|MUNICIPIO|CITY OF|CO)\b"


def normalize_county(county: str | None) -> str:
    if not county:
        return ""
    s = county.upper().replace("SAINT ", "ST ").replace("ST. ", "ST ")
    s = re.sub(r"[^A-Z0-9 ]+", " ", s)
    s = re.sub(_COUNTY_SUFFIX, " ", s)
    return re.sub(r"\s+", " ", s).strip()


# Worksite city spellings that mean the same place.
CITY_ALIASES = {
    "NEW YORK CITY": ["NEW YORK", "NEW YORK CITY", "NYC", "MANHATTAN", "BROOKLYN", "QUEENS",
                      "BRONX", "THE BRONX", "STATEN ISLAND", "LONG ISLAND CITY", "NEW YORK NY",
                      "NEWYORK", "NY", "N Y", "NEW YOUR"],
    "SAN FRANCISCO": ["SAN FRANCISCO", "SF", "SAN FRANSISCO", "S F"],
    "WASHINGTON DC": ["WASHINGTON", "WASHINGTON DC", "WASHINGTON D C", "DC"],
}
_CITY_LOOKUP = {alias: canon for canon, aliases in CITY_ALIASES.items() for alias in aliases}


def normalize_city(city: str | None, state: str | None = None) -> str:
    if not city:
        return ""
    s = re.sub(r"[^A-Z ]+", " ", city.upper())
    s = re.sub(r"\s+", " ", s).strip()
    if s == "WASHINGTON" and state and state.upper() != "DC":
        return s  # Washington, PA etc.
    return _CITY_LOOKUP.get(s, s)


# What users type -> metro search text. The tool fuzzy-matches the result to an OFLC area name.
PLACE_ALIASES = {
    "nyc": "New York-Newark-Jersey City", "new york": "New York-Newark-Jersey City",
    "new york city": "New York-Newark-Jersey City", "manhattan": "New York-Newark-Jersey City",
    "brooklyn": "New York-Newark-Jersey City", "jersey city": "New York-Newark-Jersey City",
    "sf": "San Francisco-Oakland", "san francisco": "San Francisco-Oakland", "bay area": "San Jose-Sunnyvale",
    "silicon valley": "San Jose-Sunnyvale", "san jose": "San Jose-Sunnyvale", "mountain view": "San Jose-Sunnyvale",
    "palo alto": "San Jose-Sunnyvale", "sunnyvale": "San Jose-Sunnyvale", "cupertino": "San Jose-Sunnyvale",
    "menlo park": "San Francisco-Oakland", "seattle": "Seattle-Tacoma", "redmond": "Seattle-Tacoma",
    "bellevue": "Seattle-Tacoma", "boston": "Boston-Cambridge", "cambridge": "Boston-Cambridge",
    "la": "Los Angeles-Long Beach", "los angeles": "Los Angeles-Long Beach", "chicago": "Chicago-Naperville",
    "austin": "Austin-Round Rock", "dallas": "Dallas-Fort Worth", "houston": "Houston-Pasadena",
    "atlanta": "Atlanta-Sandy Springs", "dc": "Washington-Arlington", "washington dc": "Washington-Arlington",
    "pittsburgh": "Pittsburgh", "philadelphia": "Philadelphia-Camden", "denver": "Denver-Aurora",
    "san diego": "San Diego-Chula Vista", "miami": "Miami-Fort Lauderdale", "phoenix": "Phoenix-Mesa",
    "raleigh": "Raleigh-Cary", "detroit": "Detroit-Warren", "minneapolis": "Minneapolis-St. Paul",
    "charlotte": "Charlotte-Concord",
}


# What users type for a company -> its canonical name in employer_overrides.csv.
EMPLOYER_ALIASES = {
    "tcs": "Tata Consultancy Services", "tata": "Tata Consultancy Services", "jpm": "JPMorgan Chase",
    "jp morgan": "JPMorgan Chase", "chase": "JPMorgan Chase", "msft": "Microsoft", "aws": "Amazon",
    "fb": "Meta", "facebook": "Meta", "instagram": "Meta", "alphabet": "Google", "gs": "Goldman Sachs",
    "goldman": "Goldman Sachs", "bofa": "Bank of America", "boa": "Bank of America", "ms": "Morgan Stanley",
    "citibank": "Citi", "hrt": "Hudson River Trading", "de shaw": "D. E. Shaw", "ey": "EY",
    "ernst & young": "EY", "pwc": "PwC", "bcg": "Boston Consulting Group", "hcl": "HCLTech",
    "lti": "LTIMindtree", "nyu": "New York University", "cmu": "Carnegie Mellon University",
    "bytedance": "TikTok / ByteDance", "tiktok": "TikTok / ByteDance", "ibm": "IBM", "nvda": "NVIDIA",
    "amex": "American Express", "capgemini": "Capgemini", "accenture": "Accenture",
}
