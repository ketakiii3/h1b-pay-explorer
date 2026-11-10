"""Deterministic checks of the lookup tools, guardrails and wage logic. No model calls."""

import pytest

import app
import h1b_common as hc


@pytest.fixture(scope="module", autouse=True)
def store():
    app.load_store()


@pytest.mark.parametrize("q", [
    "SELECT avg(wage_from_raw) FROM lca",
    "SELECT median(l.wage_to_raw) FROM lca l",
    "SELECT count(*) FROM lca WHERE employer_name_raw LIKE '%GOOGLE%'",
    "SELECT count(*) FROM lca WHERE employer ILIKE '%google%'",
    "SELECT count(*) FROM lca WHERE job_title ILIKE '%machine learning%'",
    "SELECT count(*) FROM lca WHERE worksite_city_raw = 'NYC'",
    "SELECT median(wage_annual_from) FROM lca",
    "DROP TABLE lca",
    "SELECT 1; DELETE FROM lca",
])
def test_guardrail_rejects(q):
    assert app.check_sql(q)


@pytest.mark.parametrize("q", [
    "SELECT median(wage_annual_from) FROM lca WHERE employer_id = 1 AND wage_flag = 'ok'",
    "WITH x AS (SELECT * FROM lca WHERE role_family = 'Quant') SELECT count(*) FROM x",
    "SELECT employer, count(*) FROM lca WHERE area_code = '35620' GROUP BY 1;",
    "SELECT fiscal_year, approved, denied FROM petitions WHERE employer_id = 7 ORDER BY 1",
])
def test_guardrail_allows(q):
    assert app.check_sql(q) is None


def test_wage_level_boundaries():
    t = [100.0, 200.0, 300.0, 400.0]
    assert hc.wage_level(99, t) == 0
    assert hc.wage_level(100, t) == 1
    assert hc.wage_level(299.99, t) == 2
    assert hc.wage_level(300, t) == 3
    assert hc.wage_level(10_000, t) == 4


def test_annualize():
    assert hc.annualize(50, "Hour") == 104_000
    assert hc.annualize(5000, "Month") == 60_000
    assert hc.annualize(4000, "Bi-Weekly") == 104_000
    assert hc.annualize(1, "Fortnight") is None


@pytest.mark.parametrize("name,expected", [("google", "Google"), ("GOOGLE LLC.", "Google"), ("facebook", "Meta"),
                                           ("tcs", "Tata Consultancy Services"), ("JP Morgan", "JPMorgan Chase")])
def test_find_employer(name, expected):
    assert app.match_employers(name)[0]["employer"] == expected


@pytest.mark.parametrize("text,family", [("ML engineer", "Machine Learning Engineer"), ("mle", "Machine Learning Engineer"),
                                         ("Sr. Data Scientist", "Data Scientist"), ("quant", "Quant"),
                                         ("Postdoctoral Research Scientist", "Postdoc / Research Associate")])
def test_find_role(text, family):
    assert app.match_role(text)["role_family"] == family


@pytest.mark.parametrize("place", ["NYC", "new york", "Brooklyn", "Manhattan"])
def test_nyc_spellings_share_one_area(place):
    assert app.match_place(place)["area_code"] == "35620"


def test_classify_uses_soc_for_vague_titles():
    assert hc.classify(hc.normalize_title("Engineer II"), "15-1252.00")[0] == "Software Engineer"


def test_offer_calculator():
    r = app.compute_wage_level(150_000, "data scientist", "NYC")
    assert r["soc_code"] == "15-2051" and 1 <= r["wage_level"] <= 4
    assert r["lottery_entries"] == r["wage_level"]


def test_petitions_one_row_per_employer_year():
    dupes = app.store.q("""SELECT count(*) FROM (SELECT fiscal_year, employer_id FROM petitions
                           WHERE employer_id IS NOT NULL GROUP BY 1, 2 HAVING count(*) > 1)""")[0][0]
    assert dupes == 0


def test_petitions_share_employer_ids_with_lca():
    eid = app.match_employers("Meta")[0]["employer_id"]
    rows = app.store.q("SELECT fiscal_year, approved, new_employment_approved FROM petitions WHERE employer_id = ? ORDER BY 1", [eid])
    assert [r[0] for r in rows] == [2024, 2025, 2026]
    assert all(approved >= new > 0 for _, approved, new in rows)


def test_petition_totals_add_up():
    bad = app.store.q("""SELECT count(*) FROM petitions WHERE approved <> new_employment_approved + continuation_approved
                         + change_same_employer_approved + new_concurrent_approved + change_employer_approved + amended_approved""")[0][0]
    assert bad == 0


@pytest.mark.parametrize("uscis,dol", [
    ("LOWES COMPANIES INC", "Lowe's Companies, Inc."),
    ("NORDSTROM INC D B A NORDSTROM", "Nordstrom, Inc."),
    ("MAPLEBEAR INC D B A INSTACART", "Maplebear Inc. d/b/a Instacart"),
])
def test_loose_key_bridges_uscis_and_dol_spellings(uscis, dol):
    import build

    assert build.loose_key(uscis) == build.loose_key(dol)


def test_db_is_read_only():
    with pytest.raises(Exception):
        app.store.q("CREATE TABLE x AS SELECT 1")


def test_no_join_fanout_and_wages_clean():
    n, ok_bad = app.store.q("""SELECT count(*), count(*) FILTER (wage_flag = 'ok' AND wage_annual_from <= 0) FROM lca""")[0]
    assert n == app.store.q("SELECT count(DISTINCT case_number) FROM lca")[0][0]
    assert ok_bad == 0


@pytest.mark.parametrize("title,soc,family", [
    ("Forward Deployed AI Engineer", "15-1252", "Forward Deployed"),
    ("Forward Deployed Product Manager", "15-1299", "Forward Deployed"),
    ("Gen AI Engineer", "15-1252", "AI Engineer (GenAI / LLM)"),
    ("Full Stack LLM Development Manager", "15-1252", "AI Engineer (GenAI / LLM)"),
    ("AI/ML Engineer", "15-1252", "Machine Learning Engineer"),
    ("Software Engineer, Computer Vision", "15-1252", "Machine Learning Engineer"),
    ("Order Fulfillment Specialist III", "43-5081", "Analyst (other)"),
    ("Package Consultant 2", "15-1299", "IT Specialist (other)"),
    ("Technical Architect", "15-1299", "IT Architect"),
    ("Technical Project Lead", "15-1299", "Project / Program Manager"),
])
def test_ai_era_titles(title, soc, family):
    assert hc.classify(hc.normalize_title(title), soc)[0] == family
