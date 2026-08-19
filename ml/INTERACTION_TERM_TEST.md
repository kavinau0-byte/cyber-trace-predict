# Chain Confidence Interaction Term — Test Summary

## What Was Done

Verified that `ml/location_predictor.py` already implements the interaction formula for `chain_confidence` (applied in a prior session), and ran before/after tests to confirm it actually changes ATM rankings.

## The Two Formulas Compared

| Formula | Expression |
|---|---|
| **Additive (old, broken)** | `0.40 * distance + 0.35 * hotspot + 0.25 * chain_confidence` |
| **Interaction (current code)** | `distance * (1 - conf*0.5) + hotspot * (0.5 + conf*0.5)` |

## Key Insight

In the additive formula, `chain_confidence` is constant across all ATMs for a given complaint — it shifts every score by the same amount and never changes relative ranking. The interaction formula instead uses `chain_confidence` to **reweight** the two components, which can change rankings when ATMs have divergent distance vs. hotspot scores.

## Test Setup

- **Input:** Same complaint (victim location, ATMs, hotspots) held constant
- **High confidence:** Real mule chain from the complaint (conf ≈ 0.86–1.00)
- **Low confidence:** Fake mule chain of unknown IDs (conf ≈ 0.37–0.39)
- **Checked:** Whether top-3 ATM ranking changes between the two cases

## Results (10 complaints tested)

| Complaint | High conf | Low conf | Old formula changed? | Interaction formula changed? |
|---|---|---|---|---|
| CMP00001 | 0.9976 | 0.3774 | NO | NO |
| CMP00002 | 0.9997 | 0.3861 | NO | **YES** |
| CMP00003 | 0.8680 | 0.3724 | NO | NO |
| CMP00004 | 0.7924 | 0.3762 | NO | NO |
| CMP00005 | 0.9916 | 0.3754 | NO | NO |
| CMP00006 | 0.9874 | 0.3741 | NO | **YES** |
| CMP00007 | 0.8622 | 0.3655 | NO | NO |
| CMP00008 | 0.8857 | 0.3763 | NO | NO |
| CMP00009 | 0.9393 | 0.3685 | NO | NO |
| CMP00010 | 0.9972 | 0.3761 | NO | **YES** |

**Additive formula:** 0/10 ranking changes — confirmed broken.
**Interaction formula:** 3/10 ranking changes — confirmed working.

## Detailed Example: CMP00002

**High confidence (0.9997)** — weights: w_dist=0.501, w_hotspot=0.999
```
#1  [2416036200]  s_dist=0.989  s_hot=0.991  raw=1.4857
#2  [2416036211]  s_dist=0.989  s_hot=0.990  raw=1.4850
#3  [3255140843]  s_dist=0.999  s_hot=0.983  raw=1.4826
```

**Low confidence (0.386)** — weights: w_dist=0.807, w_hotspot=0.693
```
#1  [3255140843]  s_dist=0.999  s_hot=0.983  raw=1.4839  ← promoted
#2  [2416036200]  s_dist=0.989  s_hot=0.991  raw=1.4808  ← demoted
#3  [2416036211]  s_dist=0.989  s_hot=0.990  raw=1.4802  ← demoted
```

ATM 3255140843 has the best distance score but slightly worse hotspot. Low confidence shifts weight toward distance, promoting it. High confidence shifts toward hotspot, demoting it.

## Why Most Complaints Don't Change

Top-ranked ATMs typically score high on **both** distance and hotspot (e.g. 0.999 + 1.000). Since the two signals are correlated — ATMs near the victim also tend to be in hotspot zones — reweighting rarely flips them. The formula only changes rankings when ATMs have divergent component scores.

## Files Modified

None. The interaction formula was already present in `ml/location_predictor.py` from a prior session. Tests were run as standalone scripts in `/tmp/`.
