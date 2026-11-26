
# Timothée Premat and Hugo Dumoulin 
# 24/05/2026
# Modifié le 11/06/2026 par @jcharlesDS
# updated by Timothée Premat on the 10/10/2026

#--------------------------------------------------------------
# Python/R interface
#--------------------------------------------------------------
args <- commandArgs(trailingOnly = TRUE)

path = args[1]

rep_name=path

#--------------------------------------------------------------
# BASIC R STUFF
#--------------------------------------------------------------

#Load/install packages, input file and set variables
ipak <- function(pkg){
options(repos = c(CRAN = "https://cloud.r-project.org"))

# Utiliser un répertoire utilisateur pour les packages R
user_lib <- Sys.getenv("R_LIBS_USER")
if (!dir.exists(user_lib)) {
    dir.create(user_lib, recursive = TRUE)
}
.libPaths(c(user_lib, .libPaths()))

new.pkg <- pkg[!(pkg %in% installed.packages()[, "Package"])]
if (length(new.pkg)) {
    cat("Installation des packages R:", paste(new.pkg, collapse=", "), "\n")
    install.packages(new.pkg, dependencies = TRUE, lib = user_lib)
}

sapply(pkg, require, character.only = TRUE)
}

# usage
packages <- c('FactoMineR',
	            'ggrepel',
	            'factoextra',
              "glue",
              "shiny",
              "DT",
              "ggplot2",
              "plotly",
              "dplyr",
              "tidyverse",
              "shinyjs",
              "viridis",
              "scales",
              "fastcluster",
              "jsonlite",
              "bslib",
              "shinyBS",
              "bsicons"
              )
ipak(packages)

# ---- Deal with file selection ---- #
args <- commandArgs(trailingOnly = TRUE)
json_input <- args[1]

resolve_analysis_path <- function(path, root) {
  if (grepl("^(/|[A-Za-z]:[/\\\\])", path)) path else file.path(root, path)
}

json_input <- normalizePath(json_input, mustWork = TRUE)
analysis_root <- if (length(args) >= 4) {
  normalizePath(args[4], mustWork = TRUE)
} else if (file.exists(file.path(dirname(json_input), "analysis_info.json"))) {
  dirname(json_input)
} else {
  last_analysis_file <- file.path(dirname(json_input), "last_analysis.json")
  if (file.exists(last_analysis_file)) {
    dirname(fromJSON(last_analysis_file)$patterns_results)
  } else {
    getwd()
  }
}

patterns_dir <- file.path(analysis_root, "Patterns_results")
context_path <- file.path(analysis_root, "shiny_context.json")
shiny_context <- if (file.exists(context_path)) fromJSON(context_path) else list()
ca_plots_dir <- file.path(patterns_dir, "CA_plots")
dir.create(ca_plots_dir, recursive = TRUE, showWarnings = FALSE)

# The mapping and every analysis resource share the explicitly selected root.
datasets <- fromJSON(json_input)
datasets <- lapply(datasets, resolve_analysis_path, root = analysis_root)

print(datasets)

is_specif_dataset <- grepl("_specifs_", names(datasets), fixed = TRUE)
normal_dataset_names <- names(datasets)[!is_specif_dataset]
specif_dataset_names <- names(datasets)[is_specif_dataset]
specif_metadata <- sub("^(.*)_specifs_.*$", "\\1", specif_dataset_names)
specif_metadata_names <- unique(specif_metadata)
normal_dataset_metadata <- vapply(datasets[normal_dataset_names], function(path) {
  normalized <- gsub("\\\\", "/", path)
  if (grepl("/Patterns_results/R/", normalized, fixed = TRUE)) {
    sub("^.*/Patterns_results/R/([^/]+)/.*$", "\\1", normalized)
  } else {
    NA_character_
  }
}, character(1))
missing_metadata <- is.na(normal_dataset_metadata)
normal_dataset_metadata[missing_metadata] <- sub("_.*", "", normal_dataset_names[missing_metadata])
metadata_name <- unique(normal_dataset_metadata)

read_analysis_metadata <- function(patterns_dir) {
  analysis_info_path <- file.path(dirname(patterns_dir), "analysis_info.json")
  snapshot <- file.path(dirname(patterns_dir), "metadata.tsv")
  metadata_path <- if (file.exists(snapshot)) {
    snapshot
  } else if (!is.null(shiny_context$metadata_path)) {
    resolve_analysis_path(shiny_context$metadata_path, dirname(patterns_dir))
  } else {
    if (!file.exists(analysis_info_path)) return(NULL)
    configured <- fromJSON(analysis_info_path)$config$path_metadata
    if (is.null(configured)) return(NULL)
    resolve_analysis_path(configured, getwd())
  }
  if (!file.exists(metadata_path)) return(NULL)

  metadata <- read.delim(
    metadata_path,
    colClasses = "character",
    check.names = FALSE
  )
  metadata[] <- lapply(metadata, stringi::stri_trans_nfc)
  metadata
}

# Build size (nb of tokens) of each value of each metadata column, summing the
# sizes of its texts, e.g. metadata_sizes$genre["news"]. Every column of the
# metadata file is covered (whatever was selected in python), id included:
# metadata_sizes$id gives the size of each text
read_metadata_sizes <- function(patterns_dir, metadata) {
  text_json <- file.path(patterns_dir, "text_sizes.json")
  # Older analyses can have CA and specificity tables without PCA sizes.
  if (!file.exists(text_json)) {
    return(list())
  }

  text_sizes <- unlist(fromJSON(text_json)$texts)
  names(text_sizes) <- stringi::stri_trans_nfc(names(text_sizes))
  text_sizes[duplicated(names(text_sizes)) | duplicated(names(text_sizes), fromLast = TRUE)] <- NA_real_
  sizes <- list(id = text_sizes)

  if (is.null(metadata)) return(sizes)
  id_col <- names(metadata)[1]
  metadata$size <- text_sizes[metadata[[id_col]]]
  invalid <- !is.finite(metadata$size) | metadata$size <= 0 |
    duplicated(metadata[[id_col]]) | duplicated(metadata[[id_col]], fromLast = TRUE)
  metadata$size[invalid] <- NA_real_
  for (col in setdiff(names(metadata), c("size", "id", id_col))) {
    sizes[[col]] <- tapply(metadata$size, metadata[[col]], sum)
  }
  sizes[[id_col]] <- text_sizes
  sizes
}
analysis_metadata <- read_analysis_metadata(patterns_dir)
metadata_sizes <- read_metadata_sizes(patterns_dir, analysis_metadata)
print("Metadata sizes:")
print(metadata_sizes)




print("Metadata name:")
print(metadata_name)

has_user_input_list <- grepl("user_input_listTrue", names(datasets))
print("Has user input list:")
print(has_user_input_list)

name_user_input <- names(datasets)[grepl("user_input_listTrue", names(datasets))]
user_input_value <- sub(".*user_input_listTrue([^_]+).*", "\\1", name_user_input)
print("User input value:")
print(user_input_value)



has_specifs <- length(specif_dataset_names) > 0
print("Has specifs:")
print(has_specifs)

name_motifs <- normal_dataset_names[grepl("motif", normal_dataset_names, ignore.case = TRUE)]
has_motifs <- name_motifs
print("Has motifs:")
print(has_motifs)

minsup <- unique(sub(".*_([^_]+)_[^_]+_[^_]+_[^_]+$", "\\1", name_motifs))
print("Minsup:")
print(minsup)

gapmin <- unique(sub(".*_[^_]+_([^_]+)_[^_]+_[^_]+$", "\\1", name_motifs))
print("Gapmin:")
print(gapmin)

gapmax <- unique(sub(".*_[^_]+_[^_]+_([^_]+)_[^_]+$", "\\1", name_motifs))
print("Gapmax:")
print(gapmax)

itemsetmin <- unique(sub(".*_[^_]+_[^_]+_[^_]+_([^_]+)$", "\\1", name_motifs))
print("Itemsetmin:")
print(itemsetmin)

pattern_representations <- unique(ifelse(

  grepl("motif", normal_dataset_names, ignore.case = TRUE),
  "motif",
  sub(".*_([^_]+)$", "\\1", normal_dataset_names)
))



#--------------------------------------------------------------
# HELPERS FOR CASCADING DROPDOWNS
#--------------------------------------------------------------

get_candidates <- function(meta=NULL, rep=NULL, minsup=NULL, gapmin=NULL, gapmax=NULL) {

  cands <- normal_dataset_names

  if (!is.null(meta))
    cands <- cands[normal_dataset_metadata[cands] == meta]
  if (!is.null(rep)) {
    if (grepl("motif", rep, ignore.case=TRUE))
      cands <- cands[grepl("motif", cands, ignore.case=TRUE)]
    else
      cands <- cands[endsWith(cands, paste0("_", rep))]
  }
  if (!is.null(minsup))
    cands <- cands[sub(".*_([^_]+)_[^_]+_[^_]+_[^_]+$", "\\1", cands) == minsup]
  if (!is.null(gapmin))
    cands <- cands[sub(".*_[^_]+_([^_]+)_[^_]+_[^_]+$", "\\1", cands) == gapmin]
  if (!is.null(gapmax))
    cands <- cands[sub(".*_[^_]+_[^_]+_([^_]+)_[^_]+$", "\\1", cands) == gapmax]
  cands
}


get_specif_candidates <- function(meta) {
  specif_dataset_names[specif_metadata == meta]
}

format_specif_choices <- function(cands) {
  setNames(cands, sub("^.*_specifs_", "", cands))
}

