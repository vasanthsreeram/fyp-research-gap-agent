# Novelty-vs-corpus report

| Field | Value |
|-------|-------|
| **Backend** | `lexical` |
| **Papers** | 52 |
| **Gaps** | 104 |
| **Mean corpus novelty** | 0.79 |
| **Mean gap redundancy** | 0.37 |
| **High novelty (≥0.55)** | 104 |
| **Redundant gaps (≥0.55)** | 7 |

_Own source papers excluded from nearest match. High corpus_novelty ≈ gap text distant from rest of corpus; high gap_redundancy ≈ near-duplicate of another gap._

## Top surprising gaps (by blended novelty, n=12)

### 1. Limitation: Results indicate cytosolic RNP competition is a post-escape bottleneck distinct 
- **Gap ID**: `gap_97eceb9be220` · kind=`delivery_barrier`
- **Scores**: blended_novelty=0.75 corpus=0.83 prior=0.70 redundancy=0.25
- **Overall**: 0.72 → 0.74
- **Domains**: endosomal_escape
- **Nearest corpus papers** (excluded own sources):
  - [0.17] The endosomal escape of lipid nanoparticles: mechanisms and strategies for improvement (2021) (`paper_c7e8fd1221af`)
  - [0.15] Aptamer-ncRNA chimeras for receptor-mediated cytosolic delivery without ionizable lipids (2024) (`paper_23ecae94b297`)
  - [0.14] Endosomal escape of lipid nanoparticles: a mechanistic investigation (2020) (`paper_b9627cb1b710`)

### 2. Cross-paper tension: However, the exact molecular mechanism of bilayer disruption remains controversi
- **Gap ID**: `gap_2d9ae4fab851` · kind=`cross_paper_tension`
- **Scores**: blended_novelty=0.75 corpus=0.76 prior=0.88 redundancy=0.47
- **Overall**: 0.82 → 0.78
- **Domains**: endosomal_escape, targeting, gene_therapy, hybrid_ncrna
- **Nearest corpus papers** (excluded own sources):
  - [0.24] Lipid nanoparticles for mRNA delivery (2021) (`paper_1fa5e2118f32`)
  - [0.21] CRISPR-Cas9 lipid nanoparticle systems for in vivo gene editing (2018) (`paper_532b86cc69ae`)
  - [0.20] Rapidly adaptable nanoparticle platforms for mRNA delivery to the lung (2021) (`paper_27d2bf201d94`)

### 3. Untested: We propose ribosome dwell time modulates endosomal TLR exposure via altered unpa
- **Gap ID**: `gap_2545ca567b9e` · kind=`untested_claim`
- **Scores**: blended_novelty=0.74 corpus=0.85 prior=0.65 redundancy=0.27
- **Overall**: 0.71 → 0.73
- **Domains**: lnp, endosomal_escape
- **Nearest corpus papers** (excluded own sources):
  - [0.15] The endosomal escape of lipid nanoparticles: mechanisms and strategies for improvement (2021) (`paper_c7e8fd1221af`)
  - [0.14] Quantitative single-cell map of LNP uptake, endosomal progression, and mRNA translation (2023) (`paper_9987f496e55d`)
  - [0.11] Aptamer-ncRNA chimeras for receptor-mediated cytosolic delivery without ionizable lipids (2024) (`paper_23ecae94b297`)

### 4. Limitation: However, delivery to extrahepatic tissues was minimal.
- **Gap ID**: `gap_d8a9ff3ff4eb` · kind=`delivery_barrier`
- **Scores**: blended_novelty=0.73 corpus=0.83 prior=0.70 redundancy=0.38
- **Overall**: 0.76 → 0.77
- **Domains**: targeting
- **Nearest corpus papers** (excluded own sources):
  - [0.17] CRISPR-Cas9 lipid nanoparticle systems for in vivo gene editing (2018) (`paper_532b86cc69ae`)
  - [0.15] Extrahepatic targeting of lipid nanoparticles in vivo (2021) (`paper_8c324faebf8d`)
  - [0.15] Bifunctional guide–scaffold RNAs couple Cas9 editing to local transcript silencing (2025) (`paper_c6d523abb249`)

### 5. Mechanism gap: We hypothesized that origami geometry would protect cargo and promote endosomal 
- **Gap ID**: `gap_3b14f0cd6dc4` · kind=`mechanism_unknown`
- **Scores**: blended_novelty=0.73 corpus=0.76 prior=0.80 redundancy=0.38
- **Overall**: 0.67 → 0.65
- **Domains**: endosomal_escape
- **Nearest corpus papers** (excluded own sources):
  - [0.24] Hybrid nucleic acid nanostructures for programmable intracellular delivery (2023) (`paper_b551c556b1a5`)
  - [0.23] The endosomal escape of lipid nanoparticles: mechanisms and strategies for improvement (2021) (`paper_c7e8fd1221af`)
  - [0.23] Bifunctional guide–scaffold RNAs couple Cas9 editing to local transcript silencing (2025) (`paper_c6d523abb249`)

### 6. Limitation: A major barrier is manufacturing long structured RNA at clinical purity.
- **Gap ID**: `gap_c2f5dbea297f` · kind=`delivery_barrier`
- **Scores**: blended_novelty=0.73 corpus=0.87 prior=0.60 redundancy=0.25
- **Overall**: 0.70 → 0.73
- **Domains**: —
- **Nearest corpus papers** (excluded own sources):
  - [0.13] Serum-stable DNA-ionizable lipid hybrid nanoparticles for gene editing outside the liver (2024) (`paper_a170dae93a1a`)
  - [0.12] Hybrid nucleic acid nanostructures for programmable intracellular delivery (2023) (`paper_b551c556b1a5`)
  - [0.10] Aptamer-ncRNA chimeras for receptor-mediated cytosolic delivery without ionizable lipids (2024) (`paper_23ecae94b297`)

