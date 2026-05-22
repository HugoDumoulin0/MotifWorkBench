# Timothée Premat and Hugo Dumoulin vTim
# 28/03/2025

#--------------------------------------------------------------
# Python/R interface
#--------------------------------------------------------------
args <- commandArgs(trailingOnly = TRUE)
# file = args[1]
path = args[1]

# input_file <- file
# base_name <- basename(input_file)

# head(input_file)

dir.create("./Patterns_results/CA_plots", recursive = TRUE, showWarnings = FALSE)


rep_name=path

#--------------------------------------------------------------
# BASIC R STUFF
#--------------------------------------------------------------

#Load/install packages, input file and set variables
ipak <- function(pkg){
options(repos = c(CRAN = "https://cloud.r-project.org"))
new.pkg <- pkg[!(pkg %in% installed.packages()[, "Package"])]
if (length(new.pkg))
    install.packages(new.pkg, dependencies = TRUE)
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


# Load JSON from python
datasets <- fromJSON(paste(json_input, collapse = ""))

print(datasets)

metadata_name <- unique(sub("_.*", "", names(datasets)))
print("Metadata name:")
print(metadata_name)

has_user_input_list <- grepl("user_input_listTrue", names(datasets))
print("Has user input list:")
print(has_user_input_list)

name_user_input <- names(datasets)[grepl("user_input_listTrue", names(datasets))]
user_input_value <- sub(".*user_input_listTrue([^_]+).*", "\\1", name_user_input)
print("User input value:")
print(user_input_value)

has_early_sel <- ifelse(any(grepl("earlySelectionTrue", names(datasets))), TRUE, FALSE)
print("Has early selection:")
print(has_early_sel)

name_early_sel <- names(datasets)[grepl("earlySelectionTrue", names(datasets))]
early_sel_num <- sub(".*earlySelectionTrue([0-9]+).*", "\\1", name_early_sel)
print("Early selection num:")
print(early_sel_num)

early_pos4lemma <- sub(".*early_pos4lemma([^_]+).*", "\\1", name_early_sel)
print("Early pos4lemma")
print(early_pos4lemma)

has_specifs <- ifelse(any(grepl("specifsTrue", names(datasets))), TRUE, FALSE)
print("Has specifs:")
print(has_specifs)

specif_part <- sub(".*specifsTrue([^_][^motif]+).*", "\\1", name_early_sel)
print("Specif part:")
print(specif_part)

name_motifs <- names(datasets)[grepl("motif", names(datasets), ignore.case = TRUE)]
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
  grepl("motif", names(datasets), ignore.case = TRUE),
  "motif",
  sub(".*_([^_]+)$", "\\1", names(datasets))
))


early_list <- early_sel_num
pattern_representation <- pattern_representations
minsup_display <- minsup
gapmin_display <- gapmin
gapmax_display <- gapmax
itemsetmin_display <- itemsetmin

#--------------------------------------------------------------
# HELPERS FOR CASCADING DROPDOWNS
#--------------------------------------------------------------

get_candidates <- function(meta=NULL, rep=NULL, early=NULL, minsup=NULL, gapmin=NULL, gapmax=NULL) {
  cands <- names(datasets)
  if (!is.null(meta))
    cands <- cands[startsWith(cands, paste0(meta, "_"))]
  if (!is.null(rep)) {
    if (grepl("motif", rep, ignore.case=TRUE))
      cands <- cands[grepl("motif", cands, ignore.case=TRUE)]
    else
      cands <- cands[endsWith(cands, paste0("_", rep))]
  }
  if (!is.null(early) && early != "No (all tokens)")
    cands <- cands[grepl(paste0("earlySelectionTrue", early), cands, fixed=TRUE)]
  if (!is.null(minsup))
    cands <- cands[grepl(paste0("_", minsup, "_[^_]+_[^_]+_[^_]+$"), cands, perl=TRUE)]
  if (!is.null(gapmin))
    cands <- cands[grepl(paste0("_[^_]+_", gapmin, "_[^_]+_[^_]+$"), cands, perl=TRUE)]
  if (!is.null(gapmax))
    cands <- cands[grepl(paste0("_[^_]+_[^_]+_", gapmax, "_[^_]+$"), cands, perl=TRUE)]
  cands
}

