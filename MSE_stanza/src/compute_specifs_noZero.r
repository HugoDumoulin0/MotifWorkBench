# T. Premat and H. Dumoulin
# 2025-09-10
# Based on textometry package (R)
# https://cran.r-project.org/web/packages/textometry/index.html

# Packages
  # This allows auto-installing AND loading packages listed below.
  ipak <- function(pkg){
    new.pkg <- pkg[!(pkg %in% installed.packages()[, "Package"])]
    if (length(new.pkg))
      install.packages(new.pkg, dependencies = TRUE)
    sapply(pkg, require, character.only = TRUE)
  }

packages <- c('dplyr',
	'textometry',
	'data.table',
  'tidyr',
  'tidyverse')
ipak(packages)

#----------------------------------------------
# Inherit from Python
#----------------------------------------------
args <- commandArgs(trailingOnly=TRUE)
minsup_percent <- as.numeric(args[1])
execution_time <- paste(args[2])
default_folder <- paste(args[3]) #proposition pour organiser l'espace de travail
print(default_folder)
path_in <- paste(args[4])

output_name_vertical <- paste0(default_folder, "/", minsup_percent, "_specif_", execution_time, ".tsv")
# output_name_pivot <- paste0(default_folder, "/", minsup_percent, "_specif_pivot_", execution_time, ".tsv")
# output_name_pivot_minimal <- paste0(default_folder, "/", minsup_percent, "_synthesis_", execution_time, ".tsv")

#----------------------------------------------
# Rewriting of textometry functions
#----------------------------------------------
custom_probabilities_specif <- function (df) {
    rowMargin <- rowSums(df) #compute F (sum freq. per motif)
    t <- df["others", ]
    t <- as.numeric(df["others", ]) # Note : replace colMargin by "others" (t comes directly from df)
    T <- sum(df["others", ]) #Define T as the sum of words ('others' row in pseudo-lexical table). Called F in textometry implementation (but not in their other func).
    specif <- matrix(0, nrow = nrow(df), ncol = ncol(df))
    for (i in 1:ncol(df)) {
        specif[, i] <- specificities.probabilities.vector(df[, i],
            rowMargin, T, t[i])
    }
    colnames(specif) <- colnames(df)
    rownames(specif) <- rownames(df)
    return(specif)
}

custom_specif <- function (df) {
    spe <- custom_probabilities_specif(df)
    spelog <- matrix(0, nrow = nrow(spe), ncol = ncol(spe)) #Create matrix filled with zeros
    spelog[spe < 0] <- log10(-spe[spe < 0]) #log10 of absolute value of negative values
    spelog[spe > 0] <- abs(log10(spe[spe > 0])) #log10 of positive values
    spelog[spe == 10] <- +Inf
    spelog[spe == -10] <- -Inf
    spelog <- round(spelog, digits = 4)
    rownames(spelog) <- rownames(spe)
    colnames(spelog) <- colnames(spe)
    return(spelog)
}

#----------------------------------------------
# Load and treat data
#----------------------------------------------

df <- read.delim(path_in, sep="\t")

# Shape pseudo-lexical table (≠ lex.tab. because last row is t and not REST)
df2 <- df %>%
    rename(F = f) %>%
    rename(f = k) %>%
    rename(part = fichier)

df_wide <- df2 %>%
  select(-F) %>%   # remove the F column (F is restituted by sum of f)
  select(-T) %>%   # remove the T column (T is restituted by sum of t)
  select(-t) %>%   # remove the t column (reintroduced later, if not prevent merging lines)
  pivot_wider(
    names_from = part,   # the values that become column names (A, B)
    values_from = f  # the values to fill in the table
  )

# Reintroduce t values
## Step 1+2: extract first t per part and reshape to a row
t_row <- df2 %>%
  group_by(part) %>%      # group by part (contrastive subset of corpus)
  summarise(t_first = first(t),         # keep only the first value of t
            .groups = "drop") %>%
  pivot_wider(
    names_from = part,      # make part values the column names
    values_from = t_first   # fill with the extracted t_first
  ) %>%
  mutate(motif = "others") %>%    # add a label "t" so we know this is special
  select(motif, everything())     # reorder: col2 first, then A, B, …

## Step 3: bind the new row at the bottom of df_wide
df_final <- bind_rows(df_wide, t_row) %>%
  column_to_rownames("motif")  # make 'motif' the row names col.

specif_table <- custom_specif(df_final)

# Save it!
write.table(specif_table,
            file = output_name_vertical,
            sep = "\t",
            row.names = TRUE,
            col.names = NA,
            quote = FALSE)

