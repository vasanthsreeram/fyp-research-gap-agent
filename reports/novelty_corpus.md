# Novelty-vs-corpus report

| Field | Value |
|-------|-------|
| **Backend** | `lexical` |
| **Papers** | 52 |
| **Gaps** | 171 |
| **Mean corpus novelty** | 0.79 |
| **Mean gap redundancy** | 0.53 |
| **High novelty (≥0.55)** | 171 |
| **Redundant gaps (≥0.55)** | 73 |

_Own source papers excluded from nearest match. High corpus_novelty ≈ gap text distant from rest of corpus; high gap_redundancy ≈ near-duplicate of another gap._

## Top surprising gaps (by blended novelty, n=12)

### 1. Limitation: Extrahepatic delivery remains elusive at therapeutically relevant doses without 
- **Gap ID**: `gap_845e28836c0a` · kind=`delivery_barrier`
- **Scores**: blended_novelty=0.75 corpus=0.86 prior=0.70 redundancy=0.36
- **Overall**: 0.78 → 0.80
- **Domains**: targeting
- **Nearest corpus papers** (excluded own sources):
  - [0.14] CRISPR-Cas9 lipid nanoparticle systems for in vivo gene editing (2018) (`paper_d84a83f4a21e`)
  - [0.14] Small interfering RNA delivery via lipid nanoparticles for liver target engagement (2018) (`paper_442ab5be02fd`)
  - [0.13] Lipid nanoparticles for mRNA delivery (2021) (`paper_306a3c285415`)

### 2. Limitation: Results indicate cytosolic RNP competition is a post-escape bottleneck distinct 
- **Gap ID**: `gap_f4ce3dd871dc` · kind=`delivery_barrier`
- **Scores**: blended_novelty=0.75 corpus=0.83 prior=0.70 redundancy=0.25
- **Overall**: 0.72 → 0.74
- **Domains**: endosomal_escape
- **Nearest corpus papers** (excluded own sources):
  - [0.17] The endosomal escape of lipid nanoparticles: mechanisms and strategies for improvement (2021) (`paper_4f1ae7b028cc`)
  - [0.15] Aptamer-ncRNA chimeras for receptor-mediated cytosolic delivery without ionizable lipids (2024) (`paper_df50380f7f76`)
  - [0.14] Endosomal escape of lipid nanoparticles: a mechanistic investigation (2020) (`paper_310a37ea7a80`)

### 3. Limitation: However, delivery to extrahepatic tissues was minimal.
- **Gap ID**: `gap_7c8d79bad034` · kind=`delivery_barrier`
- **Scores**: blended_novelty=0.74 corpus=0.83 prior=0.70 redundancy=0.35
- **Overall**: 0.76 → 0.77
- **Domains**: targeting
- **Nearest corpus papers** (excluded own sources):
  - [0.17] CRISPR-Cas9 lipid nanoparticle systems for in vivo gene editing (2018) (`paper_d84a83f4a21e`)
  - [0.15] Extrahepatic targeting of lipid nanoparticles in vivo (2021) (`paper_13656da26617`)
  - [0.15] Bifunctional guide–scaffold RNAs couple Cas9 editing to local transcript silencing (2025) (`paper_ab572d90e69e`)

### 4. Untested: We propose ribosome dwell time modulates endosomal TLR exposure via altered unpa
- **Gap ID**: `gap_5f4bfc7439a3` · kind=`untested_claim`
- **Scores**: blended_novelty=0.74 corpus=0.85 prior=0.65 redundancy=0.27
- **Overall**: 0.71 → 0.73
- **Domains**: endosomal_escape, lnp
- **Nearest corpus papers** (excluded own sources):
  - [0.15] The endosomal escape of lipid nanoparticles: mechanisms and strategies for improvement (2021) (`paper_4f1ae7b028cc`)
  - [0.14] Quantitative single-cell map of LNP uptake, endosomal progression, and mRNA translation (2023) (`paper_204538b2d717`)
  - [0.11] Aptamer-ncRNA chimeras for receptor-mediated cytosolic delivery without ionizable lipids (2024) (`paper_df50380f7f76`)

### 5. Mechanism gap: We hypothesized that origami geometry would protect cargo and promote endosomal 
- **Gap ID**: `gap_9d066306eedc` · kind=`mechanism_unknown`
- **Scores**: blended_novelty=0.73 corpus=0.76 prior=0.80 redundancy=0.40
- **Overall**: 0.70 → 0.68
- **Domains**: endosomal_escape
- **Nearest corpus papers** (excluded own sources):
  - [0.24] Hybrid nucleic acid nanostructures for programmable intracellular delivery (2023) (`paper_7f05a0e18a0a`)
  - [0.23] The endosomal escape of lipid nanoparticles: mechanisms and strategies for improvement (2021) (`paper_4f1ae7b028cc`)
  - [0.23] Bifunctional guide–scaffold RNAs couple Cas9 editing to local transcript silencing (2025) (`paper_ab572d90e69e`)

### 6. Limitation: Polymeric particles showed 5-fold higher epithelial association but only 1.2-fol
- **Gap ID**: `gap_c37e8f693a62` · kind=`delivery_barrier`
- **Scores**: blended_novelty=0.73 corpus=0.87 prior=0.60 redundancy=0.30
- **Overall**: 0.68 → 0.71
- **Domains**: —
- **Nearest corpus papers** (excluded own sources):
  - [0.13] tRNA-like structural motifs stabilize linear mRNA without nucleoside modification (2023) (`paper_4d4e9a3c49de`)
  - [0.13] Aptamer-ncRNA chimeras for receptor-mediated cytosolic delivery without ionizable lipids (2024) (`paper_df50380f7f76`)
  - [0.12] Rapidly adaptable nanoparticle platforms for mRNA delivery to the lung (2021) (`paper_4c30401a4c9f`)