format_specif_table_for_display <- function(df) {
  as.data.frame(lapply(df, function(col) {
    if (is.numeric(col)) {
      out <- chartr(".", ",", as.character(col))
      out[is.infinite(col) & col > 0] <- "Inf"
      out[is.infinite(col) & col < 0] <- "-Inf"
      return(out)
    }
    col
  }), check.names = FALSE, row.names = rownames(df), stringsAsFactors = FALSE)
}

specif_datatable <- function(df) {
  numeric_columns <- unname(which(vapply(df, is.numeric, logical(1))))
  display <- format_specif_table_for_display(df)
  column_defs <- list()
  if (length(numeric_columns)) {
    # Keep the original numbers for server-side sorting. Display strings preserve
    # decimal commas and +/-Inf, which would otherwise become null in JSON.
    ordering <- df[numeric_columns]
    all_names <- make.unique(c(names(df), paste0("..specif_sort_", numeric_columns)))
    names(ordering) <- tail(all_names, length(numeric_columns))
    display <- cbind(display, ordering)
    hidden_columns <- ncol(df) + seq_along(numeric_columns)
    # DT column zero contains row names, so R's one-based positions match here.
    column_defs <- lapply(seq_along(numeric_columns), function(i) {
      list(targets = numeric_columns[i], orderData = hidden_columns[i])
    })
    column_defs[[length(column_defs) + 1L]] <- list(
      targets = hidden_columns, visible = FALSE, searchable = FALSE
    )
  }
  datatable(
    display,
    options = list(
      pageLength = 15,
      autoWidth = TRUE,
      scrollX = TRUE,
      language = list(decimal = ","),
      columnDefs = column_defs
    ),
    filter = "top",
    rownames = TRUE
  )
}


extract_reps      <- function(cands) unique(ifelse(grepl("motif", cands, ignore.case=TRUE), "motif", sub(".*_([^_]+)$", "\\1", cands)))
extract_minsup    <- function(cands) unique(sub(".*_([^_]+)_[^_]+_[^_]+_[^_]+$", "\\1", cands))
extract_gapmin    <- function(cands) unique(sub(".*_[^_]+_([^_]+)_[^_]+_[^_]+$", "\\1", cands))
extract_gapmax    <- function(cands) unique(sub(".*_[^_]+_[^_]+_([^_]+)_[^_]+$", "\\1", cands))
extract_itemsetmin <- function(cands) unique(sub(".*_[^_]+_[^_]+_[^_]+_([^_]+)$", "\\1", cands))

# Initialize each dropdown from choices compatible with its predecessors.
initial_candidates <- if (length(metadata_name)) get_candidates(meta = metadata_name[1]) else character(0)
pattern_representation <- extract_reps(initial_candidates)
initial_motifs <- initial_candidates[grepl("motif", initial_candidates, ignore.case = TRUE)]
minsup_display <- extract_minsup(initial_motifs)
gapmin_candidates <- if (length(minsup_display)) {
  get_candidates(meta = metadata_name[1], rep = "motif", minsup = minsup_display[1])
} else character(0)
gapmin_display <- extract_gapmin(gapmin_candidates)
gapmax_candidates <- if (length(gapmin_display)) {
  get_candidates(meta = metadata_name[1], rep = "motif", minsup = minsup_display[1], gapmin = gapmin_display[1])
} else character(0)
gapmax_display <- extract_gapmax(gapmax_candidates)
itemset_candidates <- if (length(gapmax_display)) {
  get_candidates(meta = metadata_name[1], rep = "motif", minsup = minsup_display[1],
                 gapmin = gapmin_display[1], gapmax = gapmax_display[1])
} else character(0)
itemsetmin_display <- extract_itemsetmin(itemset_candidates)

# Scale the rendered label sizes so contribution-based sizing keeps its proportions.
export_point_labels <- function(plot, percent) {
  if (percent == 100) return(plot)
  draw_labels <- function(self, data, ...) {
    data$size <- data$size * percent / 100
    ggplot2::ggproto_parent(ggplot2::Geom, self)$draw_layer(data, ...)
  }
  plot$layers <- lapply(plot$layers, function(layer) {
    if (!inherits(layer$geom, c("GeomTextRepel", "GeomText"))) return(layer)
    geom <- ggplot2::ggproto(NULL, layer$geom, draw_layer = draw_labels)
    ggplot2::ggproto(NULL, layer, geom = geom)
  })
  plot
}

