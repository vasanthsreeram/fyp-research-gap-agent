# Experiment protocol cards

_Prototype structured protocols derived from topic proposals. Not wet-lab SOPs — for design discussion and preregistration sketches._

## 1. Protocol: Payload competition in bifunctional ncRNA–mRNA co-delivery nanoparticles
- **ID**: `proto_84224be19136` · **topic**: `topic_32f2bf31c427` · **pack**: `hybrid_ncrna`
- **Primary aim**: Test whether when ncRNA and mRNA share a single LNP, endosomal escape capacity is a zero-sum resource
- **Hypothesis**: When ncRNA and mRNA share a single LNP, endosomal escape capacity is a zero-sum resource; optimizing mass ratio and staggered release chemistry can restore translation without sacrificing silencing.
- **Expected readout**: Identify a ratio/chemistry window with ≥70% of single-payload translation and ≥50% target knockdown.

### Steps
1. Titrate ncRNA:mRNA mass ratios in matched LNPs and measure translation vs knockdown
2. Use orthogonal barcodes to quantify cytosolic arrival of each payload
3. Test delayed-release linker designs that temporally separate escape events

### Controls
- Single-payload mRNA-only LNP (matched total RNA mass)
- Single-payload ncRNA-only LNP
- Scrambled ncRNA + mRNA co-LNP
- Vehicle / empty LNP and untreated cells

### Assay panel
- Dual-payload encapsulation efficiency (RiboGreen / fluorophore orthogonal labels)
- Translation (luciferase or NanoLuc) and target knockdown (RT-qPCR / western) in same wells
- Cytosolic arrival reporters (split-fluorophore or aptamer) for each cargo
- RISC loading / Ago2 IP for ncRNA arm; ribosome profiling optional for mRNA arm
- Cell viability + IFN/ISG panel (CXCL10, IFIT1) for innate cost

### Success criteria
- Primary: Identify a ratio/chemistry window with ≥70% of single-payload translation and ≥50% target knockdown.
- Pre-register binary pass if primary numeric threshold is met with the study's planned analysis (hints in readout: ≥70%, ≥50%).
- Secondary: no worse than reference on pre-specified safety panel (viability drop ≤20% in vitro; no unexpected grade of systemic cytokines in vivo).
- Replicates: ≥3 independent formulations for in vitro; in vivo n powered for primary effect size.

### Stop rules
- Stop expansion if lead fails primary readout in two independent formulation lots.
- Stop in vivo if acute reactogenicity exceeds reference by pre-set cytokine fold-change.
- Redesign (do not force dose escalation) if QC (PDI>0.3 or EE%<70%) is unstable across lots.
- Kill criterion tied to feasibility note: Standard formulation + reporter assays; moderate complexity.

### Timeline
- Week 0–1: freeze hypothesis, SOPs, power calc, preregister primary readout
- Week 2–4: formulation library + QC (size, EE%, endotoxin)
- Week 5–7: in vitro screen with full control set; down-select top 3–5
- Week 8–11: in vivo pilot (n small) on top candidates + reference
- Week 12: stats, failure analysis, decide kill / expand / redesign

### Risks
- Payload competition confounds ratio titration if encapsulation is uneven
- Orthogonal reporters may themselves compete for escape capacity
- Innate activation from dual RNA may mask true efficacy windows

### Materials (skeleton)
- Ionizable lipid + helper + cholesterol + PEG-lipid set (or pack-specific scaffold)
- Orthogonal ncRNA + mRNA payloads with distinct barcodes/labels
- Reporter / therapeutic nucleic acid cargo (sequence-verified)
- Reference clinical-like LNP reagents
- Cell lines relevant to claim + serum for corona / stability assays

**Feasibility:** Standard formulation + reporter assays; moderate complexity.