### 7. Gap: Prior work demonstrated multi-day expression, yet mecha vs Prior work demonstrated multi-day expression, yet mecha
- **Gap ID**: `gap_ddd38aff5be3` · kind=`theory_vs_experiment`
- **Scores**: blended_novelty=0.72 corpus=0.88 prior=0.55 redundancy=0.22
- **Overall**: 0.55 → 0.59
- **Domains**: —
- **Nearest corpus papers** (excluded own sources):
  - [0.12] Hybrid DNA–RNA nanotubes as endosomal rupture nucleation scaffolds (2025) (`paper_1acb4c831ac4`)
  - [0.12] In situ PROTAC mRNA LNPs for controllable degradation of hepatic disease targets (2024) (`paper_fa81fe1e1c5d`)
  - [0.11] Ionizable lipid nanoparticles for RNA delivery: design, mechanism, and applications (2017) (`paper_1e6824d52790`)

### 8. Gap: Mechanism of cargo-selective membrane partitioning rema vs Mechanism of cargo-selective membrane partitioning rema
- **Gap ID**: `gap_ac7f71975b4a` · kind=`theory_vs_experiment`
- **Scores**: blended_novelty=0.72 corpus=0.89 prior=0.55 redundancy=0.30
- **Overall**: 0.55 → 0.59
- **Domains**: —
- **Nearest corpus papers** (excluded own sources):
  - [0.11] MicroRNA–mRNA bifunctional LNPs reprogram macrophage phenotypes in solid tumors (2025) (`paper_e0bbbabab6bc`)
  - [0.09] Aptamer-ncRNA chimeras for receptor-mediated cytosolic delivery without ionizable lipids (2024) (`paper_df50380f7f76`)
  - [0.09] Bifunctional ncRNA-mRNA co-delivery reveals interference between RISC loading and translation (2025) (`paper_556b5abd372e`)

### 9. Untested: We hypothesized site-specific Ψ installation would stabilize transcripts without
- **Gap ID**: `gap_fc4b2b92a3b2` · kind=`untested_claim`
- **Scores**: blended_novelty=0.71 corpus=0.84 prior=0.60 redundancy=0.29
- **Overall**: 0.70 → 0.73
- **Domains**: endosomal_escape
- **Nearest corpus papers** (excluded own sources):
  - [0.16] Base-edited HSC mobilization via mRNA-LNP delivery of engraftment enhancers (2024) (`paper_18ff1e01b3e1`)
  - [0.14] Long noncoding RNA scaffolds organize chromatin editors delivered as mRNA-LNP (2024) (`paper_8074cefa64cb`)
  - [0.14] Hybrid nucleic acid nanostructures for programmable intracellular delivery (2023) (`paper_7f05a0e18a0a`)

### 10. Mechanism gap: Mechanism-guided lipid design and live-cell pore sensors are experimentally test
- **Gap ID**: `gap_d1e75ea5cbe1` · kind=`mechanism_unknown`
- **Scores**: blended_novelty=0.71 corpus=0.80 prior=0.70 redundancy=0.44
- **Overall**: 0.64 → 0.65
- **Domains**: —
- **Nearest corpus papers** (excluded own sources):
  - [0.20] Advances in lipid nanoparticle delivery of nucleic acids and beyond (2021) (`paper_bb70be787ad3`)
  - [0.19] Lipid nanoparticles for mRNA delivery (2021) (`paper_306a3c285415`)
  - [0.18] Lipid nanoparticle chemistry: from RNA delivery to the next generation of therapeutics (2019) (`paper_63b6138fd277`)

### 11. Mechanism gap: Conclusions Mechanism-guided formulation and dual-payload-aware assays are neede
- **Gap ID**: `gap_6a15eb341702` · kind=`mechanism_unknown`
- **Scores**: blended_novelty=0.71 corpus=0.87 prior=0.70 redundancy=0.77
- **Overall**: 0.70 → 0.70
- **Domains**: —
- **Nearest corpus papers** (excluded own sources):
  - [0.13] Comparative benchmark of bifunctional ncRNA claims against single-payload LNP baselines (2025) (`paper_ddb0c5b47095`)
  - [0.13] MicroRNA–mRNA bifunctional LNPs reprogram macrophage phenotypes in solid tumors (2025) (`paper_e0bbbabab6bc`)
  - [0.11] Dual-function ADAR recruiting RNAs for therapeutic A-to-I editing with reduced bystander edits (2025) (`paper_7bf3ec125abc`)

### 12. Gap: A key limitation is that extrahepatic disease targets w vs A key limitation is that extrahepatic disease targets w
- **Gap ID**: `gap_60b2ab00c83d` · kind=`theory_vs_experiment`
- **Scores**: blended_novelty=0.71 corpus=0.84 prior=0.60 redundancy=0.31
- **Overall**: 0.59 → 0.62
- **Domains**: lnp, targeting, pks
- **Nearest corpus papers** (excluded own sources):
  - [0.16] Dual-function ADAR recruiting RNAs for therapeutic A-to-I editing with reduced bystander edits (2025) (`paper_7bf3ec125abc`)
  - [0.15] tRNA-like structural motifs stabilize linear mRNA without nucleoside modification (2023) (`paper_4d4e9a3c49de`)
  - [0.15] Hybrid nucleic acid nanostructures for programmable intracellular delivery (2023) (`paper_7f05a0e18a0a`)