#---------------------------------------
# Old Script/archived code
#---------------------------------------
# Defined but not ran
# Functions
calc_specif_hyper <- function(x, F, t, T){
  
  f=0:F
  
  mode.val=((F+1)*(t+1))/(T+2)
  
  pf=dhyper(f, F, T-F, t)
  pfsum=specificities.probabilities.vector(f, rep(F, F+1), rep(T, F+1), t)
  
  px <- pf[x+1]
  
  mode.int <- as.integer(mode.val)
  #~ def pfsum = r.eval('res$pfsum'+"[$f+1]").asDouble()
  is.positive.spec = ifelse(x > abs(mode.int), TRUE, FALSE) # True if S+
  pfsumx <- pfsum[x+1]
  proba = abs(pfsumx)  # Compute actual probability (should be a positive number, even for negative specificities, where pfsum = -probability)
  specif <- ifelse(is.positive.spec, abs(log10(proba)), -1*abs(log10(proba)))
  specif <- ifelse(is.infinite(specif), sign(specif)*1000, specif)
  
  specif
}

calc_KLD <- function(f, F, t, T){
  O11 = f
  O12 = (F - f)
  O21 = (t - f)
  O22 = (T - F - t + f)
  E11 = ((F * t) / T)
  R1 = F
  R2 = (T - F)
  C1 = t
  C2 = (T - t)
  p.O11 = (O11 / R1)
  p.O12 = (O12 / R1)
  p.C1 = (C1 / T)
  p.C2 = (C2 / T)
  
  term.prob.O11 = ifelse(p.O11 > 0, p.O11 * log2((p.O11 / p.C1)), 0)
  term.prob.O12 = ifelse(p.O12 > 0, p.O12 * log2((p.O12 / p.C2)), 0)
  KLD.score = term.prob.O11 + term.prob.O12
  
  KLD.score
}


calc_specif <- function(df, scores=c("am.specif.hyper"))
{
  # Calcul de scores d'association
  DT <- data.table(df)
  DT[, `:=`(f=as.numeric(f), F=as.numeric(F), t=as.numeric(t), T=as.numeric(T))]
  DT[, `:=`(E11=((F*t)/T), mode.val=(((F+1)*(t+1))/(T+2)),
    am.specif.hyper=calc_specif_hyper(f, F, t, T)),
    by=list(unit,part)]
  if("am.KLD" %in% scores)
  {
    DT[, `:=`(am.KLD=calc_KLD(f, F, t, T)), by=list(unit,part)]
    DT[, `:=`(am.KLD=round(am.KLD,3)), by=list(unit,part)]
  }
  
  setkey(DT, unit,part)
  DT[, `:=`(f=as.integer(f), F=as.integer(F), t=as.integer(t), T=as.integer(T))]
  DT[, `:=`(E11=round(E11,3), mode.val=round(mode.val,3),
    am.specif.hyper=round(am.specif.hyper,3)),
    by=list(unit,part)]
  
  df.res <- as.data.frame(DT)
  
  df.res
}

#=======================================
# Here starts the fun
#=======================================

# Needed to run old function:
# df2 <- df %>%
#   rename(unit = motif) %>%
#   rename(part = fichier) %>%
#   rename(F = f) %>%
#   rename(f = k) %>%
#   relocate(unit, .before=part)

# df_spec <- calc_specif(df2)


# df_wide <- df_spec %>%
#   rename(indice = am.specif.hyper) %>%
#   select(!E11) %>%
#   pivot_wider(
#     id_cols = unit,
#     names_from = part,
#     values_from = c(f, F, t, T, mode.val, indice),
#     names_glue = "{part}_{.value}"
#   ) %>%
#   # Reorder columns to group by part prefix
#   select(
#     unit,
#     # All other columns grouped by part prefix
#     order(colnames(.)[-1])
#   )

# # Get the column names (excluding unit)
# col_order <- df_wide %>%
#   select(-unit) %>%
#   colnames()

# # Extract prefix
# prefixes <- gsub("_(.*)", "", col_order)

# # Group by prefix and preserve order
# ordered_cols <- col_order[order(prefixes)]

# # Final dataframe with grouped columns
# df_wide <- df_wide %>%
#   select(unit, all_of(ordered_cols))

# df_minimal <- df_spec %>%
#   select(unit, part, f, am.specif.hyper) %>%
#   rename(indice = am.specif.hyper)

# df_pivot_minimal <- df_minimal %>%
#   pivot_wider(
#     id_cols = unit,
#     names_from = part,
#     values_from = c(indice)
#   ) %>%
#   rowwise() %>%
#   mutate(std_dev = sd(c_across(-1))) %>%
#   ungroup() %>%
#   arrange(desc(std_dev))

# # Save it!
# write.table(df_spec,
#             file = output_name_vertical,
#             sep = "\t",
#             row.names = FALSE,
#             quote = FALSE)
# write.table(df_wide,
#             file = output_name_pivot,
#             sep = "\t",
#             row.names = FALSE,
#             quote = FALSE)
# write.table(df_pivot_minimal,
#             file = output_name_pivot_minimal,
#             sep = "\t",
#             row.names = FALSE,
#             quote = FALSE)