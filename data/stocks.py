"""Stock universe: all stocks discussed in the April 2026 research session."""

from data.models import DebtLevel, GeopoliticalRisk, Sector, Stock

# --- VCI Value Stocks ---

VZ = Stock(
    ticker="VZ",
    name="Verizon",
    sector=Sector.TELECOMS,
    ttm_pe=8.6,
    forward_pe=None,
    debt_level=DebtLevel.MODERATE,
    market_cap_millions=200_000,
    price=49.39,
    week52_low=38.39,
    week52_high=51.68,
    geopolitical_risk=GeopoliticalRisk.LOW,
    ai_thesis=(
        "AI Connect partnerships with NVIDIA, Google Cloud, Meta, Vultr. "
        "1,600-strand metro fiber routes. Frontier acquisition brings fiber to 31 states. "
        "AI network traffic 35%+ CAGR. Market prices it as traditional telco."
    ),
    notes="Strongest case in VCI. AI infrastructure re-rating not yet priced in.",
)

C = Stock(
    ticker="C",
    name="Citigroup",
    sector=Sector.FINANCIALS,
    ttm_pe=9.0,
    forward_pe=16.0,
    debt_level=DebtLevel.MODERATE,
    market_cap_millions=201_500,
    price=115.39,
    week52_low=55.51,
    week52_high=125.16,
    geopolitical_risk=GeopoliticalRisk.LOW,
    ai_thesis=(
        "AI in 50+ largest internal processes. 150K employees using AI tools. "
        "Google Cloud partnership. Consent orders may advantage Citi in AI regulation."
    ),
    notes="Too expensive per share for $1,500 moonshot portfolio.",
)

CMCSA = Stock(
    ticker="CMCSA",
    name="Comcast",
    sector=Sector.TELECOMS,
    ttm_pe=8.0,
    forward_pe=None,
    debt_level=DebtLevel.HIGH,
    market_cap_millions=105_000,
    price=27.99,
    week52_low=24.35,
    week52_high=34.66,
    geopolitical_risk=GeopoliticalRisk.LOW,
    ai_thesis=(
        "Post-Versant spinoff: pure connectivity + content. 9M+ wireless lines. "
        "DOCSIS 4.0/fiber hybrid is physical AI infrastructure. FCF $19.2B."
    ),
    notes="Most debatable VCI. Broadband losses structural, but FCF floor is real.",
)

PBR = Stock(
    ticker="PBR",
    name="Petrobras",
    sector=Sector.ENERGY,
    ttm_pe=7.6,
    forward_pe=None,
    debt_level=DebtLevel.MODERATE,
    market_cap_millions=70_000,
    price=20.08,
    week52_low=11.03,
    week52_high=21.40,
    geopolitical_risk=GeopoliticalRisk.HIGH,
    ai_thesis="Energy security play. Oil at $120 = tailwind.",
    notes="Highest risk in VCI. Political risk real. Dividend policy can change by decree.",
)

IPGP = Stock(
    ticker="IPGP",
    name="IPG Photonics",
    sector=Sector.PHOTONICS,
    ttm_pe=18.5,
    forward_pe=None,
    debt_level=DebtLevel.NONE,
    market_cap_millions=4_520,
    price=107.11,
    week52_low=48.59,
    week52_high=155.82,
    geopolitical_risk=GeopoliticalRisk.LOW,
    ai_thesis=(
        "World's dominant fiber laser company. $839M cash, zero debt. "
        "Applications in precision manufacturing, medical, EV battery, semiconductor fab."
    ),
    notes="PE premium justified by cleanest balance sheet in industrial tech.",
)

# --- AgriTech ---

AGCO = Stock(
    ticker="AGCO",
    name="AGCO Corporation",
    sector=Sector.AGRITECH,
    ttm_pe=14.0,
    forward_pe=None,
    debt_level=DebtLevel.LOW,
    market_cap_millions=9_000,
    price=124.99,
    week52_low=None,
    week52_high=None,
    geopolitical_risk=GeopoliticalRisk.MODERATE,
    ai_thesis=(
        "Fendt brand + PTx Trimble precision ag JV (85% stake). "
        "Software/data recurring revenue model. Ag equipment at cycle trough."
    ),
    notes="38% below 10-year historical avg PE. Software-enriched margins should surprise.",
)