extract_reps      <- function(cands) unique(ifelse(grepl("motif", cands, ignore.case=TRUE), "motif", sub(".*_([^_]+)$", "\\1", cands)))
extract_early     <- function(cands) unique(sub(".*earlySelectionTrue([0-9]+).*", "\\1", cands[grepl("earlySelectionTrue", cands)]))
extract_minsup    <- function(cands) unique(sub(".*_([^_]+)_[^_]+_[^_]+_[^_]+$", "\\1", cands))
extract_gapmin    <- function(cands) unique(sub(".*_[^_]+_([^_]+)_[^_]+_[^_]+$", "\\1", cands))
extract_gapmax    <- function(cands) unique(sub(".*_[^_]+_[^_]+_([^_]+)_[^_]+$", "\\1", cands))
extract_itemsetmin <- function(cands) unique(sub(".*_[^_]+_[^_]+_[^_]+_([^_]+)$", "\\1", cands))

#--------------------------------------------------------------
# SERVER
#--------------------------------------------------------------
server <- function(input, output, session){

  # Show specificity filter only when the current metadata+representation has early options
  output$has_specifs_df <- renderText({
    cands <- get_candidates(meta=input$dataset_select_metadata, rep=input$dataset_select_representation)
    as.character(length(extract_early(cands)) > 0)
  })
  outputOptions(output, "has_specifs_df", suspendWhenHidden = FALSE)

  # Deal with input selection
  input_selection <- reactive({
    dataset_select <- req(input$dataset_select)           # selecting df all in one
    df_select_concatenated <- req(df_select_concatenated(), cancelOutput = FALSE)   # selecting df by separate categories

     if (input$input_sel_method == FALSE) {
      df <- df_select_concatenated
     } else { 
      df <- dataset_select
     }
    path <- datasets[[df]]   # extract path
    # Ensure it's a single string
    if(!is.character(path) || length(path) != 1){
      stop("Selected dataset is not a valid file path")
    }
    path
  })

  # Load selected data
  data1 <- reactive({
    path <- req(input_selection())
    data <- read.csv(path, sep="\t", row.names = 1, header=T, check.names = FALSE)
  })

  data <- reactive({
    data <- req(data1())
    rownames(data) <- gsub(" ", "_", rownames(data))
    data <- data[rowSums(data) != 0, ]
  })


  # Reactive value to hold CA result and an error message for display
  ca_res <- reactiveVal(NULL)
  ca_error <- reactiveVal(NULL)
  cluster_error_msg <- reactiveVal(NULL)

  output$cluster_error_msg_hcpc  <- renderText({ cluster_error_msg() })
  output$cluster_error_msg_parang <- renderText({ cluster_error_msg() })

  # Compute CA automatically when preprocessing result is ready
  observeEvent(data(), {
    d <- data()
  })

  #Preview data
  output$data_table <- renderDT({
    datatable(
      data(),
      options = list(
        pageLength = 10,
        autoWidth = TRUE,
        scrollX = TRUE
      ),
      filter = "top",    # adds per-column filters
      rownames = TRUE
    )
  })

  # ------------- Screeplot -------------
  # Store the plot as a reactive
  scree_plot <- reactive({
    data <- req(data())
    AFC <- CA(data)
    req(AFC)
    p <- fviz_screeplot(AFC,
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
      base_dir <- getwd()
      file_name <- paste("Patterns_results/CA_plots/ScreePlot_", format(Sys.time(), "%Y-%m-%d_%H-%M-%S"), ".png", sep="")
      full_path <- file.path(base_dir, file_name)
      ggsave(full_path, plot = scree_plot(), width = 8, height = 6, dpi = 300)
      showNotification(paste("Plot saved to:", full_path), type = "message")
    }
  )

  # ------------- CA computation -------------
  res_ca <- reactive({
    data <- req(data())                # your reactive data object
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

  # ------------- CA ploting -------------
    # Store the plot as a reactive
    CA__plot <- reactive({
      res <- req(res_ca())
      points_data <- req(ca_prep())
      cols_df <- points_data$cols
      rows_df <- points_data$rows
      cols_size_df <- as.data.frame(points_data$col_contrib) %>%
        rename(Contrib_Dim_1 = 'Dim 1', Contrib_Dim_2 = 'Dim 2') %>%
        rownames_to_column('label')
      rows_size_df <- as.data.frame(points_data$row_contrib) %>%
      rename(Contrib_Dim_1 = 'Dim 1', Contrib_Dim_2 = 'Dim 2') %>%
      rownames_to_column('label')
      cols_df <- merge(cols_df, cols_size_df, by = "label", all = TRUE)
      rows_df <- merge(rows_df, rows_size_df, by = "label", all = TRUE)


      # Retrieve display properties choices
        show_col_points <- "Columns points" %in% input$show_items
        show_row_points <- "Rows points" %in% input$show_items
        show_col_labels <- "Columns labels" %in% input$show_items
        show_row_labels <- "Rows labels" %in% input$show_items
        points_size <- "Points size" %in% input$size
        label_size <- "Label size" %in% input$size
        # points_color <- "Points color" %in% input$size
        # label_color <- "Label color" %in% input$size
          # Get selected axis
          axis_num <- input$selected_axis
          # Prefix the value
          contrib_var <- paste0("Contrib_Dim_", axis_num)
       #   cols_df$contrib_var <- cols_df[[contrib_var]]
         # rows_df$contrib_var <- rows_df[[contrib_var]]
         cols_df$contrib_var <- rowSums(cols_df[, grep("^Contrib_Dim_", names(cols_df))]) 	#computing contrib on all axis
		rows_df$contrib_var <- rowSums(rows_df[, grep("^Contrib_Dim_", names(rows_df))])


      if (input$contrib_threshold) {
        ca_plot <- factoextra::fviz_ca_biplot(res,
          repel = TRUE,
          geom = "all",
          ggtheme = ggplot2::theme_minimal(),
          select.row = list(contrib = input$contrib_rows),
          select.col = list(contrib = input$contrib_vars)
        )
      } else {
        ca_plot <- factoextra::fviz_ca_biplot(res, repel = TRUE, geom = "none", ggtheme = ggplot2::theme_minimal())
      }
		ca_plot <- ca_plot +
  scale_size_continuous(range = c(2, 6))									#minimal size for readability (HugoDumoulin)
      # Conditionnaly add points and/or labels
      strenght <- input$jitter_strength
      if (show_col_labels) {                                                      # If labels of rows are showed   
        if (label_size) {                                                    # If label size == contrib
          ca_plot <- ca_plot +
          geom_text_repel(data = cols_df,
                aes(x = `Dim 1`, y = `Dim 2`, label = label,
                size = contrib_var),
                color = "red", vjust = -0.5,
                force=strenght) #+
                # guides(size="none")
        } else {                                                               # If not, label size is fixed
          ca_plot <- ca_plot +
          geom_text_repel(data = cols_df,
                aes(x = `Dim 1`, y = `Dim 2`, label = label),
                color = "red", vjust = -0.5,
                force=strenght)
        }
      }
      if (show_row_labels) {                                                      # If labels of rows are showed
        if (label_size) {                                                    # If label size == contrib and jitter                                                      # If label size == contrib
          ca_plot <- ca_plot +
          geom_text_repel(data = rows_df,
                aes(x = `Dim 1`, y = `Dim 2`, label = gsub("dep_|lemma_|pos_|feats_", "", label),
                size = contrib_var),
                color = "blue", vjust = -0.5,
                force=strenght) #+
                # guides(size="none")
        } else {
                ca_plot <- ca_plot +
          geom_text_repel(data = rows_df,
                aes(x = `Dim 1`, y = `Dim 2`, label = gsub("dep_|lemma_|pos_|feats_", "", label)),
                color = "blue", vjust = -0.5,
                force=strenght)
        }
      }
      if (show_col_points) {                                                      # If points of columns are showed
        if (points_size) {                                                          # If points size == contrib
          ca_plot <- ca_plot +
          geom_point(data = cols_df,
                aes(x = `Dim 1`, y = `Dim 2`, size = contrib_var), shape = 17,
                color = "red") +
                labs(size = paste("Contrib.\non axis ", axis_num, sep=""))
        } else {                                                                    # If not, points size is fixed
          ca_plot <- ca_plot +
          geom_point(data = cols_df,
                aes(x = `Dim 1`, y = `Dim 2`), shape = 17,
                color = "red")
        }
      }
      if (show_row_points) {                                                        # If points of rows are showed
        if (points_size) {                                                            # If points size == contrib
          ca_plot <- ca_plot +
          geom_point(data = rows_df,
                aes(x = `Dim 1`, y = `Dim 2`, size = contrib_var), shape = 19,
                color = "blue")
        } else {                                                                     # If not, points size is fixed
          ca_plot <- ca_plot +
          geom_point(data = rows_df,
                aes(x = `Dim 1`, y = `Dim 2`), shape = 19,
                color = "blue")
        }
      }

      # Conditional for point size legend but no label size legend
      if (points_size & !label_size) {
        ca_plot <- ca_plot + guides(size = guide_legend(title = paste("Contrib.\non axis ", axis_num, sep="")))
      } else if (!points_size) {
        ca_plot <- ca_plot + guides(size = "none")
      } else if (points_size & label_size) {
        ca_plot <- ca_plot + guides(size = guide_legend(
          title = paste("Contrib.\non axis ", axis_num, sep=""),
          override.aes = list(label = "")))
      # } else if (points_size & input$deactivate_jitter & !label_size) {
      #   ca_plot <- ca_plot + guides(size = guide_legend(
      #     title = paste("Contrib.\non axis ", axis_num, sep=""),
      #     override.aes = list(label = "")))
      } else {
        ca_plot <- ca_plot
      }

      ca_plot <- ca_plot +
        labs(title = input$plot_title_CA)

      ca_plot
    })

    # Display it
    output$CAplot <- renderPlot({
      p <- req(CA__plot())
      p
    }, res = 96)

    # Download handler
    observeEvent(input$save_CA_plot, {
        base_dir <- getwd()
        file_name <- paste("Patterns_results/CA_plots/CA_", format(Sys.time(), "%Y-%m-%d_%H-%M-%S"), ".png", sep="")
        full_path <- file.path(base_dir, file_name)
        ggsave(full_path, plot = CA__plot(), width = 12, height = 9, dpi = 300)
        showNotification(paste("Plot saved to:", full_path), type = "message")
      }
    )

  # ------------- Contrib plotting -------------
  contrib_plot <- reactive({
    res <- req(res_ca())
    # Get user inputs
      user_choice <- req(input$contrib_choice)  # e.g. "row" or "col"
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
      base_dir <- getwd()
      file_name <- paste("Patterns_results/CA_plots/Contrib_", format(Sys.time(), "%Y-%m-%d_%H-%M-%S"), ".png", sep="")
      full_path <- file.path(base_dir, file_name)
      ggsave(full_path, plot = contrib_plot(), width = 8, height = 6, dpi = 300)
      showNotification(paste("Plot saved to:", full_path), type = "message")
    }
  )


  # ------------- Clustering -------------
  # Note : because HCPC is base R (not ggplot), I can't create it in a reactive and then renderPlot and save it through observeEvent
  # Simplest fix is to copy-paste the code in two functions, which is OK as the code is short

  output$clusters_plot <- renderPlot({
    req(input$nb_clusters,
      input$cluster_row_or_col,
      !is.null(input$type_of_plot),
      !is.null(input$ind_name),
      !is.null(input$bool_consol_tree),
      !is.null(input$bool_draw_tree)
    )
    AFC <- req(res_ca())
    nb_clusters <- ifelse(input$enable_num_clusters, input$nb_clusters, -1)
    type <- input$type_of_plot
    ind_name <- if (isTRUE(input$ind_name)) "FALSE" else "TRUE"
    draw_tree <- if (isTRUE(input$bool_draw_tree)) "TRUE" else "FALSE"

    tryCatch({
      hclust <- FactoMineR::HCPC(AFC,
        nb.clust = nb_clusters,
        consol = input$bool_consol_tree,
        graph = FALSE,
        cluster.CA = input$cluster_row_or_col)

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
    req(input$nb_clusters, input$cluster_row_or_col, !is.null(input$type_of_plot), !is.null(input$ind_name))
    AFC <- req(res_ca())
    nb_clusters <- ifelse(input$enable_num_clusters, input$nb_clusters, -1)
    type <- input$type_of_plot
    ind_name <- if (isTRUE(input$ind_name)) "FALSE" else "TRUE"
    hclust <- HCPC(AFC,
      nb.clust = nb_clusters,
      consol = input$bool_consol_tree,
      graph = FALSE,
      cluster.CA = input$cluster_row_or_col)

    base_dir <- getwd()
    full_dir <- file.path(base_dir, "Patterns_results/CA_plots")
    if (!dir.exists(full_dir)) dir.create(full_dir, recursive = TRUE)
    full_path <- file.path(full_dir, paste0("Clusters_", format(Sys.time(), "%Y-%m-%d_%H-%M-%S"), ".png"))

    png(full_path, width = 12, height = 9, units="in", res=300)
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
    req(input$parang_paraORdist, input$nb_clusters, input$cluster_row_or_col)
    tryCatch({
    cluster_error_msg(NULL)
    data_type <- input$cluster_row_or_col
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

    AFC <- req(res_ca())

    # Recreate HCPC df
    # hclust <- HCPC(AFC, nb.clust = nb_clusters, graph = FALSE, cluster.CA = input$cluster_row_or_col)
    hclust_row <- HCPC(AFC, nb.clust = nb_clusters, graph=F, nb.par = input$nb_modalites_vtest)
    hclust_col <- HCPC(AFC, cluster.CA="columns", nb.clust = nb_clusters, graph=F, nb.par = input$nb_modalites_vtest)
    
    # Extraire les parangons
    individus_full <- paste0("hclust_",data_type,"$desc.ind$", individus_type)
    individus <- eval(parse(text = individus_full))
    individus.names <- unlist(lapply(individus, names))
    
    # Coordonnées des parangons sur les deux premières dimensions
    coords_full <- paste0("AFC$", data_type, "$coord")
    coords=eval(parse(text = coords_full))
    coords.individus <- coords[individus.names, 1:2]
    
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
      type_array <- paste0("hclust_",data_type,"$desc.var")
      array_type <- eval(parse(text = type_array))
      
      #extraire pour chaque cluster les var où v.test > 0
      clust <- lapply(array_type, function(mat) {
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
        
        if (data_type=="col"){
          AFC_type = "row"
        }
        
        if (data_type=="row"){
          AFC_type = "col"
        }

      #récupérer les coordonnées de ces ind
      coords_full <- paste0("AFC$", AFC_type, "$coord")
      coords=eval(parse(text = coords_full))
      coords.individus <- coords[ind, 1:2]

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

    # Display it
    output$CA_clusters_plot <- renderPlot({
      p <- req(plot_CA_clusters())
      p
    }, res = 96)

    # Download handler
    observeEvent(input$save_cluster_v_test_post, {
        base_dir <- getwd()
        file_name <- paste("Patterns_results/CA_plots/Cluster_by_points", format(Sys.time(), "%Y-%m-%d_%H-%M-%S"), ".png", sep="")
        full_path <- file.path(base_dir, file_name)
        ggsave(full_path, plot = plot_CA_clusters(), width = 12, height = 9, dpi = 300)
        showNotification(paste("Plot saved to:", full_path), type = "message")
      }
    )

  # UI Stuff
  observe({
    # Conditional logic to change textInput default value
    if (input$parang_paraORdist == "closest to the center (medoids)") {
      updateTextInput(session, "plot_title_parang", value = "Factor map - medoids only")
    } else if (input$parang_paraORdist == "farthest from other clusters") {
      updateTextInput(session, "plot_title_parang", value = "Factor map - representatives farthest from other clusters only")
    } else if (input$parang_paraORdist == "variable associated by v-test") {
      updateTextInput(session, "plot_title_parang", value = "Factor map - variables associated by v-test only")
    }
  })

# ------------- Cascading dropdown updates -------------

  observeEvent(input$dataset_select_metadata, {
    cands <- get_candidates(meta=input$dataset_select_metadata)
    reps <- extract_reps(cands)
    updateSelectInput(session, "dataset_select_representation", choices=reps, selected=reps[1])
  }, ignoreInit=TRUE)

  observeEvent(input$dataset_select_representation, {
    meta <- input$dataset_select_metadata
    rep  <- input$dataset_select_representation
    cands <- get_candidates(meta=meta, rep=rep)
    early_opts <- extract_early(cands)
    updateSelectInput(session, "dataset_select_early",
      choices = c("No (all tokens)", early_opts),
      selected = "No (all tokens)"
    )
    if (grepl("motif", rep, ignore.case=TRUE)) {
      cands_ne <- get_candidates(meta=meta, rep=rep, early="No (all tokens)")
      vals <- extract_minsup(cands_ne)
      updateSelectInput(session, "dataset_select_minsup", choices=vals, selected=vals[1])
    }
  }, ignoreInit=TRUE)

  observeEvent(input$dataset_select_early, {
    if (!grepl("motif", input$dataset_select_representation, ignore.case=TRUE)) return()
    cands <- get_candidates(meta=input$dataset_select_metadata, rep=input$dataset_select_representation, early=input$dataset_select_early)
    vals <- extract_minsup(cands)
    updateSelectInput(session, "dataset_select_minsup", choices=vals, selected=vals[1])
  }, ignoreInit=TRUE)

  observeEvent(input$dataset_select_minsup, {
    if (!grepl("motif", input$dataset_select_representation, ignore.case=TRUE)) return()
    cands <- get_candidates(meta=input$dataset_select_metadata, rep=input$dataset_select_representation, early=input$dataset_select_early, minsup=input$dataset_select_minsup)
    vals <- extract_gapmin(cands)
    updateSelectInput(session, "dataset_select_gapmin", choices=vals, selected=vals[1])
  }, ignoreInit=TRUE)

  observeEvent(input$dataset_select_gapmin, {
    if (!grepl("motif", input$dataset_select_representation, ignore.case=TRUE)) return()
    cands <- get_candidates(meta=input$dataset_select_metadata, rep=input$dataset_select_representation, early=input$dataset_select_early, minsup=input$dataset_select_minsup, gapmin=input$dataset_select_gapmin)
    vals <- extract_gapmax(cands)
    updateSelectInput(session, "dataset_select_gapmax", choices=vals, selected=vals[1])
  }, ignoreInit=TRUE)

  observeEvent(input$dataset_select_gapmax, {
    if (!grepl("motif", input$dataset_select_representation, ignore.case=TRUE)) return()
    cands <- get_candidates(meta=input$dataset_select_metadata, rep=input$dataset_select_representation, early=input$dataset_select_early, minsup=input$dataset_select_minsup, gapmin=input$dataset_select_gapmin, gapmax=input$dataset_select_gapmax)
    vals <- extract_itemsetmin(cands)
    updateSelectInput(session, "dataset_select_itemsetmin", choices=vals, selected=vals[1])
  }, ignoreInit=TRUE)

df_select_concatenated <- reactive({
  metadata_select <- req(input$dataset_select_metadata)
  representation_select <- req(input$dataset_select_representation)

  if (grepl("motif", representation_select, ignore.case = TRUE)) {
    minsup_select        <- as.character(req(input$dataset_select_minsup))
    gapmin_select        <- as.character(req(input$dataset_select_gapmin))
    gapmax_select        <- as.character(req(input$dataset_select_gapmax))
    itemsetmin_select    <- as.character(req(input$dataset_select_itemsetmin))
    early_select         <- input$dataset_select_early

    suffix <- paste(minsup_select, gapmin_select, gapmax_select, itemsetmin_select, sep = "_")

    candidates <- names(datasets)
    candidates <- candidates[startsWith(candidates, paste0(metadata_select, "_"))]
    candidates <- candidates[grepl("motif", candidates, ignore.case = TRUE)]
    candidates <- candidates[endsWith(candidates, suffix)]

    if (!is.null(early_select) && early_select != "No (all tokens)")
      candidates <- candidates[grepl(paste0("earlySelectionTrue", early_select), candidates, fixed = TRUE)]

    df <- candidates[1]
  } else {
    df <- paste(metadata_select, representation_select, sep = "_")
  }

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
                choices = names(datasets),            # populate dropdown with keys
                selected = names(datasets)[1]
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
              conditionalPanel(
                condition = "output.has_specifs_df == 'TRUE'",
                selectInput(
                  inputId = "dataset_select_early",
                  label = tooltip(
                      trigger = list(
                        "Specificity filter",
                        bs_icon("info-circle")
                      ),
                      HTML("Depending on your settings, MWB produced datasets by:
                        <div style='text-align: left;'>
                          <ul>
                            <li>only mining specific tokens, or</li>
                            <li>mining all tokens.</li>
                          </ul>
                        </div>
                        Argument 'No (all tokens)' refers to the second choice.")
                    ),
                  choices = c("No (all tokens)", early_list),            # populate dropdown with keys
                  selected = "No (all tokens)",
                  selectize = TRUE
                ),
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
          conditionalPanel(condition = "input.tabselected == 'CA'",
            checkboxInput("contrib_threshold", "Apply minimal contrib. threshold", value=TRUE),
              conditionalPanel(
                condition = "input.contrib_threshold == true",
                sliderInput(
                  "contrib_vars",
                  label = HTML("<i>N</i>-th most contributing cols"),
                  min = 1,
                  max = 100,
                  value = 10,
                  step = 5
                ),
                sliderInput(
                  "contrib_rows",
                  label = HTML("<i>N</i>-th most contributing rows"),
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
            textInput("plot_title_CA", "Plot Title:", value = "CA - Biplot"),
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
              selectInput(
                "cluster_row_or_col",
                "Select dimension:",
                choices = c("rows", "columns"),
                selected = "rows"
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
              selectInput(
                "parang_paraORdist",
                "Select representatives:",
                choices = c(HTML("closest to the center (medoids)"), HTML("farthest from other clusters"), HTML("variable associated by v-test")),
                selected = "closest to the center (medoids)"
              ),
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
        ),
      # )
    ),
    
    # navset_pill(
    #   id = "tabselected",
        nav_panel(
          "CA",
          value = 'CA',
          # p("text"),
          card(plotOutput("CAplot", height = "700px"))
        ),
        nav_panel(
          "CA Scree Plot",
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
            textOutput("cluster_error_msg_hcpc")
          )
        ),
        nav_panel(
          "Clusters representatives",
          value = "parang_panel",
          card(
            plotOutput("CA_clusters_plot"),
            textOutput("cluster_error_msg_parang"),
            card_footer("Depending on data size, clusters' representatives computation may take some time.")
          )
        ),
        nav_panel(
          "Data",
            fluidRow(
              card(
                h4("Contingency table"),
                column(
                  width = 12,
                  DTOutput("data_table")
                ))
            )
        ),
      # ),

      theme = bslib::bs_theme(),

    )


#-------------------------------
# RUN SHINY APP
#-------------------------------
# At the bottom of Shiny_CA.R
shiny::runApp(list(ui = ui, server = server),
              launch.browser = TRUE, host = getOption("shiny.host", "127.0.0.1"))

