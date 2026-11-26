#--------------------------------------------------------------
# CQP_concordancer.r
# KWIC concordancer backend (CWB/CQP) for the MWB Shiny interface
#
# Meant to be sourced from Shiny_CA.R:
#   source(file.path(dirname(script_path), "CQP_concordancer.r"))
#
# Not wired into Shiny_CA.R yet. This file provides:
#   1. Locating cqp and the CWB registry of the current analysis
#   2. Building CQP queries (word / lemma / POS / raw, table labels, motifs)
#   3. Running CQP and parsing its output into a data.frame
#   4. Helpers for metadata, distribution and sorting
#   5. A minimal Shiny module (UI + server) to plug into a nav_panel
#
# Only base R + shiny + DT (already in Shiny_CA.R's package list).
#--------------------------------------------------------------


#--------------------------------------------------------------
# 1. Locating cqp and the registry
#--------------------------------------------------------------

# Path to the cqp executable. Only *executable* candidates are kept (the
# project's bin/cqp wrapper is not executable in the repo, and its Docker
# fallback would not see the registry path anyway): PATH, then the usual
# Homebrew / system locations, then bin/. Returns "" if not found.
cqp_find_binary <- function(project_root = getwd()) {
  exe <- if (.Platform$OS.type == "windows") "cqp.exe" else "cqp"
  wrapper <- file.path(project_root, "bin", exe)
  candidates <- c(unname(Sys.which(exe)),
                  file.path(c("/opt/homebrew/bin", "/usr/local/bin", "/usr/bin"), exe))
  for (p in candidates) {
    if (nzchar(p) && file.exists(p) && file.access(p, 1) == 0 &&
        normalizePath(p) != normalizePath(wrapper, mustWork = FALSE)) return(normalizePath(p))
  }
  # Fallback: the project's wrapper (run through bash by cqp_run(); it uses Docker)
  if (file.exists(wrapper)) return(normalizePath(wrapper))
  ""
}

# CWB registry directory of an analysis.
# Priority: path given in shiny_context.json ("registry_path" key, to be added
# on the Python side), then <analysis_root>/cwb-corpus/registry.
cqp_registry_dir <- function(analysis_root, context = NULL) {
  candidates <- c(
    if (!is.null(context) && !is.null(context$registry_path)) context$registry_path,
    file.path(analysis_root, "cwb-corpus", "registry")
  )
  for (p in candidates) {
    if (!is.null(p) && nzchar(p) && file.exists(file.path(p, "merged"))) {
      return(normalizePath(p))
    }
  }
  ""
}

cqp_is_ready <- function(registry, cqp_bin) {
  nzchar(registry) && nzchar(cqp_bin) && file.exists(file.path(registry, "merged"))
}


#--------------------------------------------------------------
# 2. Building queries
#--------------------------------------------------------------

# Escape CQP regex metacharacters so that a value is matched literally.
# (Equivalent to the %l flag, but works inside multi-condition tokens.)
cqp_escape_regex <- function(value) {
  gsub("([\\\\.^$|?*+()\\[\\]{}])", "\\\\\\1", value, perl = TRUE)
}

# Quote a value for CQP. Uses "..." unless the value contains a double quote,
# in which case '...' is used. (Values containing both are rejected.)
cqp_quote <- function(value) {
  if (!grepl('"', value, fixed = TRUE)) return(paste0('"', value, '"'))
  if (!grepl("'", value, fixed = TRUE)) return(paste0("'", value, "'"))
  stop("Value contains both single and double quotes: ", value)
}

# One condition: attr="value" (literal by default), optional %c (ignore case)
cqp_condition <- function(attr, value, literal = TRUE, ignore_case = FALSE) {
  v <- if (literal) cqp_escape_regex(value) else value
  paste0(attr, "=", cqp_quote(v), if (ignore_case) " %c" else "")
}

# One token: [attr="value"]
cqp_token <- function(attr, value, literal = TRUE, ignore_case = FALSE) {
  paste0("[", cqp_condition(attr, value, literal, ignore_case), "]")
}

# Simple search box: mode = "word", "lemma", "pos" or "cqp" (raw query).
# Several space-separated words in word/lemma mode = a sequence of tokens.
cqp_query_from_input <- function(text, mode = c("word", "lemma", "pos", "cqp"),
                                 ignore_case = TRUE) {
  mode <- match.arg(mode)
  text <- trimws(text)
  if (!nzchar(text)) stop("Empty query.")
  if (mode == "cqp") return(cqp_validate_raw(text))
  if (mode == "pos") return(cqp_token("pos", toupper(text), literal = TRUE))
  words <- strsplit(text, "\\s+")[[1]]
  paste(vapply(words, function(w) cqp_token(mode, w, TRUE, ignore_case), ""), collapse = " ")
}