#--------------------------------------------------------------
# SERVER
#--------------------------------------------------------------
server <- function(input, output, session){

  # ------------- Export resolution (shared by all "Save plot" buttons) -------------
  # Default sizes per tab (inches) - used when "Default" is selected, and to prefill "Custom"
  export_defaults <- function(tab = input$tabselected) {
    if (isTRUE(tab %in% c("scree", "contrib"))) c(width = 8, height = 6) else c(width = 12, height = 9)
  }
  export_unit_to_in <- function(units, dpi) {
    switch(units, `in` = 1, cm = 1 / 2.54, mm = 1 / 25.4, px = 1 / dpi)
  }
  # Returns list(width, height, units, dpi) for ggsave()/png(), or NULL (with a notification) if invalid
  export_dims <- function(default_w, default_h, default_dpi = 300) {
    if (!identical(input$export_mode, "custom")) {
      return(list(width = default_w, height = default_h, units = "in", dpi = default_dpi))
    }
    w <- input$export_width; h <- input$export_height; dpi <- input$export_dpi; units <- input$export_units
    if (!isTruthy(w) || !isTruthy(h) || w <= 0 || h <= 0) {
      showNotification("Export: width and height must be positive numbers.", type = "error"); return(NULL)
    }
    if (!isTruthy(dpi) || dpi < 72 || dpi > 1200) {
      showNotification("Export: DPI must be between 72 and 1200.", type = "error"); return(NULL)
    }
    k <- export_unit_to_in(units, dpi)
    if (w * k * dpi * h * k * dpi > 1e8) {
      showNotification("Export: image too large (over 100 megapixels). Reduce size or DPI.", type = "error"); return(NULL)
    }
    list(width = w, height = h, units = units, dpi = dpi)
  }
  # Prefill custom fields with the current tab's defaults when switching to "Custom"
  observeEvent(input$export_mode, {
    if (identical(input$export_mode, "custom")) {
      d <- export_defaults()
      k <- export_unit_to_in(input$export_units, input$export_dpi)
      updateNumericInput(session, "export_width",  value = round(d[["width"]]  / k, 2))
      updateNumericInput(session, "export_height", value = round(d[["height"]] / k, 2))
    }
  }, ignoreInit = TRUE)
  # Convert width/height when units change, so the physical size is kept
  export_prev_units <- reactiveVal("in")
  observeEvent(input$export_units, {
    old <- export_prev_units(); new <- input$export_units
    if (!identical(old, new) && isTruthy(input$export_dpi)) {
      f <- export_unit_to_in(old, input$export_dpi) / export_unit_to_in(new, input$export_dpi)
      if (isTruthy(input$export_width))  updateNumericInput(session, "export_width",  value = round(input$export_width  * f, 2))
      if (isTruthy(input$export_height)) updateNumericInput(session, "export_height", value = round(input$export_height * f, 2))
    }
    export_prev_units(new)
  }, ignoreInit = TRUE)
  output$export_px_info <- renderText({
    if (identical(input$export_mode, "custom")) {
      w <- input$export_width; h <- input$export_height; dpi <- input$export_dpi; units <- input$export_units
      req(isTruthy(w), isTruthy(h), isTruthy(dpi))
    } else {
      d <- export_defaults(); w <- d[["width"]]; h <- d[["height"]]; dpi <- 300; units <- "in"
    }
    k <- export_unit_to_in(units, dpi)
    sprintf("Output: %d \u00d7 %d px", round(w * k * dpi), round(h * k * dpi))
  })

# Deal with input selection
  input_selection <- reactive({
    df <- if (isTRUE(input$input_sel_method)) {
      req(input$dataset_select)
    } else {
      req(df_select_concatenated(), cancelOutput = FALSE)
    }
    req(df %in% normal_dataset_names)
    path <- datasets[[df]]
    if (!is.character(path) || length(path) != 1) {
      stop("Selected dataset is not a valid file path")
    }
    df
  })

  # Load selected data
  data1 <- reactive({
    path <- datasets[[req(input_selection())]]
    data <- read.csv(path, sep="\t", row.names = 1, header=T, check.names = FALSE)
  })


  data_CA <- reactive({

    data <- req(data1())
    rownames(data) <- gsub(" ", "_", rownames(data))
    data <- data[rowSums(data) != 0, ]
  })


  data_PCA <- reactive({
    data <- req(data1())
    rownames(data) <- gsub(" ", "_", rownames(data))
    # Observation table from the contingency table: texts (or metadata values)
    # become the individuals (rows), motifs the variables (columns)
    obs <- as.data.frame(t(data), check.names = FALSE)
    meta <- normal_dataset_metadata[[input_selection()]]
    sizes <- metadata_sizes[[meta]]
    shiny::validate(need(length(sizes) > 0, paste("ACP impossible : tailles indisponibles pour", meta)))
    ids <- stringi::stri_trans_nfc(rownames(obs))
    denominators <- as.numeric(sizes[ids])
    invalid <- !is.finite(denominators) | denominators <= 0 |
      duplicated(ids) | duplicated(ids, fromLast = TRUE)
    shiny::validate(need(!any(invalid), paste("ACP impossible : taille absente, invalide ou identifiant ambigu pour",
                                       paste(rownames(obs)[invalid], collapse = ", "))))
    sweep(obs, 1L, denominators, "/")
  })



  # Reactive value to hold CA result and an error message for display
  ca_res <- reactiveVal(NULL)
  ca_error <- reactiveVal(NULL)
  cluster_error_msg <- reactiveVal(NULL)


  # Selected analysis method (CA or PCA)
  analysis_method <- reactiveVal("CA")
  observeEvent(input$analysis_method, {
    analysis_method(input$analysis_method)
  })


  output$cluster_error_msg_hcpc  <- renderText({ cluster_error_msg() })
  output$cluster_error_msg_parang <- renderText({ cluster_error_msg() })

  # Compute CA automatically when preprocessing result is ready

  observeEvent(data_CA(), {
    d <- data_CA()
    d 

  })

  #Preview data
  output$data_table <- renderDT({

    df <- if (analysis_method() == "PCA") req(data_PCA()) else req(data_CA())
    datatable(
      df,

      options = list(
        pageLength = 10,
        autoWidth = TRUE,
        scrollX = TRUE
      ),
      filter = "top",    # adds per-column filters
      rownames = TRUE
    )
  })


  specif_selection <- reactive({
    req(has_specifs)
    meta <- req(input$specifs_metadata_select)
    selected <- req(input$specifs_table_select)
    req(selected %in% get_specif_candidates(meta))
    path <- datasets[[selected]]
    shiny::validate(need(
      is.character(path) && length(path) == 1L && file.exists(path),
      "Le fichier de spécificités est introuvable."
    ))
    path
  })

  specif_data <- reactive({
    path <- req(specif_selection())
    read.delim(path, row.names = 1, quote = "", check.names = FALSE)
  })

  output$specifs_table <- renderDT({
    req(has_specifs)
    specif_datatable(specif_data())
  })



  # ------------- Screeplot -------------
  # Suffix the default title with the method, without overwriting a custom title
  observeEvent(analysis_method(), {
    defaults <- c("Scree plot", "Scree plot (PCA)", "Scree plot (CA)")
    if (is.null(input$plot_title_scree) || input$plot_title_scree %in% defaults) {
      updateTextInput(session, "plot_title_scree",
        value = paste0("Scree plot (", analysis_method(), ")"))
    }
  })

  # Store the plot as a reactive
  scree_plot <- reactive({
      if (analysis_method() == "PCA"){
        res <- req(res_pca())
        valid_choices <- c("var", "ind")
      } else {
        res <- req(res_ca())
        valid_choices <- c("row", "col")
      }
    p <- fviz_screeplot(res,

      addlabels = TRUE, 
      title=input$plot_title_scree,
      xlab = input$plot_xlab_scree,
      ylab = input$plot_ylab_scree,
      ) + theme_classic()
    p
  })

  # Render the plot
  output$screePlot <- renderPlot({
    p <- req(scree_plot())
    p
  }, res = 96)

  # Download handler
  observeEvent(input$save_scree_plot, {
      #base_dir <- getwd()
      file_name <- paste("CA_plots/ScreePlot_", format(Sys.time(), "%Y-%m-%d_%H-%M-%S"), ".png", sep="")
      full_path <- file.path(patterns_dir, file_name)
      d <- req(export_dims(8, 6))
      ggsave(full_path, plot = scree_plot(), width = d$width, height = d$height, units = d$units, dpi = d$dpi)
      showNotification(paste("Plot saved to:", full_path), type = "message")
    }
  )

  # ------------- CA computation -------------
  res_ca <- reactive({

    data <- req(data_CA())                # your reactive data object

    FactoMineR::CA(data, graph = FALSE, ncp = 2)
  })

  # ------------- Prepare data for CA ploting -------------
  ca_prep <- reactive({
    res <- req(res_ca())

    # Extract coordinated for rows and columns
    rows_df <- as.data.frame(res$row$coord[, 1:2])
    cols_df <- as.data.frame(res$col$coord[, 1:2])
    rows_df$label <- rownames(rows_df)
    cols_df$label <- rownames(cols_df)
    # res$row$contrib$label <- rownames(res$row$contrib)
    # res$col$contrib$label <- rownames(res$col$contrib)

    # Subset n-rows for displaying points and labels
    if (input$contrib_threshold) {
  total_contrib_rows <- rowSums(res$row$contrib)
  top_rows <- names(sort(total_contrib_rows, decreasing = TRUE))[1:input$contrib_rows]

  total_contrib_cols <- rowSums(res$col$contrib)
  top_cols <- names(sort(total_contrib_cols, decreasing = TRUE))[1:input$contrib_vars]

  rows_df <- rows_df[rows_df$label %in% top_rows, ]
  cols_df <- cols_df[cols_df$label %in% top_cols, ]
}

    # Also include the raw CA object and contributions if other outputs need them
    list(
      ca = res,
      rows = rows_df,
      cols = cols_df,
      # flags = flags,
      eig = res$eig,
      row_contrib = res$row$contrib,
      col_contrib = res$col$contrib
    )
  })
  
  # ------------- Retrieve axis selection -------------
  observe({
    res <- req(res_ca())
    n_axes <- ncol(res$col$coord)

    updateSelectInput(
      session,
      "selected_axis",
      choices = 1:n_axes,
      selected = 1
    )
  })


  # ------------- Shared CA/PCA plot layers -------------
    # Adds the points, labels and contribution sizes chosen in Plot settings
    # to a base factor map. points_data is the list returned by ca_prep() or pca_prep().
    add_factor_layers <- function(fplot, points_data, plot_title, show_cols = TRUE) {

      cols_df <- points_data$cols
      rows_df <- points_data$rows
      rows_df$contrib_var <- rowSums(
        points_data$row_contrib[rows_df$label, 1:2, drop = FALSE]
      )

      cols_df$contrib_var <- rowSums(
        points_data$col_contrib[cols_df$label, 1:2, drop = FALSE]
      )

      contribution_title <- "Contribution (axes 1 + 2)"


      # Retrieve display properties choices

        # show_cols = FALSE drops column layers whatever the checkboxes say
        show_col_points <- show_cols && "Columns points" %in% input$show_items
        show_row_points <- "Rows points" %in% input$show_items
        show_col_labels <- show_cols && "Columns labels" %in% input$show_items

        show_row_labels <- "Rows labels" %in% input$show_items
        points_size <- "Points size" %in% input$size
        label_size <- "Label size" %in% input$size
        # points_color <- "Points color" %in% input$size
        # label_color <- "Label color" %in% input$size
          

		fplot <- fplot +
  scale_size_continuous(range = c(2, 6))									#minimal size for readability (HugoDumoulin)
      # Conditionnaly add points and/or labels
      strenght <- input$jitter_strength
      if (show_col_labels) {                                                      # If labels of rows are showed   
        if (label_size) {                                                    # If label size == contrib
          fplot <- fplot +
          geom_text_repel(data = cols_df,
                aes(x = `Dim 1`, y = `Dim 2`, label = label,
                size = contrib_var),
                color = "red", vjust = -0.5,
                force=strenght) #+
                # guides(size="none")
        } else {                                                               # If not, label size is fixed
          fplot <- fplot +
          geom_text_repel(data = cols_df,
                aes(x = `Dim 1`, y = `Dim 2`, label = label),
                color = "red", vjust = -0.5,
                force=strenght)
        }
      }
      if (show_row_labels) {                                                      # If labels of rows are showed
        if (label_size) {                                                    # If label size == contrib and jitter                                                      # If label size == contrib
          fplot <- fplot +
          geom_text_repel(data = rows_df,
                aes(x = `Dim 1`, y = `Dim 2`, label = gsub("dep_|lemma_|pos_|feats_", "", label),
                size = contrib_var),
                color = "blue", vjust = -0.5,
                force=strenght) #+
                # guides(size="none")
        } else {
                fplot <- fplot +
          geom_text_repel(data = rows_df,
                aes(x = `Dim 1`, y = `Dim 2`, label = gsub("dep_|lemma_|pos_|feats_", "", label)),
                color = "blue", vjust = -0.5,
                force=strenght)
        }
      }
      if (show_col_points) {                                                      # If points of columns are showed
        if (points_size) {                                                          # If points size == contrib
          fplot <- fplot +
          geom_point(data = cols_df,
                aes(x = `Dim 1`, y = `Dim 2`, size = contrib_var), shape = 17,
                color = "red") +
                labs(size = contribution_title)
        } else {                                                                    # If not, points size is fixed
          fplot <- fplot +
          geom_point(data = cols_df,
                aes(x = `Dim 1`, y = `Dim 2`), shape = 17,
                color = "red")
        }
      }
      if (show_row_points) {                                                        # If points of rows are showed
        if (points_size) {                                                            # If points size == contrib
          fplot <- fplot +
          geom_point(data = rows_df,
                aes(x = `Dim 1`, y = `Dim 2`, size = contrib_var), shape = 19,
                color = "blue")
        } else {                                                                     # If not, points size is fixed
          fplot <- fplot +
          geom_point(data = rows_df,
                aes(x = `Dim 1`, y = `Dim 2`), shape = 19,
                color = "blue")
        }
      }

      # Conditional for point size legend but no label size legend
      if (points_size & !label_size) {
        fplot <- fplot + guides(size = guide_legend(title = contribution_title))
      } else if (!points_size) {
        fplot <- fplot + guides(size = "none")
      } else if (points_size & label_size) {
        fplot <- fplot + guides(size = guide_legend(
          title = contribution_title,
          override.aes = list(label = "")))
      # } else if (points_size & input$deactivate_jitter & !label_size) {
      #   fplot <- fplot + guides(size = guide_legend(
      #     title = contribution_title,
      #     override.aes = list(label = "")))
      } else {
        fplot <- fplot
      }

      fplot <- fplot +
        labs(title = plot_title)

      fplot
    }

  # ------------- PCA computation -------------
  res_pca <- reactive({
    data <- req(data_PCA())
    FactoMineR::PCA(data, graph = FALSE, ncp = 2, scale.unit=TRUE)
  })

  # Each active point (text or aggregate) must belong to exactly one level.
  supplementary_groups <- reactive({
    req(isTRUE(input$show_supplementary))
    meta <- normal_dataset_metadata[[req(input_selection())]]
    id_col <- names(analysis_metadata)[1]
    key <- if (meta == "id") id_col else meta
    if (is.null(analysis_metadata) || !key %in% names(analysis_metadata)) return(list())

    ids <- stringi::stri_trans_nfc(rownames(req(data_PCA())))
    index <- match(analysis_metadata[[key]], ids)
    active <- !is.na(index)
    candidates <- setdiff(names(analysis_metadata), c(key, id_col, "id"))
    groups <- list()
    for (name in candidates) {
      pairs <- unique(data.frame(index = index[active], level = analysis_metadata[[name]][active]))
      if (anyDuplicated(pairs$index)) next
      values <- pairs$level[match(seq_along(ids), pairs$index)]
      if (anyNA(values) || any(!nzchar(trimws(values)))) next
      group <- factor(values)
      if (nlevels(group) > 1L && nlevels(group) < length(ids)) {
        groups[[name]] <- group
      }
    }
    groups
  })

  output$supplementary_selector <- renderUI({
    choices <- names(supplementary_groups())
    if (!length(choices)) return(helpText("No metadata can group these active individuals."))
    selected <- isolate(input$supplementary_variable)
    selectInput("supplementary_variable", "Supplementary metadata", choices,
                selected = if (length(selected) && selected %in% choices) selected else choices[1])
  })

  # Keep the two-axis PCA used by the maps and HCPC. Retrieve the remaining
  # scores only when a supplementary variable is requested, once per dataset.
  all_axis_scores <- reactive({
    scores <- res_pca()$ind$coord
    data <- data_PCA()
    n_axes <- min(nrow(data) - 1L, ncol(data))
    if (n_axes > ncol(scores)) {
      full <- FactoMineR::PCA(data, graph = FALSE, ncp = n_axes)$ind$coord
      full[, seq_len(ncol(scores))] <- scores
      return(full)
    }
    scores
  })

  supplementary_stats <- reactive({
    if (!isTRUE(input$show_supplementary) || is.null(input$supplementary_variable)) return(NULL)
    group <- supplementary_groups()[[input$supplementary_variable]]
    if (is.null(group)) return(NULL)
    scores <- all_axis_scores()
    counts <- as.numeric(table(group))
    centers <- rowsum(scores, group) / counts
    means <- colMeans(scores)
    between <- colSums(counts * sweep(centers, 2L, means)^2)
    total <- colSums(sweep(scores, 2L, means)^2)
    # Numerically null axes carry no inertia and have no defined eta squared.
    valid <- sqrt(total) > max(sqrt(total)) * max(dim(data_PCA())) * .Machine$double.eps
    eta2 <- rep(NA_real_, ncol(scores))
    eta2[valid] <- pmin(1, between[valid] / total[valid])
    list(centers = data.frame(x = centers[, 1], y = centers[, 2], level = rownames(centers)),
         eta2 = eta2)
  })

  output$supplementary_eta <- renderDT({
    stats <- req(supplementary_stats())
    table <- data.frame(Axis = seq_along(stats$eta2), `η²` = stats$eta2, check.names = FALSE)
    caption <- paste("η² by PCA axis —", input$supplementary_variable)
    if (anyNA(stats$eta2)) caption <- paste0(caption, ". Blank values indicate axes with zero inertia.")
    DT::formatRound(DT::datatable(table, rownames = FALSE, caption = caption,
      options = list(dom = "tp", pageLength = 10)), "η²", digits = 4)
  })

  output$has_supplementary_eta <- renderText({
    if (isTRUE(input$show_supplementary) &&
        isTRUE(input$supplementary_variable %in% names(supplementary_groups()))) "yes" else "no"
  })
  outputOptions(output, "has_supplementary_eta", suspendWhenHidden = FALSE)

  # ------------- Prepare data for PCA ploting -------------
  # Rows are the PCA individuals, columns the PCA variables, so the same
  # Rows/Columns settings apply as for CA
  pca_prep <- reactive({
    res <- req(res_pca())

    ind_coord <- res$ind$coord[, 1:2]
    var_coord <- res$var$coord[, 1:2]
    # Variable coordinates are correlations (within [-1, 1]): stretch them
    # onto the individuals' scale so both fit on one biplot (as fviz_pca_biplot does)
    r <- 0.7 * min(diff(range(ind_coord[, 1])) / diff(range(var_coord[, 1])),
                   diff(range(ind_coord[, 2])) / diff(range(var_coord[, 2])))
    var_coord <- var_coord * r

    # FactoMineR::PCA names axes "Dim.1", CA names them "Dim 1": align on CA
    to_ca_names <- function(m) { colnames(m) <- sub("Dim.", "Dim ", colnames(m), fixed = TRUE); m }
    rows_df <- as.data.frame(to_ca_names(ind_coord))
    cols_df <- as.data.frame(to_ca_names(var_coord))
    rows_df$label <- rownames(rows_df)
    cols_df$label <- rownames(cols_df)
    row_contrib <- to_ca_names(res$ind$contrib)
    col_contrib <- to_ca_names(res$var$contrib)

    # Subset n-rows for displaying points and labels
    if (input$contrib_threshold) {
      top_rows <- names(sort(rowSums(row_contrib), decreasing = TRUE))[1:input$contrib_rows]
      top_cols <- names(sort(rowSums(col_contrib), decreasing = TRUE))[1:input$contrib_vars]
      rows_df <- rows_df[rows_df$label %in% top_rows, ]
      cols_df <- cols_df[cols_df$label %in% top_cols, ]
    }

    list(
      pca = res,
      rows = rows_df,
      cols = cols_df,
      eig = res$eig,
      row_contrib = row_contrib,
      col_contrib = col_contrib
    )
  })

  # ------------- PCA ploting ------------
    # Store the plot as a reactive
    PCA__plot <- reactive({
      res <- req(res_pca())
      points_data <- req(pca_prep())

      pca_plot <- factoextra::fviz_pca_ind(res, geom.ind = "none", geom.var = "none",
                                              ggtheme = ggplot2::theme_minimal())

      # Rows only: columns (variables) are drawn in the circle plot
      pca_plot <- add_factor_layers(pca_plot, points_data, input$plot_title_PCA, show_cols = FALSE)
      stats <- supplementary_stats()
      if (!is.null(stats)) {
        pca_plot <- pca_plot +
          geom_point(data = stats$centers, aes(x, y), inherit.aes = FALSE,
                     shape = 8, colour = "#762A83", size = 4, stroke = 1.2) +
          ggrepel::geom_text_repel(data = stats$centers, aes(x, y, label = level),
                     inherit.aes = FALSE, colour = "#762A83", force = input$jitter_strength)
      }
      pca_plot +
        ggplot2::theme(legend.position = "bottom")
    })

    # Circle plot
        PCA_circle_plot <- reactive({
      res <- req(res_pca())

      # Coordonnées de corrélation du cercle des variables
      vars <- data.frame(
        x = res$var$coord[, 1],
        y = res$var$coord[, 2],
        label = rownames(res$var$coord),
        contrib_var = rowSums(
          res$var$contrib[, 1:2, drop = FALSE]
        )
      )

      vars$display_label <- gsub(
        "dep_|lemma_|pos_|feats_", "", vars$label
      )

      # Filtrer les variables les plus contributives
      if (isTRUE(input$contrib_threshold)) {
        n <- req(input$contrib_vars)
        keep <- head(order(vars$contrib_var, decreasing = TRUE), n)
        vars <- vars[keep, , drop = FALSE]
      }

      show_points <- "Columns points" %in% input$show_items
      show_labels <- "Columns labels" %in% input$show_items
      points_size <- "Points size" %in% input$size
      label_size <- "Label size" %in% input$size

      # Fond : cercle et axes
      p <- factoextra::fviz_pca_var(
        res,
        geom.var = "none",
        ggtheme = ggplot2::theme_minimal()
      )

      # Flèches et points aux extrémités
      if (show_points) {
        p <- p + geom_segment(
          data = vars,
          aes(x = 0, y = 0, xend = x, yend = y),
          arrow = grid::arrow(length = grid::unit(0.2, "cm")),
          color = "red",
          alpha = 0.6,
          inherit.aes = FALSE
        )

        point_mapping <- aes(x = x, y = y)
        if (points_size) {
          point_mapping$size <- aes(size = contrib_var)$size
        }

        p <- p + geom_point(
          data = vars,
          mapping = point_mapping,
          color = "red",
          shape = 17,
          inherit.aes = FALSE
        )
      }

      # Étiquettes, avec taille et répulsion réglables
      if (show_labels) {
        label_mapping <- aes(
          x = x, y = y, label = display_label
        )
        if (label_size) {
          label_mapping$size <- aes(size = contrib_var)$size
        }

        p <- p + ggrepel::geom_text_repel(
          data = vars,
          mapping = label_mapping,
          color = "red",
          force = input$jitter_strength,
          box.padding = 0.25 + 1.5 * input$jitter_strength,
          seed = 42,
          show.legend = FALSE,
          inherit.aes = FALSE
        )
      }

      p <- p + scale_size_continuous(
        name = "Contribution (axes 1 + 2)",
        range = c(2, 6)
      )

      if (!show_points || !points_size) {
        p <- p + guides(size = "none")
      }

      p + labs(title = input$plot_title_PCA_circle) +
        ggplot2::theme(legend.position = "bottom")
    })
    
    # Display it
    output$PCAplot <- renderPlot({
      p <- req(PCA__plot())
      p
    }, res = 96, execOnResize = TRUE)
    output$PCAcircleplot <- renderPlot({
      p <- req(PCA_circle_plot())
      p
    }, res = 96, execOnResize = TRUE)

  # ------------- CA ploting -------------
    # Store the plot as a reactive
      CA__plot <- reactive({
      res <- req(res_ca())
      points_data <- req(ca_prep())

      ca_plot <- factoextra::fviz_ca_biplot(
        res,
        geom = "none",
        ggtheme = ggplot2::theme_minimal()
      )

      add_factor_layers(ca_plot, points_data, input$plot_title_CA)
    })
    
    
    # Display it
    output$CAplot <- renderPlot({
      p <- req(CA__plot())
      p
    }, res = 96)


    # Download handler (saves the plot(s) of the selected analysis method)
    # PCA: individuals and circle plots are saved as two separate files
    observeEvent(input$save_CA_plot, {
        method <- analysis_method()
        plots <- if (method == "PCA") {
          list(PCA_individuals = PCA__plot(), PCA_circle = PCA_circle_plot())
        } else {
          list(CA = CA__plot())
        }
        #base_dir <- getwd()
        timestamp <- format(Sys.time(), "%Y-%m-%d_%H-%M-%S")
        d <- req(export_dims(12, 9))
        for (name in names(plots)) {
          file_name <- paste("CA_plots/", name, "_", timestamp, ".png", sep="")
          full_path <- file.path(patterns_dir, file_name)
          export_plot <- export_point_labels(plots[[name]], if (identical(input$export_mode, "custom")) input$factor_export_label_pct else 100)
          ggsave(full_path, plot = export_plot, width = d$width, height = d$height, units = d$units, dpi = d$dpi)
          showNotification(paste("Plot saved to:", full_path), type = "message")
        }

      }
    )

  # ------------- Contrib plotting -------------

  # Dimension choices depend on the method: row/col for CA, var/ind for PCA
  observeEvent(analysis_method(), {
    choices <- if (analysis_method() == "PCA") c("var", "ind") else c("row", "col")
    updateSelectInput(session, "contrib_choice", choices = choices, selected = choices[1])

    # Suffix the default title with the method, without overwriting a custom title
    base_title <- "Contribution of XX to Dim-XX"
    defaults <- c(base_title, paste0(base_title, c(" (PCA)", " (CA)")))
    if (is.null(input$plot_title_contrib) || input$plot_title_contrib %in% defaults) {
      updateTextInput(session, "plot_title_contrib",
        value = paste0(base_title, " (", analysis_method(), ")"))
    }
  })

  contrib_plot <- reactive({
    if (analysis_method() == "PCA"){
        res <- req(res_pca())
        valid_choices <- c("var", "ind")
      } else {
        res <- req(res_ca())
        valid_choices <- c("row", "col")
      }
    # Get user inputs
      user_choice <- req(input$contrib_choice)  # e.g. "row"/"col" (CA) or "var"/"ind" (PCA)
      # Wait for the selector to update after a method switch
      req(user_choice %in% valid_choices)

      user_axes   <- req(input$contrib_axes)    # e.g. 1 or 2
    if (input$contrib_custom_title) {
      plot_obj <- fviz_contrib(res,
        choice = user_choice,
        axes = user_axes,
        title = input$plot_title_contrib)
      plot_obj
    } else {
      plot_obj <- fviz_contrib(res,
        choice = user_choice,
        axes = user_axes)

      # Suffix the default factoextra title with the method
      plot_obj <- plot_obj +
        ggtitle(paste0(plot_obj$labels$title, " (", analysis_method(), ")"))
      plot_obj
    }

    if (input$scree_hide_labels) {
      plot_obj <- plot_obj +
        theme(axis.text.x = element_blank(),
              axis.ticks.x = element_blank())
    }

    plot_obj <- plot_obj +
    ylab(input$plot_ylab_contrib)
  })

  output$contribPlot <- renderPlot({
      p <- req(contrib_plot())
      p
    }, res = 96)

  # Download handler
  observeEvent(input$save_contrib_plot, {
      #base_dir <- getwd()
      file_name <- paste("CA_plots/Contrib_", format(Sys.time(), "%Y-%m-%d_%H-%M-%S"), ".png", sep="")
      full_path <- file.path(patterns_dir, file_name)
      d <- req(export_dims(8, 6))
      ggsave(full_path, plot = contrib_plot(), width = d$width, height = d$height, units = d$units, dpi = d$dpi)
      showNotification(paste("Plot saved to:", full_path), type = "message")
    }
  )



  # ------------- Clustering -------------
  # Note : because HCPC is base R (not ggplot), I can't create it in a reactive and then renderPlot and save it through observeEvent
  # Simplest fix is to copy-paste the code in two functions

  # HCPC's cluster.CA only applies to CA: PCA always clusters rows (individuals)
  cluster_row_or_col <- reactive({
    if (analysis_method() == "PCA") "rows" else req(input$cluster_row_or_col)
  })

  output$clusters_plot <- renderPlot({
    req(input$nb_clusters,

      !is.null(input$type_of_plot),
      !is.null(input$ind_name),
      !is.null(input$bool_consol_tree),
      !is.null(input$bool_draw_tree)
    )

      # Select PCA of CA
      res <- if (analysis_method() == "PCA") req(res_pca()) else req(res_ca())
    nb_clusters <- ifelse(input$enable_num_clusters, input$nb_clusters, -1)
    type <- input$type_of_plot
    ind_name <- if (isTRUE(input$ind_name)) "FALSE" else "TRUE"
    draw_tree <- if (isTRUE(input$bool_draw_tree)) "TRUE" else "FALSE"

    tryCatch({

      hclust <- FactoMineR::HCPC(res,
        nb.clust = nb_clusters,
        consol = input$bool_consol_tree,
        graph = FALSE,
        cluster.CA = cluster_row_or_col())


      nb_clusters_after_HCPC <- length(unique(hclust$data.clust$clust))
      palette(scales::hue_pal()(nb_clusters_after_HCPC))

      plot.HCPC(hclust,
        choice = type,
        ind.names = ind_name,
        draw.tree = draw_tree)
    }, error = function(e) {
      if (grepl("arguments must have same length", conditionMessage(e), fixed = TRUE))
        cluster_error_msg("Clustering failed: the number of items is incompatible with the requested number of clusters. Try changing the number of clusters or the row/column setting.")
      stop(e)
    })
  }, res = 96)

  #Download handler
  observeEvent(input$download_clusters, {
    req(input$nb_clusters, !is.null(input$type_of_plot), !is.null(input$ind_name))
    res <- if (analysis_method() == "PCA") req(res_pca()) else req(res_ca())
    nb_clusters <- ifelse(input$enable_num_clusters, input$nb_clusters, -1)
    type <- input$type_of_plot
    ind_name <- if (isTRUE(input$ind_name)) "FALSE" else "TRUE"
    hclust <- HCPC(res,
      nb.clust = nb_clusters,
      consol = input$bool_consol_tree,
      graph = FALSE,
      cluster.CA = cluster_row_or_col())


    #base_dir <- getwd()
    full_dir <- ca_plots_dir
    if (!dir.exists(full_dir)) dir.create(full_dir, recursive = TRUE)
    full_path <- file.path(full_dir, paste0("Clusters_", format(Sys.time(), "%Y-%m-%d_%H-%M-%S"), ".png"))

    d <- req(export_dims(12, 9))
    png(full_path, width = d$width, height = d$height, units = d$units, res = d$dpi)
    plot.HCPC(hclust, choice = type, ind.names = ind_name)
    dev.off()

    showNotification(paste("Plot saved to:", full_path), type = "message")
  })

  # Disable cluster numbering and activate on checkbox
  disable("nb_clusters")
  observeEvent(input$enable_num_clusters, {
    if (input$enable_num_clusters) {
      enable("nb_clusters")
    } else {
      disable("nb_clusters")
    }
  })

  # Diable scaled jittering if no scaling labels on CA
  # disable("deactivate_jitter")
  # observeEvent(input$size, {
  #   # label_size <- "Label size" %in% input$size
  #   if ("Label size" %in% input$size) {
  #     enable("deactivate_jitter")
  #   } else {
  #     disable("deactivate_jitter")
  #     updateCheckboxInput(session, "deactivate_jitter", value = FALSE)
  #   }
  # }, ignoreNULL = FALSE)

  # ------------- Parangons, dist, v-test -------------

  plot_CA_clusters <- reactive({

    req(input$parang_paraORdist, input$nb_clusters)
    tryCatch({
    cluster_error_msg(NULL)
    data_type <- cluster_row_or_col()

      if (data_type == "columns") {
        data_type <- "col"
      } else {
        data_type <- "row"
      }
    individus_type <- input$parang_paraORdist
      if (individus_type == "closest to the center (medoids)") {
        individus_type <- "para"
        v_test_bool <- FALSE
      } else if (individus_type == "farthest from other clusters") {
        individus_type <- "dist"
        v_test_bool <- FALSE
      } else {
        individus_type <- "para"
        v_test_bool <- TRUE
      }

    nb_clusters <- ifelse(input$enable_num_clusters, input$nb_clusters, -1)


    
      # Select PCA of CA
      res <- if (analysis_method() == "PCA") req(res_pca()) else req(res_ca())

    # Recreate HCPC df
    # hclust <- HCPC(res, nb.clust = nb_clusters, graph = FALSE, cluster.CA = input$cluster_row_or_col)
    hclust_row <- HCPC(res, nb.clust = nb_clusters, graph=F, nb.par = input$nb_modalites_vtest)
    # Column clustering only exists for CA
    if (analysis_method() == "CA") {
      hclust_col <- HCPC(res, cluster.CA="columns", nb.clust = nb_clusters, graph=F, nb.par = input$nb_modalites_vtest)
    }

    hclust <- if (data_type == "col") hclust_col else hclust_row

    # Coordinates of the clustered items and of the describing variables
    # CA: row/col (the describing side is the other one); PCA: ind/var
    if (analysis_method() == "PCA") {
      ind_coords <- res$ind$coord
      var_coords <- res$var$coord
      desc_var <- hclust$desc.var$quanti
    } else {
      other_type <- if (data_type == "col") "row" else "col"
      ind_coords <- res[[data_type]]$coord
      var_coords <- res[[other_type]]$coord
      desc_var <- hclust$desc.var
    }

    # Extraire les parangons
    individus <- hclust$desc.ind[[individus_type]]
    individus.names <- unlist(lapply(individus, names))

    # Coordonnées des parangons sur les deux premières dimensions
    coords.individus <- ind_coords[individus.names, 1:2]

    
    # Déterminer à quel cluster appartient chaque parangon
    clusters <- sapply(individus.names, function(x) {
      which(sapply(individus, function(cl) x %in% names(cl)))
    })
    clusters <- factor(clusters)
    
    # Construire le data.frame
    df <- data.frame(
      Dim1 = coords.individus[,1],
      Dim2 = coords.individus[,2],
      Cluster = clusters,
      Nom = individus.names
    )
    
    if (isTRUE(v_test_bool)) {

      # type_array <- paste0("hclust_",data_type,"$desc.var")
      # array_type <- eval(parse(text = type_array))
      
      #extraire pour chaque cluster les var où v.test > 0
      # clust <- lapply(array_type, function(mat) {

      #extraire pour chaque cluster les var où v.test > 0
      clust <- lapply(desc_var, function(mat) {
        # PCA: clusters with no significant variable are NULL
        if (is.null(mat)) return(character(0))

        # Sélectionner uniquement les lignes avec v.test > 0
        vars <- rownames(mat)[mat[, "v.test"] > 0]
        # Garder au plus 5 variables
        head(vars, input$nb_modalites_vtest)
      })

      clust_clean <- lapply(clust, function(vec) {
          # Remplacer uniquement les points entre deux blocs {lemma_"..."} -> {lemma_"..."} {lemma_"..."}
        gsub("\\}\\.\\{", "} {", vec)
        })

        ind = unlist(clust_clean)


      #récupérer les coordonnées de ces ind
      coords.individus <- var_coords[ind, 1:2, drop = FALSE]


      clusters <- unlist(lapply(names(clust_clean), function(cluster_name) {
      individus <- clust_clean[[cluster_name]]
        setNames(rep(cluster_name, length(individus)), individus)
      }))
      clusters <- factor(clusters)

      # Construire le data.frame
      df <- data.frame(
        Dim1 = coords.individus[,1],
        Dim2 = coords.individus[,2],
        Cluster = clusters,
        Nom = ind
      )

      p <- ggplot(data = df, aes(x = Dim1, y = Dim2, color = Cluster)) +
        geom_point(size = 3) +
        ggrepel::geom_text_repel(aes(label = Nom), show.legend = FALSE, size = 3) +
        geom_hline(yintercept = 0, linetype = "dashed", color = "grey70") +
        geom_vline(xintercept = 0, linetype = "dashed", color = "grey70") +
        theme_classic() +
        theme(
          panel.grid = element_blank(),
          axis.line = element_blank(),
          axis.ticks = element_blank(),
          axis.text = element_blank(),
          axis.title = element_text(color = "grey30")
        ) +
        labs(
          title = input$plot_title_parang,
          x = input$plot_xlab_parang,
          y = input$plot_ylab_parang
        )
      
      # test_full <- paste0("hclust_", data_type, "$call$t$nb.clust")
      # test <- eval(parse(text = test_full))

    } else {

    # Construire le graphique
    p <- ggplot(data = df, aes(x = Dim1, y = Dim2, color = Cluster)) +
      geom_point(size = 3) +
      ggrepel::geom_text_repel(aes(label = Nom), show.legend = FALSE, size = 3) +
      geom_hline(yintercept = 0, linetype = "dashed", color = "grey70") +
      geom_vline(xintercept = 0, linetype = "dashed", color = "grey70") +
      theme_classic() +
      theme(
        panel.grid = element_blank(),
        axis.line = element_blank(),
        axis.ticks = element_blank(),
        axis.text = element_blank(),
        axis.title = element_text(color = "grey30")
      ) +
      labs(
        title = input$plot_title_parang,
        x = input$plot_xlab_parang,
        y = input$plot_ylab_parang
      )
    }

    return(p)
    }, error = function(e) {
      if (grepl("arguments must have same length", conditionMessage(e), fixed = TRUE))
        cluster_error_msg("Clustering failed: the number of items is incompatible with the requested number of clusters. Try changing the number of clusters or the row/column setting.")
      stop(e)
    })
  })


    # Display it (one output per representatives tab; only the visible one renders)
    for (out_id in c("CA_clusters_plot_medoids", "CA_clusters_plot_dist", "CA_clusters_plot_vtest")) {
      output[[out_id]] <- renderPlot({
        p <- req(plot_CA_clusters())
        p
      }, res = 96)
    }


    # Download handler
    observeEvent(input$save_cluster_v_test_post, {
        #base_dir <- getwd()
        file_name <- paste("CA_plots/Cluster_by_points", format(Sys.time(), "%Y-%m-%d_%H-%M-%S"), ".png", sep="")
        full_path <- file.path(patterns_dir, file_name)
        export_plot <- export_point_labels(plot_CA_clusters(), if (identical(input$export_mode, "custom")) input$cluster_export_label_pct else 100)
        d <- req(export_dims(12, 9))
        ggsave(full_path, plot = export_plot, width = d$width, height = d$height, units = d$units, dpi = d$dpi)
        showNotification(paste("Plot saved to:", full_path), type = "message")
      }
    )

  # UI Stuff
  observe({
    # Conditional logic to change textInput default value

    req(input$parang_paraORdist)
    if (input$parang_paraORdist == "closest to the center (medoids)") {
      updateTextInput(session, "plot_title_parang", value = "Factor map - medoids")
    } else if (input$parang_paraORdist == "farthest from other clusters") {
      updateTextInput(session, "plot_title_parang", value = "Factor map - representatives farthest from other clusters")
    } else if (input$parang_paraORdist == "variable associated by v-test") {
      updateTextInput(session, "plot_title_parang", value = "Factor map - variables associated by v-test")

    }
  })

# ------------- Cascading dropdown updates -------------

  update_cascade_input <- function(id, choices) {
    previous <- isolate(input[[id]])
    selected <- if (length(previous) && previous %in% choices) previous else head(choices, 1)
    updateSelectInput(session, id, choices = choices, selected = selected)
  }

  observeEvent(input$dataset_select_metadata, {
    cands <- get_candidates(meta = input$dataset_select_metadata)
    update_cascade_input("dataset_select_representation", extract_reps(cands))
  })

  observeEvent(list(input$dataset_select_metadata, input$dataset_select_representation), {
    rep <- req(input$dataset_select_representation)
    if (!grepl("motif", rep, ignore.case = TRUE)) return()
    cands <- get_candidates(meta = req(input$dataset_select_metadata), rep = rep)
    update_cascade_input("dataset_select_minsup", extract_minsup(cands))
  })

  observeEvent(list(input$dataset_select_metadata, input$dataset_select_representation,
                    input$dataset_select_minsup), {
    rep <- req(input$dataset_select_representation)
    if (!grepl("motif", rep, ignore.case = TRUE)) return()
    cands <- get_candidates(meta = req(input$dataset_select_metadata), rep = rep,
                            minsup = req(input$dataset_select_minsup))
    update_cascade_input("dataset_select_gapmin", extract_gapmin(cands))
  })

  observeEvent(list(input$dataset_select_metadata, input$dataset_select_representation,
                    input$dataset_select_minsup, input$dataset_select_gapmin), {
    rep <- req(input$dataset_select_representation)
    if (!grepl("motif", rep, ignore.case = TRUE)) return()
    cands <- get_candidates(meta = req(input$dataset_select_metadata), rep = rep,
                            minsup = req(input$dataset_select_minsup),
                            gapmin = req(input$dataset_select_gapmin))
    update_cascade_input("dataset_select_gapmax", extract_gapmax(cands))
  })

  observeEvent(list(input$dataset_select_metadata, input$dataset_select_representation,
                    input$dataset_select_minsup, input$dataset_select_gapmin, input$dataset_select_gapmax), {
    rep <- req(input$dataset_select_representation)
    if (!grepl("motif", rep, ignore.case = TRUE)) return()
    cands <- get_candidates(meta = req(input$dataset_select_metadata), rep = rep,
                            minsup = req(input$dataset_select_minsup),
                            gapmin = req(input$dataset_select_gapmin),
                            gapmax = req(input$dataset_select_gapmax))
    update_cascade_input("dataset_select_itemsetmin", extract_itemsetmin(cands))
  })

  observe({
    req(has_specifs)
    meta <- req(input$specifs_metadata_select)
    cands <- get_specif_candidates(meta)
    selected <- if (length(cands) > 0) cands[1] else character(0)
    updateSelectInput(session, "specifs_table_select", choices = format_specif_choices(cands), selected = selected)
  })


df_select_concatenated <- reactive({
  metadata_select <- req(input$dataset_select_metadata)
  representation_select <- req(input$dataset_select_representation)

  if (grepl("motif", representation_select, ignore.case = TRUE)) {
    candidates <- get_candidates(
      meta = metadata_select, rep = representation_select,
      minsup = as.character(req(input$dataset_select_minsup)),
      gapmin = as.character(req(input$dataset_select_gapmin)),
      gapmax = as.character(req(input$dataset_select_gapmax))
    )
    itemset <- as.character(req(input$dataset_select_itemsetmin))
    candidates <- candidates[sub(".*_([^_]+)$", "\\1", candidates) == itemset]
    req(length(candidates) > 0)
    df <- candidates[1]
  } else {
    df <- paste(metadata_select, representation_select, sep = "_")
  }

  req(df %in% normal_dataset_names)
  df
})

observe({
  # print("test:")
  print("Concatenated:")
  print(df_select_concatenated())
  print("Single string:")
  print(input$dataset_select)
  # print(datasets)
})

}


