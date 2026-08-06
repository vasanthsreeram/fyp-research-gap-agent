# Novelty-vs-corpus report

| Field | Value |
|-------|-------|
| **Backend** | `lexical` |
| **Papers** | 52 |
| **Gaps** | 119 |
| **Mean corpus novelty** | 0.78 |
| **Mean gap redundancy** | 0.38 |
| **High novelty (≥0.55)** | 119 |
| **Redundant gaps (≥0.55)** | 9 |

_Own source papers excluded from nearest match. High corpus_novelty ≈ gap text distant from rest of corpus; high gap_redundancy ≈ near-duplicate of another gap._

## Top surprising gaps (by blended novelty, n=12)

### 1. Cross-paper tension: However, the exact molecular mechanism of bilayer disruption remains controversi
- **Gap ID**: `gap_861eaa8c8485` · kind=`cross_paper_tension`
- **Scores**: blended_novelty=0.76 corpus=0.76 prior=0.88 redundancy=0.44
- **Overall**: 0.82 → 0.79
- **Domains**: lnp, endosomal_escape, targeting, gene_therapy, hybrid_ncrna
- **Nearest corpus papers** (excluded own sources):
  - [0.24] The endosomal escape of lipid nanoparticles: mechanisms and strategies for improvement (2021) (`paper_f95a5456ca2e`)
  - [0.22] Endosomal escape of lipid nanoparticles: a mechanistic investigation (2020) (`paper_417e28a34abd`)
  - [0.22] Ionizable lipid nanoparticles for RNA delivery: design, mechanism, and applications (2017) (`paper_012a9503a1bc`)

### 2. Limitation: Extrahepatic delivery remains elusive at therapeutically relevant doses without 
- **Gap ID**: `gap_f5166d573691` · kind=`delivery_barrier`
- **Scores**: blended_novelty=0.75 corpus=0.86 prior=0.70 redundancy=0.36
- **Overall**: 0.78 → 0.80
- **Domains**: targeting
- **Nearest corpus papers** (excluded own sources):
  - [0.14] CRISPR-Cas9 lipid nanoparticle systems for in vivo gene editing (2018) (`paper_b974ca809a3c`)
  - [0.14] Small interfering RNA delivery via lipid nanoparticles for liver target engagement (2018) (`paper_05e234315ab3`)
  - [0.13] Lipid nanoparticles for mRNA delivery (2021) (`paper_13775d65e865`)

### 3. Limitation: Results indicate cytosolic RNP competition is a post-escape bottleneck distinct 
- **Gap ID**: `gap_50668e85e7c9` · kind=`delivery_barrier`
- **Scores**: blended_novelty=0.75 corpus=0.83 prior=0.70 redundancy=0.25
- **Overall**: 0.72 → 0.74
- **Domains**: endosomal_escape
- **Nearest corpus papers** (excluded own sources):
  - [0.17] The endosomal escape of lipid nanoparticles: mechanisms and strategies for improvement (2021) (`paper_f95a5456ca2e`)
  - [0.15] Aptamer-ncRNA chimeras for receptor-mediated cytosolic delivery without ionizable lipids (2024) (`paper_1f92f1c4f678`)
  - [0.14] Endosomal escape of lipid nanoparticles: a mechanistic investigation (2020) (`paper_417e28a34abd`)

### 4. Limitation: However, delivery to extrahepatic tissues was minimal.
- **Gap ID**: `gap_c2ebb78b1420` · kind=`delivery_barrier`
- **Scores**: blended_novelty=0.74 corpus=0.83 prior=0.70 redundancy=0.32
- **Overall**: 0.76 → 0.77
- **Domains**: targeting
- **Nearest corpus papers** (excluded own sources):
  - [0.17] CRISPR-Cas9 lipid nanoparticle systems for in vivo gene editing (2018) (`paper_b974ca809a3c`)
  - [0.15] Extrahepatic targeting of lipid nanoparticles in vivo (2021) (`paper_ed92a814dc51`)
  - [0.15] Bifunctional guide–scaffold RNAs couple Cas9 editing to local transcript silencing (2025) (`paper_8801eaa3b088`)

### 5. Mechanism gap: We hypothesized that origami geometry would protect cargo and promote endosomal 
- **Gap ID**: `gap_7cef098c0806` · kind=`mechanism_unknown`
- **Scores**: blended_novelty=0.74 corpus=0.76 prior=0.80 redundancy=0.32
- **Overall**: 0.67 → 0.66
- **Domains**: endosomal_escape
- **Nearest corpus papers** (excluded own sources):
  - [0.24] Hybrid nucleic acid nanostructures for programmable intracellular delivery (2023) (`paper_1e16756cdbef`)
  - [0.23] The endosomal escape of lipid nanoparticles: mechanisms and strategies for improvement (2021) (`paper_f95a5456ca2e`)
  - [0.23] Bifunctional guide–scaffold RNAs couple Cas9 editing to local transcript silencing (2025) (`paper_8801eaa3b088`)

### 6. Untested: We propose ribosome dwell time modulates endosomal TLR exposure via altered unpa
- **Gap ID**: `gap_135ff1b2e880` · kind=`untested_claim`
- **Scores**: blended_novelty=0.74 corpus=0.85 prior=0.65 redundancy=0.27
- **Overall**: 0.71 → 0.73
- **Domains**: lnp, endosomal_escape
- **Nearest corpus papers** (excluded own sources):
  - [0.15] The endosomal escape of lipid nanoparticles: mechanisms and strategies for improvement (2021) (`paper_f95a5456ca2e`)
  - [0.14] Quantitative single-cell map of LNP uptake, endosomal progression, and mRNA translation (2023) (`paper_f62fc271e55d`)
  - [0.11] Aptamer-ncRNA chimeras for receptor-mediated cytosolic delivery without ionizable lipids (2024) (`paper_1f92f1c4f678`)