# A raw query must be a single CQP query: no ';' or newline, otherwise a user
# could chain other CQP commands (e.g. redirect output to a file).
cqp_validate_raw <- function(query) {
  query <- sub(";\\s*$", "", trimws(query))
  if (grepl("[;\r\n]", query)) stop("A raw CQP query cannot contain ';' or line breaks.")
  query
}

# Port of tools.read_req_CQP(): motif string -> CQP query.
#   {lemma_"monsieur",pos_"NOUN"} {pos="VERB"}  ->  [lemma="monsieur" & pos="NOUN"] [pos="VERB"]
# literal = FALSE reproduces the Python behaviour exactly (values used as regex),
# which is what the frequency tables were computed with.
cqp_query_from_motif <- function(motif, literal = FALSE) {
  m <- gregexpr("\\{[^}]+\\}", motif, perl = TRUE)
  regmatches(motif, m) <- list(vapply(regmatches(motif, m)[[1]], function(block) {
    inner <- substr(block, 2, nchar(block) - 1)
    items <- strsplit(inner, '(?<!_),(?=(?:[^"]*"[^"]*")*[^"]*$)', perl = TRUE)[[1]]
    conds <- vapply(items, function(item) {
      if (grepl("_", item, fixed = TRUE) && !grepl("=", item, fixed = TRUE)) {
        key <- sub("_.*$", "", item); value <- sub("^[^_]*_", "", item)
      } else {
        key <- sub("=.*$", "", item); value <- sub("^[^=]*=", "", item)
      }
      value <- gsub('^"+|"+$', "", value)
      cqp_condition(trimws(key), value, literal = literal)
    }, "")
    paste0("[", paste(conds, collapse = " & "), "]")
  }, ""))
  motif
}

# Row label of a contingency table -> CQP query, based on the dataset name
# (names of results_for_shiny.json, e.g. "id_pos", "id_100lemmaADJ|ADV|NOUN|VERB",
# "id_100bigramslemma", motif tables).
# literal = FALSE matches how the tables were counted (see compute_CQP.py);
# literal = TRUE is more correct for labels such as "." or "-".
cqp_query_from_label <- function(label, dataset_name, literal = FALSE) {
  if (grepl("\\{[^}]+\\}", label)) return(cqp_query_from_motif(label, literal))
  if (grepl("bigrams", dataset_name, fixed = TRUE)) {
    attr <- if (grepl("pos", dataset_name, fixed = TRUE)) "pos" else "lemma"
    parts <- strsplit(label, " ", fixed = TRUE)[[1]]
    return(paste(vapply(parts, function(p) cqp_token(attr, p, literal), ""), collapse = " "))
  }
  if (grepl("lemma", dataset_name, fixed = TRUE)) return(cqp_token("lemma", label, literal))
  if (grepl("pos", dataset_name, fixed = TRUE)) return(cqp_token("pos", label, literal))
  stop("Cannot build a CQP query for label '", label, "' (dataset ", dataset_name, ").")
}


#--------------------------------------------------------------
# 3. Running CQP
#--------------------------------------------------------------

CQP_EOL <- "-::-EOL-::-"   # printed by the ".EOL.;" command in child mode (-c)

# Run a vector of CQP commands (without ';') in child mode.
# Returns the stdout lines; stops with CQP's error message on failure.
cqp_run <- function(commands, registry, cqp_bin, timeout = 30) {
  if (!cqp_is_ready(registry, cqp_bin)) stop("CQP or the CWB registry is not available.")
  script <- tempfile(fileext = ".cqp"); out <- tempfile(); err <- tempfile()
  on.exit(unlink(c(script, out, err)), add = TRUE)
  writeLines(c(paste0(commands, ";"), "exit;"), script, useBytes = TRUE)

  # bin/cqp is a bash wrapper stored without the execute bit: run it through bash
  cmd <- cqp_bin; cmd_args <- c("-c", "-r", shQuote(registry))
  first_line <- tryCatch(readLines(cqp_bin, n = 1, warn = FALSE), error = function(e) "")
  if (length(first_line) && startsWith(first_line, "#!")) {
    cmd <- "bash"; cmd_args <- c(shQuote(cqp_bin), cmd_args)
  }
  status <- system2(cmd, cmd_args,
                    stdin = script, stdout = out, stderr = err, timeout = timeout)
  if (identical(status, 124L)) stop("CQP timed out after ", timeout, " s.")
  lines <- readLines(out, encoding = "UTF-8", warn = FALSE)
  errors <- readLines(err, encoding = "UTF-8", warn = FALSE)
  errors <- errors[nzchar(trimws(errors))]
  # CQP still prints the .EOL. markers after a failed command: report its errors anyway
  if (length(errors) > 0 && (!any(lines == CQP_EOL) || any(grepl("error", errors, ignore.case = TRUE)))) {
    stop("CQP error: ", paste(errors, collapse = " "))
  }
  lines
}

