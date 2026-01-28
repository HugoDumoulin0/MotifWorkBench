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
execution_time <- paste(args[2])
default_folder <- paste(args[3])
print(default_folder)
path_in <- paste(args[4])
seuil <-paste(args[5])
pos <- paste(args[6])

output_name_vertical <- paste0(default_folder, "/","specif_", seuil, pos, execution_time, ".tsv")

#----------------------------------------------
# Rewriting of textometry functions
#----------------------------------------------
custom_probabilities_specif <- function (df) {
    rowMargin <- rowSums(df) #compute F (sum freq. per motif)
    t <- df["others", ]
    t <- as.numeric(df["others", ]) # Note : replace colMargin by "others" (t comes directly from df)
    T <- sum(df["others", ]) #Define T as the sum of words ('others' row in pseudo-lexical table).
                              #Called F in textometry implementation (but not in their other func).
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
    names_from = part, # the values that become column names (A, B)
    values_from = f  # the values to fill in the table
  )

# Reintroduce t values
## Extract first t per part and reshape to a row
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

## Bind the new row at the bottom of df_wide
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

