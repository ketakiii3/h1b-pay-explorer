"""Write a SYNTHETIC LCA file in DOL's record layout, for testing the pipeline before the real
files are downloaded. It reproduces the real data's traps on purpose (name variants, hourly vs
yearly wages, messy titles, NYC spellings, withdrawn cases, amendments).

    uv run scripts/make_synthetic_lca.py

build.py ignores SYNTHETIC files as soon as any real file is in raw/lca/, and marks a
synthetic build in mappings.json so the app shows a "synthetic data" banner.
"""

import csv
import random
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT = ROOT / "raw" / "lca"
random.seed(7)

EMPLOYERS = [  # (name variants, naics, h1b dependent, weight)
    (["GOOGLE LLC", "Google LLC", "GOOGLE LLC.", "Google Inc."], "541511", "No", 30),
    (["Amazon.com Services LLC", "AMAZON WEB SERVICES, INC.", "Amazon Development Center U.S., Inc.", "AMAZON.COM SERVICES LLC"], "454110", "No", 45),
    (["Meta Platforms, Inc.", "META PLATFORMS INC", "Facebook, Inc."], "519130", "No", 18),
    (["Microsoft Corporation", "MICROSOFT CORP"], "511210", "No", 25),
    (["JPMorgan Chase & Co.", "JPMORGAN CHASE BANK, N.A.", "J.P. Morgan Securities LLC"], "522110", "No", 15),
    (["Goldman Sachs & Co. LLC"], "523110", "No", 6),
    (["Bloomberg L.P."], "511210", "No", 5),
    (["Cognizant Technology Solutions US Corp"], "541512", "Yes", 35),
    (["Infosys Limited", "INFOSYS LTD"], "541511", "Yes", 30),
    (["Tata Consultancy Services Limited"], "541512", "Yes", 28),
    (["The Trustees of Columbia University in the City of New York"], "611310", "No", 5),
    (["New York University"], "611310", "No", 4),
    (["Two Sigma Investments, LP"], "523920", "No", 3),
    (["Spotify USA Inc."], "519130", "No", 3),
    (["Datadog, Inc."], "511210", "No", 4),
    (["Acme Analytics LLC"], "541511", "Yes", 3),
]

ROLES = [  # (titles, soc, soc title, base salary)
    (["Software Engineer", "Software Engineer II", "Sr. Software Engineer", "SWE III", "Software Development Engineer", "Software Developer", "Member of Technical Staff"], "15-1252.00", "Software Developers", 150000),
    (["Machine Learning Engineer", "ML Engineer", "Machine Learning Eng II", "Senior MLE", "Applied ML Engineer"], "15-1252.00", "Software Developers", 175000),
    (["Data Scientist", "Sr. Data Scientist", "Data Scientist II", "Decision Scientist"], "15-2051.00", "Data Scientists", 145000),
    (["Data Engineer", "Big Data Engineer", "Senior Data Engineer"], "15-1252.00", "Software Developers", 140000),
    (["Quantitative Researcher", "Quant Developer"], "15-2041.00", "Statisticians", 220000),
    (["Business Analyst", "Programmer Analyst"], "15-1211.00", "Computer Systems Analysts", 95000),
    (["Postdoctoral Research Scientist", "Postdoc"], "19-1042.00", "Medical Scientists", 65000),
    (["Engineer II", "Technical Lead", "Consultant"], "15-1252.00", "Software Developers", 120000),
]

SITES = [  # (city spelling, county, state)
    ("New York", "New York", "NY"), ("NEW YORK CITY", "NEW YORK", "NY"), ("Brooklyn", "Kings", "NY"),
    ("NYC", "", "NY"), ("Manhattan", "New York County", "NY"), ("Jersey City", "Hudson", "NJ"),
    ("Mountain View", "Santa Clara", "CA"), ("Sunnyvale", "Santa Clara", "CA"), ("San Francisco", "San Francisco", "CA"),
    ("Seattle", "King", "WA"), ("Bellevue", "King", "WA"), ("Austin", "Travis", "TX"), ("Chicago", "Cook", "IL"),
    ("Boston", "Suffolk", "MA"), ("Cambridge", "Middlesex", "MA"), ("Edison", "Middlesex", "NJ"),
]

FIELDS = ["CASE_NUMBER", "CASE_STATUS", "RECEIVED_DATE", "DECISION_DATE", "VISA_CLASS", "JOB_TITLE", "SOC_CODE",
          "SOC_TITLE", "FULL_TIME_POSITION", "BEGIN_DATE", "TOTAL_WORKER_POSITIONS", "NEW_EMPLOYMENT",
          "CONTINUED_EMPLOYMENT", "CHANGE_PREVIOUS_EMPLOYMENT", "NEW_CONCURRENT_EMPLOYMENT", "CHANGE_EMPLOYER",
          "AMENDED_PETITION", "EMPLOYER_NAME", "EMPLOYER_CITY", "EMPLOYER_STATE", "NAICS_CODE", "WORKSITE_CITY",
          "WORKSITE_COUNTY", "WORKSITE_STATE", "WORKSITE_POSTAL_CODE", "WAGE_RATE_OF_PAY_FROM",
          "WAGE_RATE_OF_PAY_TO", "WAGE_UNIT_OF_PAY", "PREVAILING_WAGE", "PW_UNIT_OF_PAY", "PW_WAGE_LEVEL",
          "H_1B_DEPENDENT", "WILLFUL_VIOLATOR", "TOTAL_WORKSITE_LOCATIONS"]