# Split CQP output into the blocks delimited by .EOL. markers
cqp_blocks <- function(lines) {
  lines <- lines[!grepl("^CQP version", lines)]
  ends <- which(lines == CQP_EOL)
  starts <- c(1, head(ends, -1) + 1)
  Map(function(s, e) if (e > s) lines[s:(e - 1)] else character(0), starts, ends)
}

# Main entry point: KWIC concordance of a CQP query.
#   query     : CQP query (see section 2)
#   context   : number of tokens left and right
#   show_attr : positional attribute(s) shown in the concordance, e.g. "word",
#               "lemma", or c("word", "pos") -> "house/NOUN"
#   max_hits  : maximum number of lines returned (total is still reported)
#   sample    : TRUE = random sample of max_hits lines, FALSE = first ones
#   text_ids  : optional vector of text_id to restrict the search to
# Returns list(total = <int>, hits = data.frame(text_id, left, kwic, right,
#              match, left_sort)), where `match` is the corpus position.
cqp_concordance <- function(query, registry, cqp_bin, context = 10,
                            show_attr = "word", max_hits = 1000, sample = FALSE,
                            text_ids = NULL, corpus = "MERGED", timeout = 30) {
  context <- suppressWarnings(as.integer(context))
  if (length(context) != 1 || is.na(context)) context <- 10L
  context <- max(0L, context)
  max_hits <- suppressWarnings(as.integer(max_hits))
  if (length(max_hits) != 1 || is.na(max_hits)) max_hits <- 0L
  cmds <- c(corpus, "set PrettyPrint off")

  # Optional restriction to some texts: build a subcorpus of whole texts.
  # NOTE: untested against the bundled CWB version.
  if (length(text_ids) > 0) {
    ids <- paste(cqp_escape_regex(text_ids), collapse = "|")
    cmds <- c(cmds,
              paste0("Texts = <text> [] :: match.text_id=", cqp_quote(ids), " expand to text"),
              "Texts")
  }

  cmds <- c(cmds,
            paste0("Pattern = ", query),
            "size Pattern", ".EOL.",
            if (max_hits > 0) paste(if (sample) "reduce Pattern to" else "cut Pattern", max_hits))

  # One tabulate per attribute: text_id, corpus position, left / KWIC / right
  for (a in show_attr) {
    k <- max(1L, context)   # context = 0: fetch 1 token, blanked when parsing
    ranges <- c(
      sprintf("match[-%d]..match[-1] %s", k, a),
      sprintf("match..matchend %s", a),
      sprintf("matchend[1]..matchend[%d] %s", k, a)
    )
    cmds <- c(cmds, paste("tabulate Pattern match text_id, match,", paste(ranges, collapse = ", ")), ".EOL.")
  }

  blocks <- cqp_blocks(cqp_run(cmds, registry, cqp_bin, timeout))
  if (length(blocks) < 1 + length(show_attr)) stop("Unexpected CQP output.")
  total <- suppressWarnings(as.integer(trimws(blocks[[1]][1])))

  tables <- lapply(blocks[-1], cqp_parse_tabulate, context = context)
  hits <- tables[[1]]
  if (length(tables) > 1 && nrow(hits) > 0) {
    for (col in c("left", "kwic", "right")) {
      hits[[col]] <- do.call(cqp_zip_tokens, lapply(tables, `[[`, col))
    }
  }
  hits$left_sort <- cqp_reverse_tokens(tables[[1]]$left)   # for sorting on left context
  list(total = if (is.na(total)) nrow(hits) else total, hits = hits)
}

# tabulate output: text_id \t cpos \t left \t kwic \t right (tokens space-separated)
cqp_parse_tabulate <- function(lines, context = 10) {
  empty <- data.frame(text_id = character(0), match = integer(0), left = character(0),
                      kwic = character(0), right = character(0), stringsAsFactors = FALSE)
  lines <- lines[nzchar(lines)]
  if (length(lines) == 0) return(empty)
  f <- strsplit(lines, "\t", fixed = TRUE)
  f <- lapply(f, function(x) c(x, rep("", 5 - length(x)))[1:5])
  m <- do.call(rbind, f)
  out <- data.frame(text_id = m[, 1], match = as.integer(m[, 2]),
                    left = m[, 3], kwic = m[, 4], right = m[, 5],
                    stringsAsFactors = FALSE)
  if (context == 0) { out$left <- ""; out$right <- "" }
  out
}

# Combine attributes token by token: "the house" + "DET NOUN" -> "the/DET house/NOUN"
cqp_zip_tokens <- function(...) {
  cols <- list(...)
  vapply(seq_along(cols[[1]]), function(i) {
    toks <- lapply(cols, function(x) strsplit(x[i], " ", fixed = TRUE)[[1]])
    n <- min(lengths(toks))
    if (n == 0) return("")
    paste(do.call(paste, c(lapply(toks, `[`, seq_len(n)), sep = "/")), collapse = " ")
  }, "")
}