### 7. Limitation: Polymeric particles showed 5-fold higher epithelial association but only 1.2-fol
- **Gap ID**: `gap_3e6a6b8c7eeb` · kind=`delivery_barrier`
- **Scores**: blended_novelty=0.73 corpus=0.87 prior=0.60 redundancy=0.30
- **Overall**: 0.68 → 0.71
- **Domains**: —
- **Nearest corpus papers** (excluded own sources):
  - [0.13] tRNA-like structural motifs stabilize linear mRNA without nucleoside modification (2023) (`paper_7161416bd381`)
  - [0.13] Aptamer-ncRNA chimeras for receptor-mediated cytosolic delivery without ionizable lipids (2024) (`paper_23ecae94b297`)
  - [0.12] Rapidly adaptable nanoparticle platforms for mRNA delivery to the lung (2021) (`paper_27d2bf201d94`)

### 8. Gap: Mechanism of cargo-selective membrane partitioning rema vs Mechanism of cargo-selective membrane partitioning rema
- **Gap ID**: `gap_85e344bf8d65` · kind=`theory_vs_experiment`
- **Scores**: blended_novelty=0.72 corpus=0.89 prior=0.55 redundancy=0.30
- **Overall**: 0.55 → 0.59
- **Domains**: —
- **Nearest corpus papers** (excluded own sources):
  - [0.11] MicroRNA–mRNA bifunctional LNPs reprogram macrophage phenotypes in solid tumors (2025) (`paper_5e1632a5c945`)
  - [0.09] Aptamer-ncRNA chimeras for receptor-mediated cytosolic delivery without ionizable lipids (2024) (`paper_23ecae94b297`)
  - [0.09] Bifunctional ncRNA-mRNA co-delivery reveals interference between RISC loading and translation (2025) (`paper_6a757415fe2c`)

### 9. Limitation: Scale-up of scaffold synthesis remains a practical barrier to clinical manufactu
- **Gap ID**: `gap_5e13ae2b57a7` · kind=`delivery_barrier`
- **Scores**: blended_novelty=0.72 corpus=0.85 prior=0.60 redundancy=0.26
- **Overall**: 0.70 → 0.73
- **Domains**: —
- **Nearest corpus papers** (excluded own sources):
  - [0.15] CRISPR-Cas9 lipid nanoparticle systems for in vivo gene editing (2018) (`paper_532b86cc69ae`)
  - [0.14] Long noncoding RNA scaffolds organize chromatin editors delivered as mRNA-LNP (2024) (`paper_4f904a1ab893`)
  - [0.14] Hybrid DNA–RNA nanotubes as endosomal rupture nucleation scaffolds (2025) (`paper_4bb7a2ec1734`)

### 10. Mechanism gap: Aptamer-ncRNA chimeras for receptor-mediated cytosolic delivery without ionizabl
- **Gap ID**: `gap_3d55d91f2bd0` · kind=`mechanism_unknown`
- **Scores**: blended_novelty=0.72 corpus=0.80 prior=0.70 redundancy=0.37
- **Overall**: 0.63 → 0.64
- **Domains**: hybrid_ncrna, lnp
- **Nearest corpus papers** (excluded own sources):
  - [0.20] Bifunctional ncRNA-mRNA co-delivery reveals interference between RISC loading and translation (2025) (`paper_6a757415fe2c`)
  - [0.19] Single-molecule fluorescence reveals asynchronous cytosolic arrival of co-encapsulated mRNA and ncRNA (2025) (`paper_6effd989db10`)
  - [0.18] Hybrid nucleic acid nanostructures for programmable intracellular delivery (2023) (`paper_b551c556b1a5`)

### 11. Limitation: These findings underscore the need for fundamental advances in understanding nan
- **Gap ID**: `gap_90918407ad04` · kind=`delivery_barrier`
- **Scores**: blended_novelty=0.71 corpus=0.80 prior=0.70 redundancy=0.39
- **Overall**: 0.73 → 0.73
- **Domains**: targeting
- **Nearest corpus papers** (excluded own sources):
  - [0.20] CRISPR-Cas9 lipid nanoparticle systems for in vivo gene editing (2018) (`paper_532b86cc69ae`)
  - [0.18] Lipid nanoparticles for mRNA delivery (2021) (`paper_1fa5e2118f32`)
  - [0.17] Rapidly adaptable nanoparticle platforms for mRNA delivery to the lung (2021) (`paper_27d2bf201d94`)

### 12. Limitation: However, no formulation achieved significant targeting to muscle, heart, or brai
- **Gap ID**: `gap_85b43ad560ae` · kind=`delivery_barrier`
- **Scores**: blended_novelty=0.71 corpus=0.86 prior=0.60 redundancy=0.37
- **Overall**: 0.68 → 0.70
- **Domains**: —
- **Nearest corpus papers** (excluded own sources):
  - [0.14] CRISPR-Cas9 lipid nanoparticle systems for in vivo gene editing (2018) (`paper_532b86cc69ae`)
  - [0.11] Designing lipid nanoparticles for targeted delivery of nucleic acids to the brain (2020) (`paper_484bc54996e7`)
  - [0.10] Small interfering RNA delivery via lipid nanoparticles for liver target engagement (2018) (`paper_b524a709d805`)