QUARTER_MONTHS = {1: (10, 12), 2: (1, 3), 3: (4, 6), 4: (7, 9)}


def row(fy, q, i):
    names, naics, dep, _ = random.choices(EMPLOYERS, weights=[e[3] for e in EMPLOYERS])[0]
    titles, soc, soc_title, base = random.choice(ROLES)
    city, county, state = random.choice(SITES)
    level = random.choices(["I", "II", "III", "IV", ""], weights=[30, 35, 20, 10, 5])[0]
    mult = {"I": 0.75, "II": 0.95, "III": 1.15, "IV": 1.4, "": 1.0}[level] * random.uniform(0.85, 1.2)
    if dep == "Yes":
        mult *= 0.75
    annual = round(base * mult, -2)
    unit = random.choices(["Year", "Hour", "Month", "Bi-Weekly"], weights=[85, 10, 3, 2])[0]
    wage = {"Year": annual, "Hour": round(annual / 2080, 2), "Month": round(annual / 12, 2), "Bi-Weekly": round(annual / 26, 2)}[unit]
    if random.random() < 0.003:  # the classic mistake: an hourly rate typed with unit Year
        unit, wage = "Year", round(annual / 2080, 2)
    y = fy - 1 if q == 1 else fy
    m = random.randint(*QUARTER_MONTHS[q])
    kind = random.choices(["new", "cont", "change"], weights=[45, 40, 15])[0]
    workers = random.choices([1, 2, 5, 10], weights=[90, 5, 3, 2])[0]
    return {
        "CASE_NUMBER": f"I-200-{fy % 100}{q}{i:05d}-{random.randint(100000, 999999)}",
        "CASE_STATUS": random.choices(["Certified", "Certified - Withdrawn", "Withdrawn", "Denied"], weights=[88, 7, 4, 1])[0],
        "RECEIVED_DATE": f"{m:02d}/{random.randint(1, 20):02d}/{y}", "DECISION_DATE": f"{m:02d}/{random.randint(21, 28):02d}/{y}",
        "VISA_CLASS": random.choices(["H-1B", "E-3 Australian", "H-1B1 Singapore"], weights=[96, 3, 1])[0],
        "JOB_TITLE": random.choice(titles).upper() if random.random() < 0.4 else random.choice(titles),
        "SOC_CODE": soc, "SOC_TITLE": soc_title, "FULL_TIME_POSITION": "Y", "BEGIN_DATE": f"{m:02d}/28/{y}",
        "TOTAL_WORKER_POSITIONS": workers,
        "NEW_EMPLOYMENT": workers if kind == "new" else 0, "CONTINUED_EMPLOYMENT": workers if kind == "cont" else 0,
        "CHANGE_PREVIOUS_EMPLOYMENT": 0, "NEW_CONCURRENT_EMPLOYMENT": 0,
        "CHANGE_EMPLOYER": workers if kind == "change" else 0, "AMENDED_PETITION": 0,
        "EMPLOYER_NAME": random.choice(names), "EMPLOYER_CITY": "", "EMPLOYER_STATE": state, "NAICS_CODE": naics,
        "WORKSITE_CITY": city, "WORKSITE_COUNTY": county, "WORKSITE_STATE": state, "WORKSITE_POSTAL_CODE": "",
        "WAGE_RATE_OF_PAY_FROM": f"${wage:,.2f}" if random.random() < 0.3 else wage,
        "WAGE_RATE_OF_PAY_TO": "" if random.random() < 0.6 else round(wage * 1.2, 2), "WAGE_UNIT_OF_PAY": unit,
        "PREVAILING_WAGE": round(base * 0.7, 2), "PW_UNIT_OF_PAY": "Year", "PW_WAGE_LEVEL": level,
        "H_1B_DEPENDENT": dep, "WILLFUL_VIOLATOR": "No", "TOTAL_WORKSITE_LOCATIONS": 1,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for fy, quarters in [(2024, [1, 2, 3, 4]), (2025, [1, 2, 3, 4]), (2026, [1, 2, 3])]:
        for q in quarters:
            path = OUT / f"SYNTHETIC_LCA_Disclosure_Data_FY{fy}_Q{q}.csv"
            rows = [row(fy, q, i) for i in range(3000)]
            rows += [dict(r, DECISION_DATE=r["DECISION_DATE"].replace("/28/", "/29/")) for r in rows[:30]]  # amendments
            with path.open("w", newline="") as f:
                w = csv.DictWriter(f, FIELDS)
                w.writeheader()
                w.writerows(rows)
            print("wrote", path.name, len(rows))


if __name__ == "__main__":
    main()