**Rationale:** Derived from topic 'Payload competition in bifunctional ncRNA–mRNA co-delivery nanoparticles' (pack=hybrid_ncrna, priority=0.68). Anchored on gap [delivery_barrier] 'Limitation: However, delivery to extrahepatic tissues was minimal.' (overall=0.77, testability=0.70). Addresses 3 scored gaps in 'hybrid_ncrna' (pack=hybrid_ncrna, cluster mean overall=0.68, rank=0.89 (pack-balanced)). Success would advance therapeutically relevant nucleic acid delivery and/or hybrid ncRNA mechanisms.

## 2. Protocol: Non-hepatic gene editing via serum-stable hybrid DNA–LNP scaffolds
- **ID**: `proto_a444ae022205` · **topic**: `topic_12541611f99d` · **pack**: `gene_editing`
- **Primary aim**: Test whether dNA-organized ionizable lipid domains improve serum stability and spleen/immune-cell editing without proportional increases in off-target genomic injury
- **Hypothesis**: DNA-organized ionizable lipid domains improve serum stability and spleen/immune-cell editing without proportional increases in off-target genomic injury.
- **Expected readout**: ≥2× extrahepatic editing at matched liver exposure and ≤baseline off-target rate.

### Steps
1. Vary DNA scaffold fraction and measure serum stability + organ editing rates
2. Profile off-target indels and innate activation vs standard LNPs
3. Image endosomal membrane contacts with and without scaffold

### Controls
- Cas/base-editor mRNA only (no guide)
- Guide only (no editor)
- Standard clinical-like ionizable LNP reference (e.g. SM-102 or MC3 class)
- Isotype / non-targeting guide control

### Assay panel
- On-target indel / base-conversion rate (NGS amplicon)
- Off-target panel (guided SITE-seq subset or in silico top-N NGS)
- Serum stability (incubation + gel / encapsulation retention)
- Organ editing biodistribution (qPCR of edit + cargo) at 48–72 h
- Innate activation (IL-6, IFN-α) vs matched empty LNP

### Success criteria
- Primary: ≥2× extrahepatic editing at matched liver exposure and ≤baseline off-target rate.
- Pre-register binary pass if primary numeric threshold is met with the study's planned analysis (hints in readout: ≥2×).
- Secondary: no worse than reference on pre-specified safety panel (viability drop ≤20% in vitro; no unexpected grade of systemic cytokines in vivo).
- Replicates: ≥3 independent formulations for in vitro; in vivo n powered for primary effect size.

### Stop rules
- Stop expansion if lead fails primary readout in two independent formulation lots.
- Stop in vivo if acute reactogenicity exceeds reference by pre-set cytokine fold-change.
- Redesign (do not force dose escalation) if QC (PDI>0.3 or EE%<70%) is unstable across lots.
- Kill criterion tied to feasibility note: Requires editing readouts and careful scaffold manufacturing.

### Timeline
- Week 0–1: freeze hypothesis, SOPs, power calc, preregister primary readout
- Week 2–4: formulation library + QC (size, EE%, endotoxin)
- Week 5–7: in vitro screen with full control set; down-select top 3–5
- Week 8–11: in vivo pilot (n small) on top candidates + reference
- Week 12: stats, failure analysis, decide kill / expand / redesign

### Risks
- Low edit rates in extrahepatic tissue may require large cohorts
- Off-target assays under-sample rare sites
- DNA scaffold manufacturing lot variability

### Materials (skeleton)
- Ionizable lipid + helper + cholesterol + PEG-lipid set (or pack-specific scaffold)
- Editor mRNA + gRNA (and optional DNA scaffold)
- Reporter / therapeutic nucleic acid cargo (sequence-verified)
- Reference clinical-like LNP reagents
- Cell lines relevant to claim + serum for corona / stability assays

**Feasibility:** Requires editing readouts and careful scaffold manufacturing.

**Rationale:** Derived from topic 'Non-hepatic gene editing via serum-stable hybrid DNA–LNP scaffolds' (pack=gene_editing, priority=0.65). Anchored on gap [untested_claim] 'Untested: We hypothesized peptide branching improves endosomal buffering versus linear pep' (overall=0.72, testability=0.72). Addresses 3 scored gaps in 'gene_therapy' (pack=gene_editing, cluster mean overall=0.65, rank=0.84 (pack-balanced)). Success would advance therapeutically relevant nucleic acid delivery and/or hybrid ncRNA mechanisms.

