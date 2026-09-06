# Literary OS — P07-A RFV2 Historical Vectorizer Recovery Addendum R1
Date: 2026-09-07
Classification: PREFORMAL RECOVERY ADDENDUM / PRERESULT FREEZE

## Recovery evidence
After the first reconstructed full-corpus execution timed out before producing/viewing any six-case result, the sealed Research Experiment Learning Recovery Master was searched for the exact R37-R/R38-R retrieval controls.

Recovered historical registry text states:
- vectorizer: `TF-IDF char_wb ngram 2-5, min_df=1, sublinear_tf=True`;
- exact R37-R work retrieval: all canonical work profiles + target queries only, `max_features=120000`, cosine;
- top-k=4;
- R38-R donor episode/sequence selection is a separate local TF-IDF/cosine stage inside already-selected donor works;
- confidence gate: HIGH >= 0.13 / MEDIUM >= 0.10 and <0.13 / LOW <0.10 fallback.

## Frozen implementation correction
The controlled recovery implementation MUST therefore use:
`TfidfVectorizer(analyzer="char_wb", ngram_range=(2,5), min_df=1, sublinear_tf=True, max_features=120000, norm="l2")`
for work-level retrieval, with cosine similarity.

For the six development cases, the work-level vectorizer MUST be fit once over:
`all reconstructed DB59 work profiles + all six frozen development query texts`
so the IDF space is common across cases and no episode/sequence document enters that work-level IDF space.

After top-4 work selection, donor sequence selection MUST be a separate local TF-IDF/cosine stage within the already-selected work(s); episode/sequence documents MUST NOT contaminate the work-level IDF space.

The fit margin remains diagnostic only under the current RFV2 controlled-recovery authority.

No result has been observed before this addendum. Any subsequent FAIL/HOLD is preserved without changing these settings.

Status token:
`RFV2_R37R_HISTORICAL_VECTORIZER_CONTROLS_RECOVERED_AND_FROZEN_PRERESULT`