# Keep only k tokens of a context: the last ones (left context) or the first ones (right)
cqp_trim_tokens <- function(x, k, from_end = FALSE) {
  if (k <= 0) return(rep("", length(x)))
  vapply(strsplit(x, " ", fixed = TRUE), function(t) {
    n <- length(t)
    if (n <= k) return(paste(t, collapse = " "))
    paste(if (from_end) t[(n - k + 1):n] else t[1:k], collapse = " ")
  }, "")
}

cqp_reverse_tokens <- function(x) {
  vapply(strsplit(x, " ", fixed = TRUE), function(t) paste(rev(t), collapse = " "), "")
}


#--------------------------------------------------------------
# 4. Metadata and distribution
#--------------------------------------------------------------

# Load the analysis metadata table (same lookup order as Shiny_CA.R):
# <analysis_root>/metadata.tsv, then shiny_context$metadata_path, then the
# path_metadata of analysis_info.json. Returns NULL if none is found.
cqp_load_metadata <- function(analysis_root, context = NULL) {
  resolve <- function(p, root) if (grepl("^(/|[A-Za-z]:[/\\\\])", p)) p else file.path(root, p)
  path <- file.path(analysis_root, "metadata.tsv")
  if (!file.exists(path) && !is.null(context$metadata_path)) {
    path <- resolve(context$metadata_path, analysis_root)
  }
  info <- file.path(analysis_root, "analysis_info.json")
  if (!file.exists(path) && file.exists(info)) {
    configured <- tryCatch(jsonlite::fromJSON(info)$config$path_metadata, error = function(e) NULL)
    if (!is.null(configured)) path <- resolve(configured, getwd())
  }
  if (!file.exists(path)) return(NULL)
  meta <- tryCatch(read.delim(path, colClasses = "character", check.names = FALSE),
                   error = function(e) NULL)
  if (is.null(meta) || ncol(meta) == 0) return(NULL)
  names(meta)[1] <- "text_id"   # first column holds the text ids
  meta
}

# Add metadata columns (metadata.tsv) to the hits, keeping the hits' order.
# Ids are matched exactly, then on their file stem (as the Python GUI does:
# "ca01" matches "ca01.txt"). `by` = metadata id column (default: text_id/id/first).
cqp_add_metadata <- function(hits, metadata, by = NULL) {
  if (is.null(metadata) || nrow(hits) == 0) return(hits)
  if (is.null(by)) {
    by <- intersect(c("text_id", "id"), names(metadata))[1]
    if (is.na(by)) by <- names(metadata)[1]
  }
  ids <- as.character(metadata[[by]])
  stem <- function(x) tools::file_path_sans_ext(basename(x))
  idx <- match(hits$text_id, ids)
  miss <- is.na(idx)
  if (any(miss)) idx[miss] <- match(stem(hits$text_id[miss]), stem(ids))
  meta <- metadata[idx, setdiff(names(metadata), by), drop = FALSE]
  meta <- meta[, setdiff(names(meta), names(hits)), drop = FALSE]
  rownames(meta) <- NULL
  cbind(hits, meta)
}

# Number of hits per value of a column (text_id or a metadata column).
# Pass `sizes` (named vector: value -> number of tokens) to also get
# a relative frequency per 10,000 tokens.
cqp_count_by <- function(hits, column = "text_id", sizes = NULL) {
  if (nrow(hits) == 0) return(data.frame(value = character(0), n = integer(0)))
  values <- as.character(hits[[column]])
  values[is.na(values) | !nzchar(trimws(values))] <- "(empty)"
  tab <- as.data.frame(table(value = values), stringsAsFactors = FALSE)
  names(tab)[2] <- "n"
  if (!is.null(sizes)) tab$per_10k <- 1e4 * tab$n / sizes[tab$value]
  tab[order(tab$value), , drop = FALSE]
}


#--------------------------------------------------------------
# 5. Saved motifs (closed patterns / medoids of the analysis)
#--------------------------------------------------------------
# Motifs are stored as Python pickles, so they are exported to JSON by
# src/export_closed_patterns.py, run with the project's virtualenv Python.

cqp_python_bin <- function(project_root = getwd()) {
  candidates <- c(file.path(project_root, ".venv", "bin", "python"),
                  file.path(project_root, ".venv", "Scripts", "python.exe"),
                  unname(Sys.which("python3")), unname(Sys.which("python")))
  for (p in candidates) if (nzchar(p) && file.exists(p)) return(p)
  ""
}