CNH = Stock(
    ticker="CNH",
    name="CNH Industrial",
    sector=Sector.AGRITECH,
    ttm_pe=None,  # trough
    forward_pe=None,
    debt_level=DebtLevel.MODERATE,
    market_cap_millions=13_000,
    price=10.63,
    week52_low=9.00,
    week52_high=14.27,
    geopolitical_risk=GeopoliticalRisk.MODERATE,
    ai_thesis=(
        "Raven Industries autonomous farming IP. Case IH / New Holland brands. "
        "Deeper trough than AGCO, more tariff exposure."
    ),
    notes="Higher risk, potentially higher reward than AGCO.",
)

TRMB = Stock(
    ticker="TRMB",
    name="Trimble",
    sector=Sector.SPATIAL,
    ttm_pe=None,
    forward_pe=37.0,
    debt_level=DebtLevel.LOW,
    market_cap_millions=15_300,
    price=65.24,
    week52_low=None,
    week52_high=None,
    geopolitical_risk=GeopoliticalRisk.LOW,
    ai_thesis=(
        "Record ARR $2.39B (+6% YoY, +14% organic). Agentic AI platform piloted. "
        "SaaS mix shift: PE contracts as hardware revenue drops and ARR grows."
    ),
    notes="Pay now for the SaaS mix shift.",
)

# --- Photonics / Semis ---

PLAB = Stock(
    ticker="PLAB",
    name="Photronics",
    sector=Sector.SEMICONDUCTORS,
    ttm_pe=10.1,
    forward_pe=None,
    debt_level=DebtLevel.NONE,
    market_cap_millions=2_500,
    price=40.70,
    week52_low=None,
    week52_high=None,
    geopolitical_risk=GeopoliticalRisk.MODERATE,
    ai_thesis=(
        "World leader in photomask technologies. Zero effective debt (D/E 0.37%). "
        "AI exposure: ASICs, custom ICs, silicon photonics, advanced packaging. "
        "You cannot make a leading-edge chip without photomasks."
    ),
    kill_triggers=[
        "China revenue exposure in semis downcycle",
    ],
    notes="Best risk/reward in VCI. Zero debt photomask monopoly. The sleeper name.",
)

# --- Moonshot Candidates ---

ARQQ = Stock(
    ticker="ARQQ",
    name="Arqit Quantum",
    sector=Sector.CYBERSECURITY,
    ttm_pe=None,  # loss-making
    forward_pe=None,
    debt_level=DebtLevel.LOW,
    market_cap_millions=218.5,
    price=13.97,
    week52_low=11.00,
    week52_high=62.00,
    geopolitical_risk=GeopoliticalRisk.LOW,
    ai_thesis=(
        "Post-quantum cryptography is mandated (NIST 2024), not optional. "
        "UK NCSC PQC Pilot selected. Multi-year Tier-1 telecom contract. "
        "Intel NetSec Cards pre-installed. FY2026 revenue growth 214%."
    ),
    kill_triggers=[
        "PQC commoditised by AWS/Azure at zero marginal cost",
        "Management fraud",
        "Regulatory rejection",
    ],
    notes="Highest conviction moonshot. Geopolitical tailwind from cyber threats.",
)

POET = Stock(
    ticker="POET",
    name="POET Technologies",
    sector=Sector.PHOTONICS,
    ttm_pe=None,  # pre-revenue
    forward_pe=None,
    debt_level=DebtLevel.LOW,
    market_cap_millions=935,
    price=6.11,
    week52_low=None,
    week52_high=None,
    geopolitical_risk=GeopoliticalRisk.HIGH,
    ai_thesis=(
        "Optical Interposer integrates electronic and photonic devices on single chip. "
        "Direct path to AI data center co-packaged optics standard. "
        "Partnerships: LITEON, Semtech, Lessengers. $5M production order for 800G engines."
    ),
    kill_triggers=[
        "Commercialisation delays beyond H2 2026",
        "Revenue still negligible at May 20 print",
        "CPO competition from Ayar Labs or Lightmatter takes the market",
    ],
    notes="Shenzhen facility is core to manufacturing. US-China decoupling risk.",
)