## 3. Protocol: Ligand-displaying LNPs for extrahepatic targeting: avidity vs specificity
- **ID**: `proto_4f3c523b679c` · **topic**: `topic_af77348f5103` · **pack**: `lnp_core`
- **Primary aim**: Test whether multivalent display of low-affinity targeting ligands (e
- **Hypothesis**: Multivalent display of low-affinity targeting ligands (e.g., mannose, transferrin, or anti-CD3 scFv) on LNP surfaces achieves higher tissue selectivity than high-affinity monovalent targeting, due to reduced off-target uptake by liver macrophages.
- **Expected readout**: Target-to-liver uptake ratio; ≥5× improvement over non-targeted LNPs.

### Steps
1. Synthesize LNPs with controlled densities of selected ligands (0–100% surface coverage)
2. Quantify uptake in target vs off-target cells with flow cytometry
3. Test in vivo biodistribution with reporter mRNAs in xenograft or disease models

### Controls
- Clinical-like reference LNP (SM-102 or MC3 class) at matched dose
- Non-ionizable lipid control particle
- Free nucleic acid (no particle)
- Vehicle-only

### Assay panel
- Size / PDI / zeta (DLS) and encapsulation efficiency
- In vitro transfection across ≥3 cell types (hepato, endo, immune)
- Endosomal escape proxy (galectin puncta or calcein release)
- In vivo reporter biodistribution (liver vs extrahepatic organs)
- Repeat-dose PK / anti-PEG IgM if multi-dose claim

### Success criteria
- Primary: Target-to-liver uptake ratio; ≥5× improvement over non-targeted LNPs.
- Pre-register binary pass if primary numeric threshold is met with the study's planned analysis (hints in readout: ≥5×).
- Secondary: no worse than reference on pre-specified safety panel (viability drop ≤20% in vitro; no unexpected grade of systemic cytokines in vivo).
- Replicates: ≥3 independent formulations for in vitro; in vivo n powered for primary effect size.

### Stop rules
- Stop expansion if lead fails primary readout in two independent formulation lots.
- Stop in vivo if acute reactogenicity exceeds reference by pre-set cytokine fold-change.
- Redesign (do not force dose escalation) if QC (PDI>0.3 or EE%<70%) is unstable across lots.
- Kill criterion tied to feasibility note: Lipid-PEG-ligand chemistry is standard; main risk is synthesis scale-up.

### Timeline
- Week 0–1: freeze hypothesis, SOPs, power calc, preregister primary readout
- Week 2–4: formulation library + QC (size, EE%, endotoxin)
- Week 5–7: in vitro screen with full control set; down-select top 3–5
- Week 8–11: in vivo pilot (n small) on top candidates + reference
- Week 12: stats, failure analysis, decide kill / expand / redesign

### Risks
- In vitro transfection poorly predicts in vivo tropism
- Protein corona differs across serum lots / species
- Microscopy endosomal-escape assays are low-throughput and operator-sensitive

### Materials (skeleton)
- Ionizable lipid + helper + cholesterol + PEG-lipid set (or pack-specific scaffold)
- Reporter / therapeutic nucleic acid cargo (sequence-verified)
- Reference clinical-like LNP reagents
- Cell lines relevant to claim + serum for corona / stability assays
- Capability: Quantify uptake in target vs off-target cells with flow cytometry

**Feasibility:** Lipid-PEG-ligand chemistry is standard; main risk is synthesis scale-up.

**Rationale:** Derived from topic 'Ligand-displaying LNPs for extrahepatic targeting: avidity vs specificity' (pack=lnp_core, priority=0.71). Anchored on gap [delivery_barrier] 'Limitation: Extrahepatic delivery remains elusive at therapeutically relevant doses without ' (overall=0.80, testability=0.70). Addresses 3 scored gaps in 'targeting' (pack=lnp_core, cluster mean overall=0.71, rank=0.82 (pack-balanced)). Success would advance therapeutically relevant nucleic acid delivery and/or hybrid ncRNA mechanisms.

## 4. Protocol: Quantitative bottleneck analysis of the LNP delivery cascade
- **ID**: `proto_28c4bc773100` · **topic**: `topic_2c649c904769` · **pack**: `lnp_core`
- **Primary aim**: Test whether endosomal escape—not uptake or encapsulation—is the dominant loss term in the delivery cascade for most clinical-like LNP compositions, and 10× escape gains are necessary and sufficient for transformative dose reduction
- **Hypothesis**: Endosomal escape—not uptake or encapsulation—is the dominant loss term in the delivery cascade for most clinical-like LNP compositions, and 10× escape gains are necessary and sufficient for transformative dose reduction.
- **Expected readout**: Ranked elasticities per cascade step; validated 5× dose reduction via top lever.

### Steps
1. Build a quantitative cascade map (injection→uptake→escape→translation) with barcoded mRNA
2. Perturb each step independently and measure sensitivity of protein output
3. Identify the step with highest elasticity for dose reduction

### Controls
- Clinical-like reference LNP (SM-102 or MC3 class) at matched dose
- Non-ionizable lipid control particle
- Free nucleic acid (no particle)
- Vehicle-only

### Assay panel
- Size / PDI / zeta (DLS) and encapsulation efficiency
- In vitro transfection across ≥3 cell types (hepato, endo, immune)
- Endosomal escape proxy (galectin puncta or calcein release)
- In vivo reporter biodistribution (liver vs extrahepatic organs)
- Repeat-dose PK / anti-PEG IgM if multi-dose claim

### Success criteria
- Primary: Ranked elasticities per cascade step; validated 5× dose reduction via top lever.
- Pre-register binary pass if primary numeric threshold is met with the study's planned analysis (hints in readout:  5×).
- Secondary: no worse than reference on pre-specified safety panel (viability drop ≤20% in vitro; no unexpected grade of systemic cytokines in vivo).
- Replicates: ≥3 independent formulations for in vitro; in vivo n powered for primary effect size.

### Stop rules
- Stop expansion if lead fails primary readout in two independent formulation lots.
- Stop in vivo if acute reactogenicity exceeds reference by pre-set cytokine fold-change.
- Redesign (do not force dose escalation) if QC (PDI>0.3 or EE%<70%) is unstable across lots.
- Kill criterion tied to feasibility note: Requires careful assay development; high scientific payoff.

### Timeline
- Week 0–1: freeze hypothesis, SOPs, power calc, preregister primary readout
- Week 2–4: formulation library + QC (size, EE%, endotoxin)
- Week 5–7: in vitro screen with full control set; down-select top 3–5
- Week 8–11: in vivo pilot (n small) on top candidates + reference
- Week 12: stats, failure analysis, decide kill / expand / redesign

### Risks
- In vitro transfection poorly predicts in vivo tropism
- Protein corona differs across serum lots / species
- Microscopy endosomal-escape assays are low-throughput and operator-sensitive

### Materials (skeleton)
- Ionizable lipid + helper + cholesterol + PEG-lipid set (or pack-specific scaffold)
- Reporter / therapeutic nucleic acid cargo (sequence-verified)
- Reference clinical-like LNP reagents
- Cell lines relevant to claim + serum for corona / stability assays

**Feasibility:** Requires careful assay development; high scientific payoff.

**Rationale:** Derived from topic 'Quantitative bottleneck analysis of the LNP delivery cascade' (pack=lnp_core, priority=0.70). Anchored on gap [untested_claim] 'Untested: Conclusions Ionizable lipid design is clinically validated yet mechanistically u' (overall=0.76, testability=0.72). Addresses 3 scored gaps in 'delivery_efficiency' (pack=lnp_core, cluster mean overall=0.70, rank=0.81 (pack-balanced)). Success would advance therapeutically relevant nucleic acid delivery and/or hybrid ncRNA mechanisms.

## 5. Protocol: Decoupling innate immune activation from LNP delivery potency
- **ID**: `proto_db5599d414aa` · **topic**: `topic_8bee130d8962` · **pack**: `lnp_core`
- **Primary aim**: Test whether ionizable lipid structure independently drives TLR/inflammasome activation versus endosomal escape
- **Hypothesis**: Ionizable lipid structure independently drives TLR/inflammasome activation versus endosomal escape; lipids can be optimized for high delivery with low reactogenicity.
- **Expected readout**: ≥2× potency/inflammation ratio vs SM-102 or MC3 reference LNPs.

### Steps
1. Screen ionizable lipids for IL-6/IFN reporter activation in vitro
2. Correlate innate activation with endosomal escape efficiency
3. Validate low-inflammation high-potency candidates in mice

### Controls
- Clinical-like reference LNP (SM-102 or MC3 class) at matched dose
- Non-ionizable lipid control particle
- Free nucleic acid (no particle)
- Vehicle-only

### Assay panel
- Size / PDI / zeta (DLS) and encapsulation efficiency
- In vitro transfection across ≥3 cell types (hepato, endo, immune)
- Endosomal escape proxy (galectin puncta or calcein release)
- In vivo reporter biodistribution (liver vs extrahepatic organs)
- Repeat-dose PK / anti-PEG IgM if multi-dose claim

### Success criteria
- Primary: ≥2× potency/inflammation ratio vs SM-102 or MC3 reference LNPs.
- Pre-register binary pass if primary numeric threshold is met with the study's planned analysis (hints in readout: ≥2×, 102 , 3 ).
- Secondary: no worse than reference on pre-specified safety panel (viability drop ≤20% in vitro; no unexpected grade of systemic cytokines in vivo).
- Replicates: ≥3 independent formulations for in vitro; in vivo n powered for primary effect size.

### Stop rules
- Stop expansion if lead fails primary readout in two independent formulation lots.
- Stop in vivo if acute reactogenicity exceeds reference by pre-set cytokine fold-change.
- Redesign (do not force dose escalation) if QC (PDI>0.3 or EE%<70%) is unstable across lots.
- Kill criterion tied to feasibility note: Cell reporter assays are accessible; in vivo cytokine panels standard.

### Timeline
- Week 0–1: freeze hypothesis, SOPs, power calc, preregister primary readout
- Week 2–4: formulation library + QC (size, EE%, endotoxin)
- Week 5–7: in vitro screen with full control set; down-select top 3–5
- Week 8–11: in vivo pilot (n small) on top candidates + reference
- Week 12: stats, failure analysis, decide kill / expand / redesign

### Risks
- In vitro transfection poorly predicts in vivo tropism
- Protein corona differs across serum lots / species
- Microscopy endosomal-escape assays are low-throughput and operator-sensitive

### Materials (skeleton)
- Ionizable lipid + helper + cholesterol + PEG-lipid set (or pack-specific scaffold)
- Reporter / therapeutic nucleic acid cargo (sequence-verified)
- Reference clinical-like LNP reagents
- Cell lines relevant to claim + serum for corona / stability assays

**Feasibility:** Cell reporter assays are accessible; in vivo cytokine panels standard.

**Rationale:** Derived from topic 'Decoupling innate immune activation from LNP delivery potency' (pack=lnp_core, priority=0.68). Anchored on gap [delivery_barrier] 'Limitation: Decoupling immunogenicity from delivery remains a major challenge.' (overall=0.73, testability=0.70). Addresses 3 scored gaps in 'immunogenicity' (pack=lnp_core, cluster mean overall=0.68, rank=0.79 (pack-balanced)). Success would advance therapeutically relevant nucleic acid delivery and/or hybrid ncRNA mechanisms.