# Returns list(source_file, patterns = data.frame(id, display, cqp_pattern)).
# Stops with a readable message on failure.
cqp_load_saved_motifs <- function(analysis_root, project_root = getwd(), timeout = 120) {
  py <- cqp_python_bin(project_root)
  if (!nzchar(py)) stop("Python was not found (needed to read the saved motifs).")
  script <- file.path(project_root, "src", "export_closed_patterns.py")
  if (!file.exists(script)) stop("src/export_closed_patterns.py is missing.")
  out <- tempfile(fileext = ".json"); err <- tempfile()
  on.exit(unlink(c(out, err)), add = TRUE)
  status <- system2(py, c(shQuote(script), shQuote(analysis_root), shQuote(out)),
                    stdout = err, stderr = err, timeout = timeout)
  if (!identical(status, 0L) || !file.exists(out)) {
    msg <- paste(tail(readLines(err, warn = FALSE), 3), collapse = " ")
    stop("Could not load the saved motifs. ", msg)
  }
  res <- jsonlite::fromJSON(out, simplifyDataFrame = TRUE)
  pats <- res$patterns
  if (length(pats) == 0 || NROW(pats) == 0) {
    pats <- data.frame(id = integer(0), display = character(0), cqp_pattern = character(0))
  }
  list(source_file = res$source_file %||% "", patterns = as.data.frame(pats, stringsAsFactors = FALSE))
}

# "motif" or "words", from the Python GUI's settings (logs/app_settings.json)
cqp_default_display_mode <- function(project_root = getwd()) {
  f <- file.path(project_root, "logs", "app_settings.json")
  mode <- tryCatch(jsonlite::fromJSON(f)$closed_pattern_display_mode, error = function(e) NULL)
  if (identical(mode, "words")) "words" else "motif"
}


#--------------------------------------------------------------
# 6. Shiny module (same search functions as the Python GUI concordancer)
#--------------------------------------------------------------
# In the UI:      nav_panel("Concordances", value = "concordances",
#                           cqp_concordancer_ui("conc", registry, cqp_bin))
# In the server:  conc <- cqp_concordancer_server("conc", registry, cqp_bin,
#                           metadata = metadata_df, analysis_root = analysis_root,
#                           project_root = project_root)
#                 # from elsewhere (plot click...): conc$search(cqp_query_from_label(label, dataset_name))

CQP_NO_FILTER <- "(No filter)"
CQP_ALL_VALUES <- "(All values)"