NNOX = Stock(
    ticker="NNOX",
    name="Nano-X Imaging",
    sector=Sector.MEDICAL_DEVICES,
    ttm_pe=None,  # loss-making
    forward_pe=None,
    debt_level=DebtLevel.LOW,
    market_cap_millions=154.3,
    price=2.42,
    week52_low=2.11,
    week52_high=89.39,
    geopolitical_risk=GeopoliticalRisk.SEVERE,
    ai_thesis=(
        "Disrupting $5B+ X-ray market with digital cold-cathode technology. "
        "FDA 510(k) cleared. Distribution in US, Argentina, Serbia, France, UK. "
        "Cash: $52M; burn rate ~$42M/year."
    ),
    kill_triggers=[
        "FDA revocation of Nanox.ARC clearance",
        "Cash runway < 6 months without clear fundraising",
        "Reverse stock split",
        "Iran escalation directly hitting Israeli territory",
    ],
    notes="Strongest math for 100x but SEVERE geopolitical risk (Israel + Iran war).",
)

AMSC = Stock(
    ticker="AMSC",
    name="American Superconductor",
    sector=Sector.INDUSTRIALS,
    ttm_pe=11.6,
    forward_pe=None,
    debt_level=DebtLevel.LOW,
    market_cap_millions=1_550,
    price=32.65,
    week52_low=None,
    week52_high=None,
    geopolitical_risk=GeopoliticalRisk.LOW,
    ai_thesis=(
        "HTS wire manufacturer. Critical bottleneck for fusion reactors AND grid modernisation. "
        "Revenue +80% YoY Q1 FY2025. Microsoft wants superconductor data center wiring. "
        "Grid segment 85% of revenue, growing 21% YoY."
    ),
    notes="Reclassified: 10-20x quality compounder with fusion optionality as free call option.",
)

# --- Dropped from 100x list ---

OKLO = Stock(
    ticker="OKLO",
    name="Oklo",
    sector=Sector.NUCLEAR,
    ttm_pe=None,
    forward_pe=None,
    debt_level=DebtLevel.LOW,
    market_cap_millions=8_350,
    price=48.08,
    week52_low=None,
    week52_high=None,
    geopolitical_risk=GeopoliticalRisk.MODERATE,
    ai_thesis="Micro-reactor nuclear. Too large for 100x at $8.35B MC.",
    notes="Dropped: 100x = $835B, impossible.",
)

# --- Energy screen (not in portfolios) ---

VLO = Stock(
    ticker="VLO",
    name="Valero Energy",
    sector=Sector.ENERGY,
    ttm_pe=8.5,
    forward_pe=None,
    debt_level=DebtLevel.MODERATE,
    market_cap_millions=40_000,
    price=None,
    week52_low=None,
    week52_high=None,
    geopolitical_risk=GeopoliticalRisk.LOW,
    ai_thesis="Refiner, crack spread exposed.",
    notes="Screened but not selected for portfolios.",
)

PSX = Stock(
    ticker="PSX",
    name="Phillips 66",
    sector=Sector.ENERGY,
    ttm_pe=9.0,
    forward_pe=None,
    debt_level=DebtLevel.MODERATE,
    market_cap_millions=45_000,
    price=None,
    week52_low=None,
    week52_high=None,
    geopolitical_risk=GeopoliticalRisk.LOW,
    ai_thesis="Midstream/refining blend.",
    notes="Screened but not selected for portfolios.",
)


# All stocks in the universe
UNIVERSE = {s.ticker: s for s in [
    VZ, C, CMCSA, PBR, IPGP, AGCO, CNH, TRMB, PLAB,
    ARQQ, POET, NNOX, AMSC, OKLO, VLO, PSX,
]}