### 7. Limitation: A major barrier is manufacturing long structured RNA at clinical purity.
- **Gap ID**: `gap_c9c18fe2c9ca` · kind=`delivery_barrier`
- **Scores**: blended_novelty=0.73 corpus=0.87 prior=0.60 redundancy=0.25
- **Overall**: 0.70 → 0.73
- **Domains**: —
- **Nearest corpus papers** (excluded own sources):
  - [0.13] Serum-stable DNA-ionizable lipid hybrid nanoparticles for gene editing outside the liver (2024) (`paper_18485e6b447b`)
  - [0.12] Hybrid nucleic acid nanostructures for programmable intracellular delivery (2023) (`paper_1e16756cdbef`)
  - [0.10] Aptamer-ncRNA chimeras for receptor-mediated cytosolic delivery without ionizable lipids (2024) (`paper_1f92f1c4f678`)

### 8. Limitation: Polymeric particles showed 5-fold higher epithelial association but only 1.2-fol
- **Gap ID**: `gap_0e277cb3fbe6` · kind=`delivery_barrier`
- **Scores**: blended_novelty=0.73 corpus=0.87 prior=0.60 redundancy=0.30
- **Overall**: 0.68 → 0.71
- **Domains**: —
- **Nearest corpus papers** (excluded own sources):
  - [0.13] tRNA-like structural motifs stabilize linear mRNA without nucleoside modification (2023) (`paper_81a91c8871e9`)
  - [0.13] Aptamer-ncRNA chimeras for receptor-mediated cytosolic delivery without ionizable lipids (2024) (`paper_1f92f1c4f678`)
  - [0.12] Rapidly adaptable nanoparticle platforms for mRNA delivery to the lung (2021) (`paper_a475aae5ac03`)

### 9. Gap: Prior work demonstrated multi-day expression, yet mecha vs Prior work demonstrated multi-day expression, yet mecha
- **Gap ID**: `gap_2f477f66bad5` · kind=`theory_vs_experiment`
- **Scores**: blended_novelty=0.72 corpus=0.88 prior=0.55 redundancy=0.22
- **Overall**: 0.55 → 0.59
- **Domains**: —
- **Nearest corpus papers** (excluded own sources):
  - [0.12] Hybrid DNA–RNA nanotubes as endosomal rupture nucleation scaffolds (2025) (`paper_32cf82745b3c`)
  - [0.12] In situ PROTAC mRNA LNPs for controllable degradation of hepatic disease targets (2024) (`paper_f6cfdef0fc58`)
  - [0.11] Ionizable lipid nanoparticles for RNA delivery: design, mechanism, and applications (2017) (`paper_012a9503a1bc`)

### 10. Gap: Mechanism of cargo-selective membrane partitioning rema vs Mechanism of cargo-selective membrane partitioning rema
- **Gap ID**: `gap_983a61af6a8b` · kind=`theory_vs_experiment`
- **Scores**: blended_novelty=0.72 corpus=0.89 prior=0.55 redundancy=0.30
- **Overall**: 0.55 → 0.59
- **Domains**: —
- **Nearest corpus papers** (excluded own sources):
  - [0.11] MicroRNA–mRNA bifunctional LNPs reprogram macrophage phenotypes in solid tumors (2025) (`paper_07e52a686047`)
  - [0.09] Aptamer-ncRNA chimeras for receptor-mediated cytosolic delivery without ionizable lipids (2024) (`paper_1f92f1c4f678`)
  - [0.09] Bifunctional ncRNA-mRNA co-delivery reveals interference between RISC loading and translation (2025) (`paper_2100d54f2257`)

### 11. Limitation: Scale-up of scaffold synthesis remains a practical barrier to clinical manufactu
- **Gap ID**: `gap_11b117b5ed6d` · kind=`delivery_barrier`
- **Scores**: blended_novelty=0.72 corpus=0.85 prior=0.60 redundancy=0.26
- **Overall**: 0.70 → 0.73
- **Domains**: —
- **Nearest corpus papers** (excluded own sources):
  - [0.15] CRISPR-Cas9 lipid nanoparticle systems for in vivo gene editing (2018) (`paper_b974ca809a3c`)
  - [0.14] Long noncoding RNA scaffolds organize chromatin editors delivered as mRNA-LNP (2024) (`paper_ceb6d065168c`)
  - [0.14] Hybrid DNA–RNA nanotubes as endosomal rupture nucleation scaffolds (2025) (`paper_32cf82745b3c`)

### 12. Mechanism gap: Aptamer-ncRNA chimeras for receptor-mediated cytosolic delivery without ionizabl
- **Gap ID**: `gap_19fc4db6016e` · kind=`mechanism_unknown`
- **Scores**: blended_novelty=0.72 corpus=0.80 prior=0.70 redundancy=0.37
- **Overall**: 0.63 → 0.64
- **Domains**: lnp, hybrid_ncrna
- **Nearest corpus papers** (excluded own sources):
  - [0.20] Bifunctional ncRNA-mRNA co-delivery reveals interference between RISC loading and translation (2025) (`paper_2100d54f2257`)
  - [0.19] Single-molecule fluorescence reveals asynchronous cytosolic arrival of co-encapsulated mRNA and ncRNA (2025) (`paper_26f8f11d3b56`)
  - [0.18] Hybrid nucleic acid nanostructures for programmable intracellular delivery (2023) (`paper_1e16756cdbef`)