cqp_concordancer_ui <- function(id, registry = "", cqp_bin = "") {
  ns <- NS(id)
  ready <- cqp_is_ready(registry, cqp_bin)
  tagList(
    # Enter in the query box launches the search
    tags$script(HTML(sprintf(
      "$(document).on('keyup', '#%s', function(e){ if (e.key === 'Enter') $('#%s').click(); });",
      ns("query"), ns("run")))),
    # Changing the context size redraws the table at once (trimming is done in the browser)
    tags$script(HTML(sprintf(
      "$(document).on('input change', '#%s', function() {
         var tbl = $('#%s table.dataTable');
         if (tbl.length && $.fn.dataTable.isDataTable(tbl[0])) tbl.DataTable().rows().invalidate('data').draw(false);
       });", ns("context"), ns("table")))),

    div(class = "small mb-2",
        "CWB registry: ",
        tags$b(style = if (ready) "color:#166534;" else "color:#b91c1c;",
               if (ready) "Available" else "Not found"),
        if (!nzchar(cqp_bin)) tags$b(style = "color:#b91c1c;", " (cqp not found)"),
        br(), tags$span(class = "text-muted", if (nzchar(registry)) registry else "-")),

    fluidRow(
      column(3, selectInput(ns("mode"), "Mode",
                            c("Free search" = "free", "Saved motifs" = "motifs", "CQP" = "cqp"))),
      column(3, conditionalPanel("input.mode == 'motifs'", ns = ns,
        selectInput(ns("display"), "Display",
                    c("Motifs" = "motif", "Matching words" = "words")))),
      column(2, numericInput(ns("context"), "Context (tokens)", 10, min = 0, max = 50)),
      column(2, numericInput(ns("max_hits"), "Max. hits", 10000, min = 10, max = 1e6, step = 1000)),
      column(2, checkboxGroupInput(ns("show_attr"), "Show", c("word", "lemma", "pos"),
                                   selected = "word", inline = TRUE))
    ),

    conditionalPanel("input.mode == 'motifs'", ns = ns,
      helpText(tags$i("Double-click a motif (or select it and click 'Show concordances') to display its concordances.")),
      # (wrapped in a plain div: as a "fill" item of the card, a table can be squeezed
      # to 0 px height, and DT then postpones drawing it)
      div(DT::DTOutput(ns("motif_list"))),
      fluidRow(
        column(8, div(class = "small text-muted mt-2", textOutput(ns("motif_info")))),
        column(4, actionButton(ns("run_motif"), "Show concordances", icon = icon("magnifying-glass"),
                               class = "btn-primary mt-2", style = "width: 100%;"))
      )
    ),
    conditionalPanel("input.mode != 'motifs'", ns = ns,
      fluidRow(
        column(9, textInput(ns("query"), NULL, width = "100%",
                            placeholder = "Enter a term to search...")),
        column(3, actionButton(ns("run"), "Search", icon = icon("magnifying-glass"),
                               class = "btn-primary", style = "width: 100%;"))
      ),
      conditionalPanel("input.mode == 'free'", ns = ns,
        radioButtons(ns("search_type"), "Search type",
                     c("Word" = "word", "Lemma" = "lemma", "Category (POS)" = "pos"),
                     inline = TRUE))
    ),

    hr(),
    fluidRow(
      column(3, selectInput(ns("filter_col"), "Filter by", CQP_NO_FILTER)),
      column(3, selectInput(ns("filter_val"), "Value", CQP_ALL_VALUES)),
      column(2, selectInput(ns("order"), "Order", c("A → Z" = "asc", "Z → A" = "desc"))),
      column(4, br(),
             downloadButton(ns("export"), "Export CSV", class = "btn-primary"),
             actionButton(ns("distribution"), "Distribution", icon = icon("chart-bar"),
                          class = "btn-primary"))
    ),
    tags$b(textOutput(ns("summary"))),
    div(style = "min-height: 60px;", DT::DTOutput(ns("table")))
  )
}

cqp_concordancer_server <- function(id, registry, cqp_bin, metadata = NULL,
                                    analysis_root = NULL, project_root = getwd()) {
  moduleServer(id, function(input, output, session) {
    ns <- session$ns
    result <- reactiveVal(NULL)     # list(total, hits, query, motif)
    motifs <- reactiveVal(NULL)     # list(source_file, patterns)
    meta_cols <- if (is.null(metadata)) character(0) else setdiff(names(metadata), c("text_id", "id"))

    notify_error <- function(e) showNotification(conditionMessage(e), type = "error", duration = 8)

    # ---- Initial state ----
    updateSelectInput(session, "display", selected = cqp_default_display_mode(project_root))
    updateSelectInput(session, "filter_col", choices = c(CQP_NO_FILTER, meta_cols))

    observeEvent(input$mode, {
      updateTextInput(session, "query", placeholder = if (input$mode == "cqp")
        'CQP query, e.g. [lemma="faire"] []{0,3} [pos="NOUN"]' else "Enter a term to search...")
      if (input$mode == "motifs" && is.null(motifs()) && !is.null(analysis_root)) {
        withProgress(message = "Loading saved motifs...", value = 0.5, {
          m <- tryCatch(cqp_load_saved_motifs(analysis_root, project_root),
                        error = function(e) { notify_error(e); NULL })
        })
        if (!is.null(m)) motifs(m)
      }
    })

    # ---- Saved motifs list ----
    output$motif_list <- DT::renderDT({
      m <- req(motifs())
      DT::datatable(
        data.frame(Motif = m$patterns$display, stringsAsFactors = FALSE),
        rownames = FALSE, selection = "single",
        options = list(pageLength = 8, lengthChange = FALSE, dom = "ftip",
                       language = list(search = "Filter motifs:")),
        callback = DT::JS(sprintf(
          "table.on('dblclick', 'tbody tr', function() {
             var i = table.row(this).index();
             if (i !== undefined) Shiny.setInputValue('%s', i + 1, {priority: 'event'});
           });", ns("motif_dblclick")))
      )
    }, server = FALSE)   # client-side: row().index() is then the motif's real index, even when filtered or paged
    output$motif_info <- renderText({
      m <- motifs()
      if (is.null(m) || nrow(m$patterns) == 0) "No usable motif was found for this analysis."
      else sprintf("%d motif(s) loaded from %s.", nrow(m$patterns), m$source_file)
    })

    # ---- Running a search ----
    # Context is fetched once with a margin (at least CQP_PREFETCH tokens) and
    # trimmed in R, so changing the context size is instant; CQP is only
    # queried again when the requested context exceeds what was fetched.
    CQP_PREFETCH <- 20L
    requested_context <- function() {
      k <- suppressWarnings(as.integer(input$context))
      if (length(k) != 1 || is.na(k)) 10L else max(0L, k)
    }

    run_query <- function(query, motif = NULL) {
      fetch <- max(requested_context(), CQP_PREFETCH)
      res <- tryCatch(
        withProgress(message = "Searching...", value = 0.5,
          cqp_concordance(query, registry, cqp_bin,
                          context = fetch,
                          show_attr = if (length(input$show_attr)) input$show_attr else "word",
                          max_hits = input$max_hits %||% 10000)),
        error = function(e) { notify_error(e); NULL })
      if (is.null(res)) return(invisible(NULL))
      res$hits <- cqp_add_metadata(res$hits, metadata)
      res$query <- query
      res$motif <- motif
      res$fetched_context <- fetch
      result(res)
      if (res$total == 0) showNotification("No occurrence found.", type = "warning")
      invisible(res)
    }

    # Changing the context size, the shown attributes or the hit limit re-runs
    # the current search right away (debounced while typing in the number fields)
    # (an empty or invalid number field, e.g. while retyping it, is ignored)
    valid_number <- function(x) length(x) == 1 && !is.na(x) && is.numeric(x)
    display_settings <- debounce(reactive(list(input$show_attr, input$max_hits)), 400)
    observeEvent(display_settings(), {
      if (!valid_number(input$max_hits)) return()
      res <- isolate(result())
      if (!is.null(res)) run_query(res$query, motif = res$motif)
    }, ignoreInit = TRUE)
    # Context: re-query CQP only if more context than fetched is requested
    context_d <- debounce(reactive(input$context), 400)
    observeEvent(context_d(), {
      res <- isolate(result())
      if (!is.null(res) && valid_number(input$context) && requested_context() > res$fetched_context) {
        run_query(res$query, motif = res$motif)
      }
    }, ignoreInit = TRUE)

    observeEvent(input$run, {
      q <- tryCatch(
        if (input$mode == "cqp") cqp_query_from_input(input$query, "cqp")
        else cqp_query_from_input(input$query, input$search_type),
        error = function(e) { notify_error(e); NULL })
      if (!is.null(q)) run_query(q)
    })

    run_motif <- function(i) {
      m <- motifs()
      if (is.null(m) || is.null(i) || i < 1 || i > nrow(m$patterns)) {
        showNotification("Please select a motif first.", type = "warning"); return()
      }
      run_query(m$patterns$cqp_pattern[i], motif = m$patterns$display[i])
    }
    observeEvent(input$run_motif, run_motif(input$motif_list_rows_selected))
    observeEvent(input$motif_dblclick, run_motif(input$motif_dblclick))

    # ---- Filter & sort ----
    observeEvent(list(result(), input$filter_col), {
      res <- result(); col <- input$filter_col
      values <- if (!is.null(res) && !identical(col, CQP_NO_FILTER) && col %in% names(res$hits)) {
        v <- trimws(as.character(res$hits[[col]])); sort(unique(v[!is.na(v) & nzchar(v)]))
      } else character(0)
      keep <- if (isolate(input$filter_val) %in% values) isolate(input$filter_val) else CQP_ALL_VALUES
      updateSelectInput(session, "filter_val", choices = c(CQP_ALL_VALUES, values), selected = keep)
    })

    displayed <- reactive({
      res <- req(result())
      hits <- res$hits
      if (!is.null(res$motif) && identical(input$display, "motif") && nrow(hits) > 0) {
        hits$kwic <- res$motif
      }
      col <- input$filter_col
      use_col <- !is.null(col) && !identical(col, CQP_NO_FILTER) && col %in% names(hits)
      if (use_col && !identical(input$filter_val, CQP_ALL_VALUES)) {
        hits <- hits[trimws(as.character(hits[[col]])) %in% input$filter_val, , drop = FALSE]
      }
      key <- tolower(trimws(as.character(if (use_col) hits[[col]] else hits$text_id)))
      key[is.na(key)] <- ""
      hits[order(key, decreasing = identical(input$order, "desc"), method = "radix"), , drop = FALSE]
    })

    output$summary <- renderText({
      res <- req(result()); n <- nrow(displayed())
      txt <- sprintf("%d result(s) displayed / %d occurrence(s) found.", n, res$total)
      if (nrow(res$hits) < res$total) {
        txt <- paste(txt, sprintf("Only the first %d were retrieved (see 'Max. hits').", nrow(res$hits)))
      }
      txt
    })

    # Columns shown / exported, in the Python GUI's order
    table_view <- function(hits) {
      out <- data.frame(left_context = hits$left, keyword = hits$kwic,
                        right_context = hits$right, source = hits$text_id,
                        stringsAsFactors = FALSE)
      extra <- intersect(meta_cols, names(hits))
      if (length(extra)) out <- cbind(out, hits[, extra, drop = FALSE])
      rownames(out) <- NULL
      out
    }

    # Contexts are sent with the fetched margin and trimmed in the browser to the
    # current "Context" value, so changing it is instant (no server round trip).
    trim_js <- DT::JS(sprintf(
      "function(data, type, row, meta) {
         if (type !== 'display' || data === null) return data;
         var k = parseInt($('#%s').val());
         if (isNaN(k)) return data;
         if (k <= 0) return '';
         var t = String(data).split(' ');
         if (t.length <= k) return data;
         return meta.col === 0 ? t.slice(t.length - k).join(' ') : t.slice(0, k).join(' ');
       }", ns("context")))

    output$table <- DT::renderDT({
      view <- table_view(displayed())
      ref_names <- c("Source", names(view)[-(1:4)])
      sep <- "border-left: 3px solid #6b7280;"
      # Two header rows: "Concordance" (context + pivot) | "Reference" (source + metadata)
      container <- htmltools::withTags(table(class = "display nowrap",
        thead(
          tr(th(colspan = 3, class = "dt-center", "Concordance"),
             th(colspan = length(ref_names), class = "dt-center", style = sep, "Reference")),
          tr(th("Left context"), th("Term"), th("Right context"),
             lapply(seq_along(ref_names), function(i)
               th(style = if (i == 1) sep else NULL, ref_names[i])))
        )))
      DT::datatable(
        view, rownames = FALSE, selection = "none", container = container, class = "display nowrap",
        options = list(pageLength = 25, scrollX = TRUE, order = list(),
                       columnDefs = list(list(className = "dt-right", targets = 0, render = trim_js),
                                         list(targets = 2, render = trim_js),
                                         list(className = "dt-center", targets = c(1, 3))))
      ) |>
        DT::formatStyle("keyword", fontWeight = "bold") |>
        DT::formatStyle("source", borderLeft = "3px solid #6b7280")
    }, server = TRUE)

    output$export <- downloadHandler(
      filename = function() paste0("concordances_", format(Sys.time(), "%Y%m%d_%H%M%S"), ".csv"),
      content = function(file) {
        hits <- displayed()
        k <- min(requested_context(), result()$fetched_context %||% requested_context())
        if (nrow(hits) > 0) {
          hits$left <- cqp_trim_tokens(hits$left, k, from_end = TRUE)
          hits$right <- cqp_trim_tokens(hits$right, k, from_end = FALSE)
        }
        write.csv(table_view(hits), file, row.names = FALSE, fileEncoding = "UTF-8")
      }
    )

    # ---- Distribution by the selected metadata column ----
    dist_plot <- reactive({
      col <- input$filter_col
      counts <- cqp_count_by(displayed(), col)
      many <- nrow(counts) > 15
      p <- ggplot2::ggplot(counts, ggplot2::aes(x = value, y = n)) +
        ggplot2::geom_col(fill = "#3a3a5a") +
        ggplot2::labs(title = paste("Distribution by", col), x = col, y = "Occurrences") +
        ggplot2::theme_classic()
      if (many) p + ggplot2::coord_flip() + ggplot2::scale_x_discrete(limits = rev)
      else p + ggplot2::theme(axis.text.x = ggplot2::element_text(angle = 45, hjust = 1))
    })

    observeEvent(input$distribution, {
      res <- result()
      if (is.null(res) || nrow(displayed()) == 0) {
        showNotification("No result to plot.", type = "warning"); return()
      }
      col <- input$filter_col
      if (is.null(col) || identical(col, CQP_NO_FILTER)) {
        showNotification("First select a metadata column in 'Filter by' to plot the distribution.",
                         type = "warning"); return()
      }
      n_values <- nrow(cqp_count_by(displayed(), col))
      if (n_values < 2) {
        showNotification("The plot needs at least 2 different values: all displayed results have the same value for this column.",
                         type = "warning"); return()
      }
      height <- if (n_values > 15) max(500, 22 * n_values) else 450
      showModal(modalDialog(
        title = paste("Distribution of the concordances by", col), size = "l", easyClose = TRUE,
        div(style = "max-height: 600px; overflow-y: auto;",
            plotOutput(ns("dist_plot"), height = paste0(height, "px"))),
        footer = tagList(downloadButton(ns("dist_save"), "Save the plot"), modalButton("Close"))
      ))
    })
    output$dist_plot <- renderPlot(dist_plot(), res = 96)
    output$dist_save <- downloadHandler(
      filename = function() paste0("distribution_", input$filter_col, "_",
                                   format(Sys.time(), "%Y%m%d_%H%M%S"), ".png"),
      content = function(file) {
        n_values <- nrow(cqp_count_by(displayed(), input$filter_col))
        ggplot2::ggsave(file, dist_plot(), width = 10,
                        height = if (n_values > 15) max(6, n_values * 0.3) else 6, dpi = 300)
      }
    )

    # Returned API: lets other parts of the app (plot clicks, clusters) run a query
    list(
      search = function(query, mode = "cqp") {
        updateSelectInput(session, "mode", selected = mode)
        updateTextInput(session, "query", value = query)
        run_query(query)
      },
      result = result
    )
  })
}

if (!exists("%||%")) `%||%` <- function(a, b) if (is.null(a)) b else a