#--------------------------------------------------------------
# UI
#--------------------------------------------------------------
ui <- page_navbar(
  tags$head(
    tags$style(HTML("
      .pca-map[data-full-screen='true'] > .card-body {
        overflow: auto;
        overscroll-behavior: contain;
      }
      .pca-map[data-full-screen='true'] .shiny-plot-output {
        min-width: 200vw;
        min-height: 200vh;
        cursor: grab;
        user-select: none;
      }
      .pca-map[data-full-screen='true'] .shiny-plot-output:active {
        cursor: grabbing;
      }
      /* Make dropdown options wrap long words */
      .selectize-dropdown .option {
        white-space: normal !important;
        overflow-wrap: anywhere !important;
        word-break: break-all !important;
      }

      /* Wrap the selected item inside input */
      .selectize-input > div {
        white-space: normal !important;
        overflow-wrap: anywhere !important;
        word-break: break-all !important;
      }

      /* Let the dropdown expand wider */
      .selectize-dropdown {
        width: auto !important;
        min-width: 400px;
        max-width: 800px;
      }

      /* Notifications wide enough for full file paths */
      #shiny-notification-panel {
        max-width: calc(100vw - 20px);
        right: 10px;
        width: 600px;
      }
      .shiny-notification {
        width: 100%;
        word-break: break-all;
      }
    ")),
    tags$script(HTML("
      document.addEventListener('pointerdown', function(event) {
        if (event.pointerType !== 'mouse' || event.button !== 0) return;
        const plot = event.target.closest('.pca-map[data-full-screen=true] .shiny-plot-output');
        if (!plot) return;
        const viewport = plot.closest('.card-body');
        const startX = event.clientX, startY = event.clientY;
        const left = viewport.scrollLeft, top = viewport.scrollTop;
        function pan(move) {
          viewport.scrollLeft = left + startX - move.clientX;
          viewport.scrollTop = top + startY - move.clientY;
        }
        event.preventDefault();
        plot.setPointerCapture(event.pointerId);
        plot.addEventListener('pointermove', pan);
        plot.addEventListener('lostpointercapture', function() {
          plot.removeEventListener('pointermove', pan);
        }, {once: true});
      });
    "))
  ),
  useShinyjs(),
  title = "MWB: Motif Work Bench",
  id = "tabselected",
  # tags$div(style = "text-align: left; color: #888; font-size: 18px; margin-bottom: 10px;",
  #   "User interface for Correspondence Analysis and clustering"
  # ),
  # tags$div(style = "text-align: left; color: #888; font-size: 12px; margin-bottom: 10px;",
  #   "Timothée Premat and Hugo Dumoulin, ArchivU project, 2025"
  # ),

  sidebar = accordion(
    id = "accordions",
    open = "Plot settings",
        accordion_panel(
          title = "Motifs settings ",
          id = "data_settings_accordion",
          conditionalPanel(
            condition = "input.input_sel_method == true",
              selectInput(
                inputId = "dataset_select",          # ID for server to access
                label = tooltip(
                    trigger = list(
                      "Dataset",
                      bs_icon("info-circle")
                    ),
                    HTML("DATASET SELECTION<br/>
                    Depending on your settings, MWB produced several datasets. Select the one to be plotted.")
                  ),

                choices = normal_dataset_names,            # populate dropdown with keys
                selected = normal_dataset_names[1]

              ),
          ),
          conditionalPanel(
            condition = "input.input_sel_method == false",
              selectInput(
                inputId = "dataset_select_metadata",
                label = tooltip(
                    trigger = list(
                      "Metadata",
                      bs_icon("info-circle")
                    ),
                    HTML("DATASET SELECTION<br/>
                    Depending on your settings, MWB produced several datasets. Select the contrastive metadata.")
                  ),
                choices = metadata_name,            # populate dropdown with keys
                selected = metadata_name[1]
              ),
              selectInput(
                inputId = "dataset_select_representation",
                label = tooltip(
                    trigger = list(
                      "Level of representation",
                      bs_icon("info-circle")
                    ),
                    "Select the level of representation used to define linguistic units."
                  ),
                choices = pattern_representation,            # populate dropdown with keys
                selected = pattern_representation[1]
              ),
              conditionalPanel(condition = "input.dataset_select_representation == 'motif' || input.dataset_select_representation == 'motifs' || input.dataset_select_representation == 'internal-clustering-motifs'",
                selectInput(
                  inputId = "dataset_select_minsup",
                  label = tooltip(
                    trigger = list(
                      "Minsup",
                      bs_icon("info-circle")
                    ),
                    "Select the minimal support frequency for motifs."
                  ),
                  choices = minsup_display,            # populate dropdown with keys
                  selected = minsup_display[1]
                ),
                selectInput(
                  inputId = "dataset_select_gapmin",
                  label = tooltip(
                    trigger = list(
                      "Gapmin",
                      bs_icon("info-circle")
                    ),
                    "Select the gap requirement for motifs."
                  ),
                  choices = gapmin_display,            # populate dropdown with keys
                  selected = gapmin_display[1]
                ),
                selectInput(
                  inputId = "dataset_select_gapmax",
                  label = tooltip(
                    trigger = list(
                      "Gapmax",
                      bs_icon("info-circle")
                    ),
                    "Select gap tolerance for motifs."
                  ),
                  choices = gapmax_display,            # populate dropdown with keys
                  selected = gapmax_display[1]
                ),
                selectInput(
                  inputId = "dataset_select_itemsetmin",
                  label = tooltip(
                    trigger = list(
                      "Itemset min size",
                      bs_icon("info-circle")
                    ),
                    "Select the minimal size of motifs (nbr of itemsets)."
                  ),
                  choices = itemsetmin_display,            # populate dropdown with keys
                  selected = itemsetmin_display[1]
                ),
              ),
            ),
          checkboxInput("input_sel_method", " Use single name", value=FALSE)
        ),
        accordion_panel("Plot settings",
          id = "plot_settings_accordion",

          selectInput(
            inputId = "analysis_method",
            label = tooltip(
              trigger = list(
                "Analysis method",
                bs_icon("info-circle")
              ),
              HTML("PCA: Principal Component Analysis<br/>CA: Correspondence Analysis<br/>Note that
              due to multidimensionality of motives, CA can be misleading in some cases.")
            ),
            choices = c("PCA" = "PCA", "CA" = "CA"),
            selected = "PCA"
          ),
          conditionalPanel(condition = "input.tabselected == 'PCA-CA'",
            checkboxInput("contrib_threshold", "Min. contrib. threshold", value=TRUE),

              conditionalPanel(
                condition = "input.contrib_threshold == true",
                sliderInput(
                  "contrib_vars",

                  label = HTML("<i>N</i>-th most contrib. cols"),

                  min = 1,
                  max = 100,
                  value = 10,
                  step = 5
                ),
                sliderInput(
                  "contrib_rows",

                  label = HTML("<i>N</i>-th most contrib. rows"),
                  min = 1,
                  max = 100,
                  value = 10,
                  step = 5
                ),
              ),
            checkboxGroupInput(
              inputId = "show_items",
              label = "Show:",
              choices = c("Columns points", "Columns labels", "Rows points", "Rows labels"),
              selected = c("Columns points", "Columns labels", "Rows points", "Rows labels")
            ),
            checkboxGroupInput(
              inputId = "size",
              label = "Show contribution as:",
              choices = c("Points size", "Label size")#,
              # selected = "none")
            ),
            #conditionalPanel(
             # condition = "input.size == 'Points size' || input.size == 'Label size'",
             # selectInput(
             #   "selected_axis",
             #   "Axis for contribution",
             #   choices = NULL,  # initially empty
             #  selected = 1
             # ),
         	#   ),
            sliderInput(
              "jitter_strength",
              "Strenght of label repelling:",
              min = 0,
              max = 1,
              value = 0.5,
              step = 0.05
            ),
            # p(HTML("<i>Scaling labels often results in lesser constributive labels disapearing. You might need to deactivate jittering if lines are displayed with no labels:</i>")),
            # checkboxInput("deactivate_jitter", HTML("Deactivate jittering <i>(only available with 'Label size' checked)</i>"), value=FALSE),

            conditionalPanel(condition = "input.analysis_method == 'CA'",
              textInput("plot_title_CA", "Plot Title:", value = "CA - Biplot")
            ),
            conditionalPanel(condition = "input.analysis_method == 'PCA'",
              checkboxInput("show_supplementary", "Show supplementary variable", value = FALSE),
              conditionalPanel("input.show_supplementary", uiOutput("supplementary_selector")),
              textInput("plot_title_PCA", "Individuals plot title:", value = "PCA - Individuals"),
              textInput("plot_title_PCA_circle", "Circle plot title:", value = "PCA - Variables")
            ),

            actionButton(
                  inputId = "save_CA_plot",
                  label = "Save plot",
                  icon = icon("download"), # FontAwesome icon before text, as in downloadButton
                  class = "btn-primary", # Optional: Bootstrap color styling
                  style = "width: 100%;"
                )
          ),
          conditionalPanel(
            condition="input.tabselected == 'scree'",
              textInput("plot_title_scree", "Plot title", value = "Scree plot"),
              textInput("plot_ylab_scree", "Y axis title", value = "Percentage of explained variances"),
              textInput("plot_xlab_scree", "X axis title:", value = "Dimensions"),
              actionButton(
                inputId = "save_scree_plot",
                label = "Save plot",
                icon = icon("download"), # FontAwesome icon before text, as in downloadButton
                class = "btn-primary", # Optional: Bootstrap color styling
                style = "width: 100%;"
              ),
          ),
          conditionalPanel(
            condition="input.tabselected == 'contrib'",
              selectInput(
                "contrib_choice",
                "Select dimension:",
                choices = c("row", "col"),
                selected = "row"
              ),
              numericInput(
                "contrib_axes",
                "Select axis:",
                value = 1,
                min = 1,
                max = 5
              ),
              checkboxInput("contrib_custom_title", "Use custom title?", value=FALSE),
                conditionalPanel(
                  condition = "input.contrib_custom_title == true",
                  textInput("plot_title_contrib", "Plot Title:", value = "Contribution of XX to Dim-XX"),
                ),              
              textInput("plot_ylab_contrib", "Y axis title", value = "Contributions (%)"),
              checkboxInput("scree_hide_labels", "Hide labels", value=FALSE),
              actionButton(
                inputId = "save_contrib_plot",
                label = "Save plot",
                icon = icon("download"), # FontAwesome icon before text, as in downloadButton
                class = "btn-primary", # Optional: Bootstrap color styling
                style = "width: 100%;"
              )
          ),
          conditionalPanel(
            condition="input.tabselected == 'clustering' || input.tabselected == 'parang_panel'",
              checkboxInput(
                "enable_num_clusters",
                "Use custom number of clusters",
                value = FALSE
              ),
              numericInput(
                "nb_clusters",
                "Custom number of clusters:",
                min = 2,
                value = 2
              ),

              # Row/column clustering only applies to CA (PCA always clusters rows)
              conditionalPanel(
                condition = "input.analysis_method == 'CA'",
                selectInput(
                  "cluster_row_or_col",
                  "Select dimension:",
                  choices = c("rows", "columns"),
                  selected = "rows"
                )
              ),
              hr()
          ),
          conditionalPanel(
            condition="input.tabselected == 'clustering'",
              selectInput(
                "type_of_plot",
                "Type of graph",
                choices = c("tree", "bar", "map", "3D.map"),
                selected = "tree"
              ),
              checkboxInput("bool_consol_tree",
              label = tooltip(
                    trigger = list(
                      "Apply consolidation to classes",
                      bs_icon("info-circle")
                    ),
                    "By default, k-mean consolidation is applied to classes, resulting in 
                inconsistencies between tree and clusters."
                  ),
              # "Apply consolidation to classes",
              value=TRUE),
              # helpText(HTML("By default, k-mean consolidation is applied to classes, resulting in 
                # inconsistencies between tree and clusters.")),
              checkboxInput(
                "ind_name",
                "Hide individuals name",
                value = FALSE
              ),
              conditionalPanel(
                condition = "input.type_of_plot == 'map'",
                checkboxInput(
                  "bool_draw_tree",
                  "Draw tree",
                  value = TRUE
                ),
              ),
              actionButton(
                inputId = "download_clusters",
                label = "Save plot",
                icon = icon("download"),
                class = "btn-primary",
                style = "width: 100%;"
              )
          ),
          conditionalPanel(
            condition="input.tabselected == 'parang_panel'",

              sliderInput(
                inputId = "nb_modalites_vtest",
                label = "Max. number of representatives",
                min = 1,
                max = 50,   
                value = 5,
                step = 1
              ),
              textInput("plot_title_parang", "Plot title", value = ""),
              textInput("plot_xlab_parang", "X axis title:", value = "Dimension 1"),
              textInput("plot_ylab_parang", "Y axis title", value = "Dimension 2"),
              actionButton(
                inputId = "save_cluster_v_test_post",
                label = "Save plot",
                icon = icon("download"), # FontAwesome icon before text, as in downloadButton
                class = "btn-primary", # Optional: Bootstrap color styling
                style = "width: 100%;"
              )
          ),
          conditionalPanel(
            condition = "['PCA-CA', 'scree', 'contrib', 'clustering', 'parang_panel'].indexOf(input.tabselected) > -1",
              hr(),
              radioButtons("export_mode", "Export resolution",
                           choices = c("Default" = "default", "Custom" = "custom"),
                           selected = "default", inline = TRUE),
              conditionalPanel(
                condition = "input.export_mode == 'custom'",
                fluidRow(
                  column(6, numericInput("export_width",  "Width",  value = 12, min = 0.1, step = 0.5)),
                  column(6, numericInput("export_height", "Height", value = 9,  min = 0.1, step = 0.5))
                ),
                fluidRow(
                  column(6, selectInput("export_units", "Units", choices = c("in", "cm", "mm", "px"), selected = "in")),
                  column(6, numericInput("export_dpi", "DPI", value = 300, min = 72, max = 1200, step = 50))
                )
              ),
              helpText(textOutput("export_px_info", inline = TRUE)),
              conditionalPanel(condition = "input.export_mode == 'custom' && input.tabselected == 'PCA-CA'",
                sliderInput("factor_export_label_pct", "Point label size in export (%)",
                            min = 100, max = 300, value = 100, step = 25)
              ),
              conditionalPanel(condition = "input.export_mode == 'custom' && input.tabselected == 'parang_panel'",
                sliderInput("cluster_export_label_pct", "Point label size in export (%)",
                            min = 100, max = 300, value = 100, step = 25)
              )
          ),
          if (has_specifs) conditionalPanel(
            condition="input.tabselected == 'specifs'",
              selectInput(
                inputId = "specifs_metadata_select",
                label = "Métadonnée",
                choices = specif_metadata_names
              ),
              selectInput(
                inputId = "specifs_table_select",
                label = "Table de spécificités",
                choices = format_specif_choices(get_specif_candidates(specif_metadata_names[1]))
              )
          ),

        ),
      # )
    ),
    
    # navset_pill(
    #   id = "tabselected",
        nav_panel(

          "PCA/CA",
          value = 'PCA-CA',
          # p("text"),
          conditionalPanel(
            condition = "input.analysis_method == 'PCA'",
            layout_columns(
              col_widths = c(6, 6),
              div(
                card(class = "pca-map", full_screen = TRUE, height = "700px",
                     plotOutput("PCAplot", height = "100%")),
                conditionalPanel("input.show_supplementary && output.has_supplementary_eta === 'yes'",
                  class = "mt-2",
                  accordion(open = FALSE,
                    accordion_panel("η² by PCA axis", DTOutput("supplementary_eta"))
                  )
                )
              ),
              card(class = "pca-map", full_screen = TRUE, height = "700px",
                   plotOutput("PCAcircleplot", height = "100%"))
            )
          ),
          conditionalPanel(
            condition = "input.analysis_method == 'CA'",
            card(plotOutput("CAplot", height = "700px"))
          ),
        ),
        nav_panel(
          "Scree Plot",

          value = "scree",
          card(plotOutput("screePlot"))
        ),
        nav_panel(
          "Contrib. plot",
          value = 'contrib',
          card(plotOutput("contribPlot"))
        ),
        nav_panel(
          "Clustering",
          value = "clustering",
          card(
            plotOutput("clusters_plot"),

            textOutput("cluster_error_msg_hcpc"),
            card_footer("Note that, using PCA, clustering is only possible on individuals.
            One approach is to use the 'Variables by v-test' tab in the Clusters representatives panel.")
          )
        ),
        nav_panel(
          "Clusters representatives",
          value = "parang_panel",

          # One tab per type of representative; the selected tab's value sets input$parang_paraORdist
          navset_card_tab(
            id = "parang_paraORdist",
            selected = "closest to the center (medoids)",
            nav_panel("Medoids", value = "closest to the center (medoids)",
              plotOutput("CA_clusters_plot_medoids")),
            nav_panel("Farthest from other clusters", value = "farthest from other clusters",
              plotOutput("CA_clusters_plot_dist")),
            nav_panel("Variables by v-test", value = "variable associated by v-test",
              plotOutput("CA_clusters_plot_vtest")),
            # card_footer() keeps it fixed-size; a bare tagList becomes a growing card body
            footer = card_footer(
              textOutput("cluster_error_msg_parang"),
              "Depending on data size, clusters' representatives computation may take some time."
            )
          )
        ),
        nav_panel(
          "Dataset",
            fluidRow(
              card(
                h4("Dataset"),
                column(
                  width = 12,
                  DTOutput("data_table")
                ),
                card_footer("PCA observations are expressed relative to part size (text, genre, etc.) when sizes are available.")
              )
            )
        ),
        nav_panel(
          "Specifs",
          value = "specifs",
          if (has_specifs) {
            card(DTOutput("specifs_table"))
          } else {
            card(p("Aucune table de spécificités disponible pour cette analyse."))
          }
        ),

      # ),

      theme = bslib::bs_theme(),

    )




#-------------------------------
# RUN SHINY APP
#-------------------------------
args_run <- commandArgs(trailingOnly = TRUE)
host_run <- ifelse(length(args_run) >= 2, args_run[2], "127.0.0.1")
port_run <- ifelse(length(args_run) >= 3, as.integer(args_run[3]), 3838)

shiny::runApp(
  list(ui = ui, server = server),
  host = host_run,
  port = port_run,
  launch.browser = FALSE
)

