# Meeting Notes: FYP Professor Discussion

Date: 2026-07-01

## Confirmed Project Direction

The FYP was effectively allocated during this discussion. The working direction is an AI-assisted framework for finding scientifically surprising, high-impact research opportunities, with biology as the first target domain.

The most important framing is not just "find gaps in papers." The system should identify ideas that are surprising but plausibly true, then help select candidates that can be tested experimentally. A successful first demonstration should be in a biology problem where the model proposes something non-obvious, the lab tests it, and the result is meaningful.

## Key Research Theme

Use AI to reduce the time needed to recognize the right scientific problems.

Possible early domain:

- Protein and nucleic acid chemistry
- Molecular engineering
- Hybrid or bifunctional non-coding RNA
- Translation/ribosome-related mechanisms
- Engineered biological "technology" inspired by naturally evolved molecular machinery

The professor mentioned a surprising RNA-like mechanism with aspects of transfer RNA and messenger RNA, able to splice in new genetic information during translation. Similar mechanisms may not be known in eukaryotes, mammals, or humans, but analogous hybrid non-coding RNA functions could exist or be engineered.

## Candidate System Objective

Build a pipeline that scores research ideas or papers by a "surprise" signal while filtering out unsupported or fraudulent claims.

The system should distinguish:

- Surprising and plausible
- Surprising but likely wrong
- Already known or memorized by the model
- High impact and experimentally testable
- Retrospectively suspicious or fraudulent

## Model Strategy

Large language models may have memorized much of the scientific literature, which can make retrospective evaluation misleading. The project should explicitly control for this.

Suggested safeguards:

- Prefer recent papers published after a model's training cutoff for forward testing.
- Try smaller models, because they are more likely to preserve language and logic without memorizing as much domain knowledge.
- Use open models where training data is more transparent.
- Test whether a model appears to have memorized a paper by asking it to continue or reconstruct withheld text.
- Compare retrospective tests against retracted papers with prospective tests on newly published papers.

## Evaluation Ideas

Potential evaluation tracks:

- Retrospective: known retracted papers, known surprising discoveries, or known failed hypotheses.
- Prospective: papers from 2026 or later that are unlikely to be in training data.
- Expert review: professor or lab members rate generated ideas for surprise, plausibility, feasibility, and impact.
- Experimental follow-up: pick one candidate idea that can be tested in a lab workflow.

The professor saw dual-use value: the same system might identify exciting discoveries and also flag papers that are surprising for the wrong reasons.

## Lab Context

The professor's lab is expected to be primarily experimental, with heavy use of high-throughput and automated equipment. The philosophy is "dumb automation": robots and equipment reduce repetitive lab work, while humans remain the agents deciding what to do.

Relevant lab strengths and collaborators mentioned:

- Protein-nucleic acid chemistry
- Cloning, sequencing, next-generation sequencing, genomics, and bioinformatics
- Microscopy and bioimaging
- Applied deep learning on biological data
- Protein engineering
- Virology and viral entry into cells
- Nucleic acid delivery
- Molecular mechanisms, including aging-related work

The lab is expected to evolve from mostly technology-building toward a balance of technology and science.

## Immediate Next Step

Vas should write notes from the conversation and propose concrete approaches. The professor said the project formally starts around August, but Vas can make progress earlier. Follow-up can happen electronically, and in-person meetings are possible while the professor is in Singapore.

## Action Items

- Draft a short project memo from this meeting.
- Propose two or three possible technical approaches.
- Define an initial benchmark that avoids LLM memorization.
- Identify a small set of recent biology papers for prospective testing.
- Add a scoring rubric for surprise, plausibility, feasibility, and impact.
- Keep raw meeting audio/transcript local unless Vas explicitly wants it committed.
