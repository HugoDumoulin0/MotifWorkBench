# Log: introduction of PCA

Claude (Opus 5.5 Medium) was used reasonably. I did not wanted him to do everything, so I did most of it by hand and when used it specified the narrow action I wanted it to take. I'm trying to regain coding power over Claude! Or I won't know how to do R code anymore...

## Issue
As remarkes by B. Pincemin, CA might be biased for out motives because word sequences can belong to several motives and be counted several times, inflating their weight. Using PCA instead of CA resolve the problem; CA silently deals with modulating count data given texts' size; PCA does not, so that it is not biased by the 'counted several times' issue.

## Todo
- [X] change input df to get relative counts instead of absolute observation
    - [X] done by reconstruction a raw observations table from the contingency table
        - [ ] If CA is abandonned in the future, contingency table should be avoided and a raw observations table should be passed to R
- [X] build PCA based on that
    - [X] Introduce a selector in the GUI to switch between CA and ACP
    - [X] Put individual and circle plots side by side
    - [X] Also branch clustering etc. to this selector (clustering must depend either on CA or ACP)
- [X] Rename various tabs, panels and buttons
- [ ] rename `Shiny_CA.R` in `Stats_GUI.r`or something like that
- [X] get the size of texts from enslave_perl.py (it's already computed there)
    - [X] Func `save_text_sizes`
    - [X] Saved as `Patterns_results/text_sizes.json`
    - [X] Add a sanity check T == T

## Detail log
I detail here the actions I took, so that the process can be controlled on the conceptual level.

- UI
    - Added a selector on top of `Plot settings` accordion to switch between PCA and CA
    - Added a conditional for the main card of PCA/CA panel, hosting alternatively a card for PCA and a card for CA
    - Applied the same esthetics for PCA than for CA
- SERVER
    - Added a PCA plotting section, with `PCA__plot` (the reactive that computes and stores the PCA) and `output$PCAplot` (the output object that plot the PCA)
        - PCA__plot contains either the circular plot or the biplot
    - On top of the server section, branch out between `data_CA()` and `data_PCA()`; former `data()` is now `data_CA()` (changed everywhere)
        - Do some transformations on `data_PCA()`? Not sure: the demo dataset from FactoMineR provides the same type of information than the one we use in the contingency table? It's motifs and nb. token by text. Or do I need to normalise based on size of texts? I'm not sure; the question would be: how does this motive perform in each text. So that normalizing is not needed?
    - Load `Patterns_results/text_sizes.json` and compute the size of each possible part from `metadata.csv`
    - Use two different df:
        - CA uses the same df as before (contingency table)
        - PCA uses another df, where the observation table is rebuild from the contingency table
            - and number of token is devided by size of metadata (text, genre, etc.)
        - When PCA is selected in `Analysis method` field, every tab accesses the PCA df and not the CA df
        - Skema: the `Analysis method` field sets the value of the `df` variable

## PCA details and decisions to be taken
- By default, PCA center-scales columns (text, genre etc.). This is needed to produce the circle plot.
- Using rates neutralizes the size of text problem