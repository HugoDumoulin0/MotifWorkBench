# T. Premat, H. Dumoulin and S. Diwersy
# 2025-04-16

# Due to limitations in Python causing too many '-inf' and 'inf' values for specificity,
# we use R to compute these values. This is what this script does.

# Packages
  # This allows auto installing AND loading packages listed below
  ipak <- function(pkg){
    new.pkg <- pkg[!(pkg %in% installed.packages()[, "Package"])]
    if (length(new.pkg))
      install.packages(new.pkg, dependencies = TRUE)
    sapply(pkg, require, character.only = TRUE)
  }

packages <- c('dplyr',
	'textometry',
	'data.table',
  'tidyr')
ipak(packages)

# Variables
# default_folder <- "./Patterns_results/Specifs_noZero"




  # Inherit minsup_percent and execution_time from python
  args <- commandArgs(trailingOnly=TRUE)
  minsup_percent <- as.numeric(args[1])
  execution_time <- paste(args[2])
  default_folder <- paste(args[3]) #proposition pour organiser l'espace de travail
  print(default_folder)
  path_in <- paste(args[4])

  df <- read.delim(path_in, sep="\t")

  output_name_vertical <- paste0(default_folder, "/", minsup_percent, "_specif_", execution_time, ".tsv")
  output_name_pivot <- paste0(default_folder, "/", minsup_percent, "_specif_pivot_", execution_time, ".tsv")
  output_name_pivot_minimal <- paste0(default_folder, "/", minsup_percent, "_synthesis_", execution_time, ".tsv")

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

df2 <- df %>%
  rename(unit = motif) %>%
  rename(part = fichier) %>%
  rename(F = f) %>%
  rename(f = k) %>%
  relocate(unit, .before=part)

df_spec <- calc_specif(df2)

df_wide <- df_spec %>%
  rename(indice = am.specif.hyper) %>%
  select(!E11) %>%
  pivot_wider(
    id_cols = unit,
    names_from = part,
    values_from = c(f, F, t, T, mode.val, indice),
    names_glue = "{part}_{.value}"
  ) %>%
  # Reorder columns to group by part prefix
  select(
    unit,
    # All other columns grouped by part prefix
    order(colnames(.)[-1])
  )

# Get the column names (excluding unit)
col_order <- df_wide %>%
  select(-unit) %>%
  colnames()

# Extract prefix
prefixes <- gsub("_(.*)", "", col_order)

# Group by prefix and preserve order
ordered_cols <- col_order[order(prefixes)]

# Final dataframe with grouped columns
df_wide <- df_wide %>%
  select(unit, all_of(ordered_cols))

df_minimal <- df_spec %>%
  select(unit, part, f, am.specif.hyper) %>%
  rename(indice = am.specif.hyper)

df_pivot_minimal <- df_minimal %>%
  pivot_wider(
    id_cols = unit,
    names_from = part,
    values_from = c(indice)
  ) %>%
  rowwise() %>%
  mutate(std_dev = sd(c_across(-1))) %>%
  ungroup() %>%
  arrange(desc(std_dev))

# Save it!
write.table(df_spec,
            file = output_name_vertical,
            sep = "\t",
            row.names = FALSE,
            quote = FALSE)
write.table(df_wide,
            file = output_name_pivot,
            sep = "\t",
            row.names = FALSE,
            quote = FALSE)
write.table(df_pivot_minimal,
            file = output_name_pivot_minimal,
            sep = "\t",
            row.names = FALSE,
            quote = FALSE)