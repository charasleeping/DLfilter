const search_genres = {
    add: new Set(),
    included: new Set(),
    excluded: new Set()
};
const search_categories = new Set();
const genre_class = {
    add: "text-primary-emphasis bg-primary-subtle border border-primary-subtle",
    included: "text-success-emphasis bg-success-subtle border border-success-subtle",
    excluded: "text-danger-emphasis bg-danger-subtle border border-danger-subtle"
};
const work_format_class = {
    "Game": "primary",
    "Manga": "success",
    "CG + Illustrations": "info",
    "Novel": "light",
    "Video": "primary",
    "Voice / ASMR": "warning",
    "Music": "warning",
    "Tools / Accessories": "light",
    "Miscellaneous": "light"
}

const version = "2.0";
// slider position -> server weight function: lower popular genres, none, lower unpopular genres
const popularity_weight_func = [1, 4, 2];
const SUN_ICON = `<svg class="sun-icon" viewBox="0 0 24 24" width="1.6em" height="1.6em" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>`;
const rjid_regex = /^RJ(?:\d{8}|\d{6})$/;
const page_size = 48;

const startDate = new Date(2000, 0, 1);
const currentDate = new Date();
const months_from_start = (currentDate.getFullYear() - startDate.getFullYear()) * 12 + currentDate.getMonth() - startDate.getMonth();

var locale_data = null;
var current_page = 1;

// use the language chosen with the language button, otherwise the language of the browser
var lang_raw = navigator.language || navigator.userLanguage;
// lang_raw = "ja-JP";
var lang = lang_raw.replace("-", "_");
if (supported_lang.indexOf(lang) == -1) {
    lang = "en_US";
}
try {
    const saved_lang = localStorage.getItem("lang");
    if (supported_lang.indexOf(saved_lang) != -1) {
        lang = saved_lang;
        lang_raw = saved_lang.replace("_", "-");
    }
} catch (e) { }
document.documentElement.lang = lang.replace("_", "-");
var info_data = null;

$(document).ready(function () {
    // initialize the collapses
    var collapse_genres_container = new bootstrap.Collapse($("#collapse-genres-container"), {
        toggle: false
    });
    var collapse_welcome_banner = new bootstrap.Collapse($("#welcome-banner"), {
        toggle: false
    });
    var collapse_result_card_container = new bootstrap.Collapse($("#result-card-container"), {
        toggle: false
    });

    // initialize the localisation
    setLocaleText(lang);
    $.getJSON("/api/locale/" + lang, data => {
        if (data["state"] == "success") {
            locale_data = data["locale"];
            setGenreLocale(locale_data);
            setWorkFormatLocale(locale_data);
        } else {
            console.log("Failed to get locale data");
        }
    });
    $.getJSON("/api/info", data => {
        info_data = data;
        showInfo();
    });

    // go to top button
    $("#go-top-btn").click(function () {
        $("#result-panel").animate({
            scrollTop: 0
        }, 500);
    });

    // search panel tabs: "keyword" (local catalogue search) or "similar" (similarity search)
    function showSearchTab(tab) {
        bootstrap.Tab.getOrCreateInstance(document.getElementById(`${tab}-tab`)).show();
    }

    // set up interaction for start text: hovering a term highlights where to type it
    // (and its tab when that tab is not open); clicking opens the tab
    const hint_targets = {
        "welcome-start-hint-keywords": { tab: "keyword", target: "#catalog-query" },
        "welcome-start-hint-genres": { tab: "similar", target: "#genre-title, #genre-title-icon" },
        "welcome-start-hint-workid": { tab: "similar", target: "#rjid" },
    };
    $("#welcome-start-hint").on("mouseenter mouseleave", "span[id^=welcome-start-hint-]", function (event) {
        const hint = hint_targets[this.id];
        const on = event.type == "mouseenter";
        $(hint.target).toggleClass("hint-highlight", on);
        $(`#${hint.tab}-tab`).toggleClass("hint-highlight", on && !$(`#${hint.tab}-tab`).hasClass("active"));
    }).on("click", "span[id^=welcome-start-hint-]", function () {
        const hint = hint_targets[this.id];
        $(`#${hint.tab}-tab`).removeClass("hint-highlight");
        showSearchTab(hint.tab);
        if (this.id == "welcome-start-hint-keywords") {
            $("#catalog-query").focus();
        } else if (this.id == "welcome-start-hint-workid") {
            $("#rjid").focus();
        }
    });

    // set up the range slider
    setDateRangeText($("#date-range").val());
    $("#date-range").on("input", function () {
        setDateRangeText($(this).val());
    });

    $("#date-reset-btn").click(function () {
        $("#date-range").val(5);
        setDateRangeText(5);
    });
    $("#dlcount-reset-btn").click(function () {
        $("#dlcount-range").val(50);
    });
    $("#popularity-weight-reset-btn").click(function () {
        $("#popularity-weight-range").val(1);
    });

    // each advanced slider only applies while its switch is on
    $(".advanced-option .form-switch input").on("change", function () {
        const option = $(this).closest(".advanced-option");
        option.toggleClass("is-off", !this.checked);
        option.find("input[type=range]").prop("disabled", !this.checked);
        option.find(".btn-add").toggleClass("disabled", !this.checked).attr("aria-disabled", !this.checked);
    });

    // set up the genre when it is clicked
    $("#genre-container").on("change", ".genre-item input[type=checkbox]", function () {
        var genre_id = $(this).val();
        var genre_type = $('#selected-genre-container').attr('data-genre-action');
        if (this.checked) {
            addGenre(genre_type, genre_id);
        } else {
            removeGenre(genre_type, genre_id);
        }
    });
    // set up the work format when it is clicked
    $("#categories-container").on("change", ".col-12 input[type=checkbox]", function () {
        var workformat_id = $(this).val();
        if (this.checked) {
            addWorkFormat(workformat_id);
        } else {
            removeWorkFormat(workformat_id);
        }
    });

    // initialize the genre select modal for each genre type (add, included, excluded)
    $('#genre-modal').on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget);
        var genre_type = button.data('genre-action');

        $("#category-link-nav a").removeClass("text-success-emphasis text-danger-emphasis");
        $("#genre-search-bar").removeClass("focus-ring-success focus-ring-danger");

        // unchecked all the checkbox
        $("#genre-container input[type=checkbox]").prop("checked", false).removeClass("focus-ring-success focus-ring-danger");
        $('#selected-genre-container').attr('data-genre-action', genre_type);
        $("#genre-container").attr("data-genre-action", genre_type);

        // clear the selected genre container
        $("#selected-genre-container").empty();

        // add the selected genre to the selected genre container
        search_genres[genre_type].forEach(genre_id => {
            $(`#genre-${genre_id}`).prop("checked", true);
            $("#selected-genre-container").append(
                $("<a>", {
                    "class": `btn me-1 ${genre_class[genre_type]} rounded-pill btn-genre`,
                    "role": "button",
                    "data-genre-value": genre_id
                }).html(`${locale_data["genres"][genre_id]["name"]} <i class="fa-solid fa-xmark"></i>`)
            );
        });

        // change the modal title and description
        var hint = `<br><span id='selected-genre-container-hint' class='text-muted small'>${localisation.not_selected[lang]}</span>`;
        switch (genre_type) {
            case "add":
                $("#genre-modal-title").html(`<i class="fa-solid fa-tags"></i> ${localisation.search_genres_modal_title[lang]}`);
                $("#modal-desc").html(`${localisation.selected_search_genres_desp[lang]} (<span id="selected-genre-size">${search_genres[genre_type].size}</span>)${hint}`);

                break;
            case "included":
                $("#genre-modal-title").html(`<i class="fa-solid fa-filter"></i> ${localisation.included_genres_modal_title[lang]}`);
                $("#modal-desc").html(`${localisation.selected_included_genres_desp[lang]} (<span id="selected-genre-size">${search_genres[genre_type].size}</span>)${hint}`);

                $("#category-link-nav a").addClass("text-success-emphasis")
                $("#genre-search-bar").addClass("focus-ring-success");
                $("#genre-container input[type=checkbox]").addClass("focus-ring-success");
                break;
            case "excluded":
                $("#genre-modal-title").html(`<i class="fa-solid fa-filter-circle-xmark"></i> ${localisation.excluded_genres_modal_title[lang]}`);
                $("#modal-desc").html(`${localisation.selected_excluded_genres_desp[lang]} (<span id="selected-genre-size">${search_genres[genre_type].size}</span>)${hint}`);

                $("#category-link-nav a").addClass("text-danger-emphasis")
                $("#genre-search-bar").addClass("focus-ring-danger");
                $("#genre-container input[type=checkbox]").addClass("focus-ring-danger");
                break;
        }

        if (search_genres[genre_type].size > 0) {
            $("#selected-genre-container-hint").hide();
        }
    });

    // toggle the light/dark mode
    function applyTheme(theme) {
        const isDark = theme == "dark";
        const label = (isDark ? localisation.theme_to_light : localisation.theme_to_dark)[lang];
        $("html").attr("data-bs-theme", theme);
        $("#lang-toggle")
            .toggleClass("btn-outline-light", isDark)
            .toggleClass("btn-outline-dark", !isDark);
        $("#dark-toggle")
            .toggleClass("btn-outline-light", isDark)
            .toggleClass("btn-outline-dark", !isDark)
            .attr({ "aria-label": label, "title": label })
            .html(isDark ? `<i class="fa-solid fa-moon"></i>` : SUN_ICON);
    }

    $("#dark-toggle").click(function () {
        const next = $("html").attr("data-bs-theme") == "dark" ? "light" : "dark";
        if (!document.startViewTransition) {
            applyTheme(next);
            return;
        }
        // normal motion: the new theme spreads out from the button as a circle
        // reduced motion: the CSS keeps the default cross-fade instead
        const rect = this.getBoundingClientRect();
        const x = rect.left + rect.width / 2;
        const y = rect.top + rect.height / 2;
        const radius = Math.hypot(Math.max(x, window.innerWidth - x), Math.max(y, window.innerHeight - y));
        const reduce_motion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        const transition = document.startViewTransition(() => applyTheme(next));
        if (reduce_motion) {
            transition.ready.catch(() => { });
            return;
        }
        transition.ready.then(() => {
            document.documentElement.animate(
                { clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${radius}px at ${x}px ${y}px)`] },
                { duration: 600, easing: "ease-in-out", pseudoElement: "::view-transition-new(root)" }
            );
        }).catch(() => { });
    });

    // catalogue age filter: summarise the ticked options on the dropdown button
    function updateCatalogAgeSummary() {
        const labels = [1, 2, 3]
            .filter(i => $(`#catalog-age-${i}`).prop("checked"))
            .map(i => $(`#catalog-age-${i}-label`).text());
        $("#catalog-age-summary").text(labels.length ? labels.join(", ") : localisation.catalog_age_any[lang]);
    }
    $("#catalog-age-container").on("change", "input[type=checkbox]", updateCatalogAgeSummary);

    // credits: reveal the text one character at a time (links stay intact)
    function typeCredits(container) {
        const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
        const text_nodes = [];
        while (walker.nextNode()) {
            text_nodes.push(walker.currentNode);
        }
        const chars = [];
        text_nodes.forEach(node => {
            const fragment = document.createDocumentFragment();
            for (const ch of node.nodeValue) {
                const span = document.createElement("span");
                span.className = "tw-char";
                span.textContent = ch;
                chars.push(span);
                fragment.appendChild(span);
            }
            node.replaceWith(fragment);
        });
        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
            chars.forEach(span => span.classList.add("tw-on"));
            return;
        }
        const caret = document.createElement("span");
        caret.className = "tw-caret";
        caret.setAttribute("aria-hidden", "true");
        container.appendChild(caret);
        let i = 0;
        const timer = setInterval(() => {
            if (i >= chars.length) {
                clearInterval(timer);
                setTimeout(() => caret.remove(), 1500);
                return;
            }
            chars[i].classList.add("tw-on");
            chars[i].after(caret);
            i++;
        }, 45);
    }
    typeCredits(document.getElementById("credits"));

    // when the genre is clicked, remove the genre
    $("#selected-genre-container").on("click", ".btn-genre", function () {
        var genre_id = $(this).data("genre-value");
        var genre_type = $('#selected-genre-container').attr('data-genre-action');
        $(`#genre-${genre_id}`).prop("checked", false);
        removeGenre(genre_type, genre_id);
    });
    $("#search-terms-container").on("click", ".btn-genre", function () {
        var genre_id = $(this).data("genre-value");
        var genre_type = $(this.parentElement).attr("id").split("-")[1];
        removeGenre(genre_type, genre_id);
    });
    // when the work format is clicked, remove the work format
    $("#workformat-add-container").on("click", ".btn-genre", function () {
        var workformat_id = $(this).data("workformat-value");
        $(`#workformat-${workformat_id}`).prop("checked", false);
        removeWorkFormat(workformat_id);
    });

    // select all the work format when click on the title
    $("#categories-container").on("change", ".category-container p input[type=checkbox]", function () {
        var isChecked = $(this).prop("checked");
        $(this.parentElement.parentElement).find("div input[type=checkbox]").prop("checked", isChecked);
        $(this.parentElement.parentElement).find("div input[type=checkbox]").each(function () {
            var workformat_id = $(this).val();
            if (isChecked) {
                addWorkFormat(workformat_id);
            } else {
                removeWorkFormat(workformat_id);
            }
        });
    });

    // clear all the genre
    $("#btn-genre-clear").click(function () {
        var genre_type = $('#selected-genre-container').attr('data-genre-action');
        search_genres[genre_type].forEach(genre_id => {
            $(`#genre-${genre_id}`).prop("checked", false);
            removeGenre(genre_type, genre_id);
        });
    });

    // automatically filter the genre in the modal when the user type in the search bar
    $("#genre-search-bar").keyup(function () {
        // first reset the genre visibility
        $("#genre-container .category-container .form-check").show();
        $("#genre-container .category-container").show();

        let search = $(this).val().toLowerCase();
        if (search != "") {
            // hide the genre that does not match the search
            $("#genre-container .category-container .form-check-label").each(function () {
                let label = $(this).text().trim().replace(/\s+\S+$/, '').toLowerCase();
                if (!label.includes(search)) {
                    $(this).parent().hide();
                }
            });

            // hide the category that does not have any visible genre
            $("#genre-container .category-container").each(function () {
                if ($(this).find(".form-check:visible").length == 0) {
                    $(this).hide();
                }
            });
        }
    });

    // automatically fill genres when the user type in the search bar
    $("#rjid").keyup(function () {
        var rjid = $(this).val().toUpperCase();
        if (rjid_regex.test(rjid)) {
            $.ajax({
                url: "/api/works",
                dataType: "json",
                data: { "rj_id": rjid },
                success: function (data) {
                    if (data["state"] == "success") {
                        if (Object.keys(data["works"][rjid]).length !== 0) {
                            var work = data["works"][rjid];
                            console.log(work);

                            var work_name = work["name"];
                            var genres = work["tags"];

                            // clear the genre container
                            clearAddGenre();

                            // check if the genre is in locale_data
                            // if not, remove it from the genre list
                            genres = genres.filter(genre_id => genre_id in locale_data.genres);

                            // add the genre
                            genres.forEach(genre_id => {
                                addGenre("add", genre_id);
                            });

                            // if the work format is empty, add the work format of the work
                            if (search_categories.size == 0) {
                                var workformat_id = work["type"];
                                addWorkFormat(workformat_id);
                                $(`#workformat-${workformat_id}`).prop("checked", true);
                            }

                            // add the name to the search bar
                            $("#rjid-work-name").text(work_name);
                        } else {
                            $("#rjid-work-name").text(localisation.work_not_in_local_db[lang]);
                        }
                    } else {
                        console.log(data["message"]);
                        $("#rjid-work-name").text(localisation.error_occurred[lang]);
                    }
                },

                error: function (xhr, ajaxOptions, thrownError) {
                    console.log(xhr.status);
                    console.log(thrownError);
                    $("#rjid-work-name").text(localisation.error_occurred[lang]);
                },
                timeout: 3000,
            });
        } else if (rjid == "") {
            $("#rjid-work-name").text("");
        } else {
            $("#rjid-work-name").text(localisation.work_input_hint_format[lang]);
        }
    });

    // switch pages
    $("#pagination-container").on("click", ".page-link", function () {
        console.log("page clicked");
        if ($(this).hasClass("active")) {
            return;
        }
        $("#pagination-container .page-link").removeClass("active");
        $(this).addClass("active");
        const page = $(this).text();
        collapse_result_card_container.hide();

        getSearchResults(page, success => {
            if (success) {
                setTimeout(function () {
                    collapse_result_card_container.show();
                }, 750);
            } else {
                console.log("Error occurred when getting the search results.");
            }
        });
    });

    // clear the search result
    $("#clear-btn").click(function () {
        if (!$("#result-card-container").hasClass("show")) {
            return;
        }
        if (!$("#loading-spinner-container").hasClass("visually-hidden")) {
            return;
        }
        if (!$("#search-info").hasClass("visually-hidden")) {
            $("#search-info").addClass("visually-hidden");
        }
        $("#pagination-container").empty();
        $("#search-end-of-result").css("display", "none");
        $("#side-btn-container").css("display", "none");
        collapse_result_card_container.hide();
        if ($("#catalog-results-section").hasClass("d-none")) {
            collapse_welcome_banner.show();
        }
        setTimeout(function () {
            $("#search-result-container").empty();
        }, 500);
    });

    $("#expand-btn").click(function () {
        if (!$("#result-card-container").hasClass("show")) {
            return;
        }
        if (!$("#loading-spinner-container").hasClass("visually-hidden")) {
            return;
        }
        const collapseThumbList = document.querySelectorAll('.work-card > .collapse')
        const collapseList = [...collapseThumbList].map(collapseEl => new bootstrap.Collapse(collapseEl, { toggle: false }))
        if ($(this).attr("data-action") == "open") {
            collapseList.forEach(collapseEl => collapseEl.show())
            $(this).attr("data-action", "close");
            $(this).html(`<i class="fa-regular fa-envelope-open"></i>`);
        } else {
            collapseList.forEach(collapseEl => collapseEl.hide())
            $(this).attr("data-action", "open");
            $(this).html(`<i class="fa-regular fa-envelope"></i>`);
        }
    });

    // ---- local catalogue search (title / circle / RJ ID) ----
    // Independent of the similarity search: own request counter, results, and pagination.
    var catalog_request_id = 0;
    var catalog_query = null;
    // the last rendered catalogue results, kept to render them again in another language
    var catalog_view = null;
    var catalog_title_key = "catalog_results_title";

    $("#catalog-search-form").on("submit", function (event) {
        event.preventDefault();
        const q = $("#catalog-query").val().trim();
        if (q == "") {
            $("#catalog-query").focus();
            return;
        }
        catalog_query = {
            q: q,
            field: $("#catalog-field").val(),
            ages: catalogAges(),
        };
        catalogSearch(1);
    });

    $("#catalog-pagination").on("click", ".page-item:not(.disabled):not(.active) .page-link", function () {
        catalogSearch(parseInt($(this).attr("data-page"), 10));
        $("#catalog-results-section").get(0).scrollIntoView({ behavior: "smooth", block: "start" });
    });

    $("#catalog-card-container").on("click", ".catalog-find-similar", function () {
        // fill the RJ ID so its genres and format are loaded; the user starts the similarity search
        $("#rjid").val($(this).attr("data-rjid")).trigger("keyup");
        showSearchTab("similar");
        $("#search-panel").get(0).scrollIntoView({ behavior: "smooth", block: "start" });
        $("#rjid").focus();
    });

    function startCatalogResults(title_key) {
        catalog_view = null;
        catalog_title_key = title_key;
        $("#catalog-results-title").text(localisation[title_key][lang]);
        $("#catalog-results-section").removeClass("d-none");
        if ($("#welcome-banner").hasClass("show")) {
            collapse_welcome_banner.hide();
        }
        $("#catalog-card-container, #catalog-pagination").empty();
        $("#catalog-status").text(localisation.catalog_searching[lang]);
        $("#catalog-spinner").removeClass("d-none");
    }

    function catalogAges() {
        return [1, 2, 3].map(i => $(`#catalog-age-${i}`).prop("checked") ? "1" : "0").join("");
    }

    function catalogSearch(page) {
        const request_id = ++catalog_request_id;
        startCatalogResults("catalog_results_title");

        $.ajax({
            url: "/api/search",
            dataType: "json",
            data: { ...catalog_query, page: page, page_size: page_size },
            timeout: 20000,
            success: function (data) {
                if (request_id != catalog_request_id) {
                    return;  // a newer search has started
                }
                $("#catalog-spinner").addClass("d-none");
                catalog_view = { kind: "search", data: data };
                renderCatalogResults(data);
            },
            error: function (xhr, ajaxOptions, thrownError) {
                if (request_id != catalog_request_id) {
                    return;
                }
                console.log(xhr.status, xhr.responseJSON ? xhr.responseJSON.message : thrownError);
                $("#catalog-spinner").addClass("d-none");
                $("#catalog-status").text(localisation.catalog_error[lang]);
            },
        });
    }

    function renderCatalogResults(data) {
        if (data.results.length == 0) {
            $("#catalog-status").text(localisation.catalog_no_results[lang]);
            renderCatalogPagination(data.page, Math.ceil(data.total / data.page_size));
            return;
        }
        const start = (data.page - 1) * data.page_size + 1;
        const end = start + data.results.length - 1;
        $("#catalog-status").html(localisation.catalog_summary[lang]
            .replace("{total}", Number(data.total).toLocaleString(lang_raw))
            .replace("{start}", Number(start).toLocaleString(lang_raw))
            .replace("{end}", Number(end).toLocaleString(lang_raw)));

        const label = localisation.catalog_find_similar[lang];
        $("#catalog-card-container").append(data.results.map(work => catalogCardTemplate(work, label)));
        renderCatalogPagination(data.page, Math.ceil(data.total / data.page_size));
    }

    function renderCatalogPagination(current, page_count) {
        const container = $("#catalog-pagination").empty();
        if (page_count <= 1) {
            return;
        }
        const item = (label, page, state, aria_label) => {
            const link = $("<button>", { "type": "button", "class": "page-link", "data-page": page }).text(label);
            if (aria_label) {
                link.attr("aria-label", aria_label);
            }
            if (state == "active") {
                link.attr("aria-current", "page");
            }
            return $("<li>", { "class": `page-item ${state || ""}` }).append(link);
        };

        // first, last, and two pages either side of the current one
        const pages = [...new Set([1, current - 2, current - 1, current, current + 1, current + 2, page_count])]
            .filter(p => p >= 1 && p <= page_count)
            .sort((a, b) => a - b);

        container.append(item("‹", current - 1, current == 1 ? "disabled" : "", localisation.catalog_previous_page[lang]));
        let previous = 0;
        pages.forEach(p => {
            if (p - previous > 1) {
                container.append(item("…", "", "disabled"));
            }
            container.append(item(p, p, p == current ? "active" : ""));
            previous = p;
        });
        container.append(item("›", current + 1, current == page_count ? "disabled" : "", localisation.catalog_next_page[lang]));
    }

    // ---- random works from the local database ----
    // on the keyword tab only the catalogue age filter applies; on the similar tab the similarity filters apply
    $("#random-works-btn").click(() => randomWorks({ ages: catalogAges() }));
    $("#similar-random-btn").click(() => randomWorks(similarFilters()));

    function randomWorks(filters) {
        const request_id = ++catalog_request_id;
        startCatalogResults("random_results_title");
        $("#result-panel").scrollTop(0);

        $.ajax({
            url: "/api/random",
            dataType: "json",
            data: { ...filters, count: page_size },
            timeout: 20000,
            success: function (data) {
                if (request_id != catalog_request_id) {
                    return;
                }
                $("#catalog-spinner").addClass("d-none");
                catalog_view = { kind: "random", data: data };
                renderRandomResults(data);
            },
            error: function (xhr, ajaxOptions, thrownError) {
                if (request_id != catalog_request_id) {
                    return;
                }
                console.log(xhr.status, xhr.responseJSON ? xhr.responseJSON.message : thrownError);
                $("#catalog-spinner").addClass("d-none");
                $("#catalog-status").text(localisation.catalog_error[lang]);
            },
        });
    }

    function renderRandomResults(data) {
        if (data.results.length == 0) {
            $("#catalog-status").text(localisation.catalog_no_results[lang]);
            return;
        }
        $("#catalog-status").text(localisation.random_summary[lang]
            .replace("{count}", Number(data.results.length).toLocaleString(lang_raw)));
        const label = localisation.catalog_find_similar[lang];
        $("#catalog-card-container").append(data.results.map(work => catalogCardTemplate(work, label)));
    }

    // render the catalogue results again, e.g. after the language changed
    function refreshCatalogView() {
        if (!catalog_view) {
            return;
        }
        $("#catalog-card-container, #catalog-pagination").empty();
        $("#catalog-results-title").text(localisation[catalog_title_key][lang]);
        if (catalog_view.kind == "search") {
            renderCatalogResults(catalog_view.data);
        } else {
            renderRandomResults(catalog_view.data);
        }
    }

    // the filters of the similarity search; the genres to look for and the popularity weights are not filters
    function excludedOptions() {
        return [[2, "AIG"], [3, "AIP"], [4, "GRO"], [5, "MEN"]]
            .filter(([i]) => $(`#misc-checkbox-${i}`).prop("checked"))
            .map(([, option]) => option).join("+");
    }

    function similarFilters() {
        const filters = {
            ages: [1, 2, 3].map(i => $(`#age-checkbox-${i}`).prop("checked") ? "1" : "0").join(""),
            excluded_low_rate: $("#misc-checkbox-1").prop("checked"),
        };
        const lists = {
            categories: [...search_categories],
            included_genres: [...search_genres.included].slice(0, 5),
            excluded_genres: [...search_genres.excluded].slice(0, 5),
        };
        for (const key in lists) {
            if (lists[key].length > 0) {
                filters[key] = lists[key].join("+");
            }
        }
        if ($("#date-range-enabled").prop("checked")) {
            const date = monthFunc(months_from_start, $("#date-range").val());
            filters.since = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
        }
        if (excludedOptions()) {
            filters.excluded_options = excludedOptions();
        }
        return filters;
    }

    // ---- reset: clear every search and go back to the welcome page ----
    $("#reset-search-btn, #similar-reset-btn").click(function () {
        catalog_request_id++;
        catalog_query = null;
        catalog_view = null;
        $("#catalog-search-form").get(0).reset();
        updateCatalogAgeSummary();
        $("#catalog-results-section").addClass("d-none");
        $("#catalog-card-container, #catalog-pagination").empty();
        $("#catalog-spinner").addClass("d-none");

        similarity_request_id++;
        applyPreset(default_preset);
        $("#loading-spinner-container, #search-info").addClass("visually-hidden");
        $("#pagination-container").empty();
        $("#search-end-of-result").css("display", "none");
        $("#side-btn-container").css("display", "none");
        collapse_result_card_container.hide();

        collapse_welcome_banner.show();
        $("#result-panel").scrollTop(0);
    });

    // ---- presets: the similarity search settings, saved as JSON files in the presets folder ----
    const preset_name_regex = /^[\p{L}\p{N}\p{M}_\- ]{1,60}$/u;
    let last_preset_name = "";

    function currentPreset() {
        const slider = (switch_id, range_id) => ({
            enabled: $(switch_id).prop("checked"),
            value: parseInt($(range_id).val(), 10),
        });
        const rj_id = $("#rjid").val().trim().toUpperCase();
        return {
            rj_id: rjid_regex.test(rj_id) ? rj_id : "",
            genres: [...search_genres.add],
            included_genres: [...search_genres.included],
            excluded_genres: [...search_genres.excluded],
            categories: [...search_categories],
            popularity_weight: slider("#popularity-weight-enabled", "#popularity-weight-range"),
            release_date: slider("#date-range-enabled", "#date-range"),
            download_count: slider("#dlcount-range-enabled", "#dlcount-range"),
            ages: [1, 2, 3].map(i => $(`#age-checkbox-${i}`).prop("checked")),
            excluded_contents: [1, 2, 3, 4, 5].map(i => $(`#misc-checkbox-${i}`).prop("checked")),
            advanced_options_open: $("#advanced-options-panel").hasClass("show"),
        };
    }
    const default_preset = currentPreset();

    // presets may come from any file, so only known ids and well-formed values are used
    function applyPreset(preset) {
        preset = { ...default_preset, ...preset };
        const ids = value => Array.isArray(value) ? value.map(String) : [];
        const known = table => id => locale_data != null && Object.hasOwn(locale_data[table], id);

        ["add", "included", "excluded"].forEach(type => {
            [...search_genres[type]].forEach(id => removeGenre(type, id));
        });
        [...search_categories].forEach(id => removeWorkFormat(id));
        $("#categories-container input[type=checkbox]").prop("checked", false);

        ids(preset.genres).filter(known("genres")).forEach(id => addGenre("add", id));
        ids(preset.included_genres).filter(known("genres")).forEach(id => addGenre("included", id));
        ids(preset.excluded_genres).filter(known("genres")).forEach(id => addGenre("excluded", id));
        ids(preset.categories).filter(known("work_formats")).forEach(id => {
            addWorkFormat(id);
            $(`#workformat-${id}`).prop("checked", true);
        });

        // set the RJ ID without its keyup handler, which would replace the genres
        const rj_id = typeof preset.rj_id == "string" && rjid_regex.test(preset.rj_id) ? preset.rj_id : "";
        $("#rjid").val(rj_id);
        showWorkName(rj_id);

        const slider = (option, switch_id, range_id) => {
            option = option || {};
            if (Number.isFinite(Number(option.value))) {
                $(range_id).val(Number(option.value));  // the range input clamps it
            }
            $(switch_id).prop("checked", option.enabled === true).trigger("change");
        };
        slider(preset.popularity_weight, "#popularity-weight-enabled", "#popularity-weight-range");
        slider(preset.release_date, "#date-range-enabled", "#date-range");
        slider(preset.download_count, "#dlcount-range-enabled", "#dlcount-range");
        setDateRangeText($("#date-range").val());

        const flags = (value, count) => Array.isArray(value) && value.length == count ? value : [];
        flags(preset.ages, 3).forEach((on, i) => $(`#age-checkbox-${i + 1}`).prop("checked", on === true));
        flags(preset.excluded_contents, 5).forEach((on, i) => $(`#misc-checkbox-${i + 1}`).prop("checked", on === true));

        const panel = bootstrap.Collapse.getOrCreateInstance("#advanced-options-panel", { toggle: false });
        if (preset.advanced_options_open === true) {
            panel.show();
        } else {
            panel.hide();
        }
    }

    function showWorkName(rj_id) {
        if (rj_id == "") {
            $("#rjid-work-name").text("");
            return;
        }
        $.getJSON("/api/works", { rj_id: rj_id }).done(data => {
            if ($("#rjid").val() != rj_id) {
                return;
            }
            const work = data.state == "success" ? data.works[rj_id] : null;
            $("#rjid-work-name").text(work && work.name ? work.name : localisation.work_not_in_local_db[lang]);
        }).fail(() => $("#rjid-work-name").text(localisation.error_occurred[lang]));
    }

    function presetError(xhr) {
        if (xhr.status == 400) {
            return localisation.preset_name_invalid[lang];
        }
        return xhr.status == 409 ? localisation.preset_too_many[lang] : localisation.preset_save_failed[lang];
    }

    $("#preset-save-modal").on("show.bs.modal", function () {
        $("#preset-name").val(last_preset_name).removeClass("is-invalid");
        $.getJSON("/api/presets").done(data => {
            $("#preset-name-list").empty().append(data.presets.map(preset => $("<option>", { value: preset.name })));
        });
    }).on("shown.bs.modal", function () {
        $("#preset-name").trigger("focus").trigger("select");
    });
    $("#preset-name").on("input", function () {
        $(this).removeClass("is-invalid");
    });

    $("#preset-save-form").on("submit", function (event) {
        event.preventDefault();
        const name = $("#preset-name").val().trim();
        const fail = message => {
            $("#preset-save-error").text(message);
            $("#preset-name").addClass("is-invalid").trigger("focus");
        };
        if (!preset_name_regex.test(name)) {
            fail(localisation.preset_name_invalid[lang]);
            return;
        }
        $("#preset-save-submit").prop("disabled", true);
        $.ajax({
            type: "PUT",
            url: `/api/presets/${encodeURIComponent(name)}`,
            data: JSON.stringify(currentPreset()),
            contentType: "application/json",
            dataType: "json",
            timeout: 10000,
        }).done(() => {
            last_preset_name = name;
            bootstrap.Modal.getOrCreateInstance("#preset-save-modal").hide();
            const icon = $("#preset-save-btn i").attr("class", "fa-solid fa-check");
            setTimeout(() => icon.attr("class", "fa-solid fa-floppy-disk"), 1500);
        }).fail(xhr => fail(presetError(xhr))).always(() => {
            $("#preset-save-submit").prop("disabled", false);
        });
    });

    function setPresetStatus(text, is_error) {
        $("#preset-list-status").text(text).toggleClass("d-none", text == "").toggleClass("text-danger", Boolean(is_error));
    }

    function finishPresetLoad(preset, name) {
        applyPreset(preset);
        last_preset_name = name;
        bootstrap.Modal.getOrCreateInstance("#preset-load-modal").hide();
        showSearchTab("similar");
    }

    $("#preset-load-modal").on("show.bs.modal", function () {
        const list = $("#preset-list").empty();
        setPresetStatus(localisation.catalog_searching[lang]);
        $.getJSON("/api/presets").done(data => {
            $("#preset-folder").text(`${data.folder}/`);
            if (data.presets.length == 0) {
                setPresetStatus(localisation.preset_none[lang]);
                return;
            }
            setPresetStatus("");
            list.append(data.presets.map(preset => $("<button>", {
                "type": "button",
                "class": "list-group-item list-group-item-action d-flex justify-content-between align-items-center gap-3",
                "data-preset": preset.name,
            }).append(
                $("<span>", { "class": "text-break" }).text(preset.name),
                $("<small>", { "class": "text-body-secondary text-nowrap" })
                    .text(new Date(preset.modified).toLocaleString(lang_raw, { dateStyle: "medium", timeStyle: "short" }))
            )));
        }).fail(() => setPresetStatus(localisation.preset_load_failed[lang], true));
    });

    $("#preset-list").on("click", "button[data-preset]", function () {
        const name = $(this).attr("data-preset");
        $.getJSON(`/api/presets/${encodeURIComponent(name)}`)
            .done(data => finishPresetLoad(data.preset, name))
            .fail(() => setPresetStatus(localisation.preset_load_failed[lang], true));
    });

    // a preset file from somewhere else is read in the browser only
    $("#preset-file-btn").click(function () {
        $("#preset-file-input").val("").trigger("click");
    });
    $("#preset-file-input").on("change", function () {
        const file = this.files[0];
        if (!file) {
            return;
        }
        if (file.size > 100000) {
            setPresetStatus(localisation.preset_load_failed[lang], true);
            return;
        }
        file.text().then(text => {
            const preset = JSON.parse(text);
            if (preset == null || typeof preset != "object" || Array.isArray(preset)) {
                throw new Error("not a preset");
            }
            finishPresetLoad(preset, file.name.replace(/\.json$/i, ""));
        }).catch(() => setPresetStatus(localisation.preset_load_failed[lang], true));
    });

    // post the search data to the server
    var similarity_request_id = 0;
    $("#search-btn").click(function () {
        const rjid_val = $("#rjid").val().toUpperCase();
        const rj_id = rjid_regex.test(rjid_val) ? rjid_val : null;

        // check if the user has selected at least one genre
        if (search_genres.add.size == 0) {
            $("#genre-add-container-hint").focus();
            return;
        }
        if (search_categories.size == 0) {
            $("#workformat-add-container-hint").focus();
            return;
        }

        const excluded_options = excludedOptions() || null;

        // hide the result container and show the loading animation
        $("#loading-spinner-container").removeClass("visually-hidden");
        if (!$("#search-info").hasClass("visually-hidden")) {
            $("#search-info").addClass("visually-hidden");
        }
        if ($("#welcome-banner").hasClass("show")) {
            collapse_welcome_banner.hide();
        }
        if ($("#result-card-container").hasClass("show")) {
            collapse_result_card_container.hide();
        }

        // send the search data to the server
        const request_id = ++similarity_request_id;
        $.ajax({
            type: "POST",
            url: "/api/similarity",
            data: JSON.stringify({
                genres: Array.from(search_genres.add).slice(0, 10).join("+"),
                included_genres: Array.from(search_genres.included).slice(0, 5).join("+") || null,
                excluded_genres: Array.from(search_genres.excluded).slice(0, 5).join("+") || null,
                rj_id: rj_id,
                categories: Array.from(search_categories).join("+") || null,
                ages: `${$("#age-checkbox-1").prop("checked") ? "1" : "0"}${$("#age-checkbox-2").prop("checked") ? "1" : "0"}${$("#age-checkbox-3").prop("checked") ? "1" : "0"}`,
                date: monthFunc(months_from_start, $("#date-range-enabled").prop("checked") ? $("#date-range").val() : 0),
                dlcount: $("#dlcount-range-enabled").prop("checked") ? $("#dlcount-range").val() : 50,
                weight_func: $("#popularity-weight-enabled").prop("checked") ? popularity_weight_func[$("#popularity-weight-range").val()] : popularity_weight_func[1],
                excluded_low_rate: $("#misc-checkbox-1").prop("checked"),
                excluded_options: excluded_options,
                // "excluding_interest"
            }),
            contentType: "application/json",
            success: function (data) {
                if (request_id != similarity_request_id) {
                    return;  // reset while searching
                }
                if (data.state == "success") {
                    // save to local storage
                    localStorage.setItem("last_search_result_info", JSON.stringify(data.info));
                    localStorage.setItem("last_search_result_list", JSON.stringify(data.result));

                    // set up the pagination
                    $("#pagination-container").empty();
                    const page_count = Math.ceil(data.result.length / page_size);
                    for (let i = 1; i <= page_count; i++) {
                        $("#pagination-container").append(`<li class="page-item"><a class="page-link" href="#">${i}</a></li>`);
                    }
                    // make the first page active
                    $("#pagination-container .page-link").first().addClass("active");

                    // get the data of the first page
                    getSearchResults(1, success => {
                        if (success) {
                            // show the result card container
                            setTimeout(function () {
                                collapse_result_card_container.show();
                            }, 750);
                        } else {
                            console.log("Error occurred when getting the search results.");
                        }
                    });

                    // hide the loading animation and show the result info
                    $("#loading-spinner-container").addClass("visually-hidden");
                    $("#search-info-count").text(data.info.length);
                    $("#search-info-time").text(Math.round(data.info.time * 100) / 100);
                    $("#search-info").removeClass("visually-hidden");

                    $("#side-btn-container").css("display", "block");

                } else if (data.state == "error") {
                    console.log(data.message);
                }
            },

            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
            },
            timeout: 20000,
            dataType: "json",
        });
    });

    function setLocaleText(lang) {
        $("#search-title").text(localisation_words.search[lang]);
        $("#rjid").attr("placeholder", localisation.work_input[lang]);
        $("#rjid-title").text(localisation.rjid_title[lang]);
        $("#search-btn-label").text(localisation_words.search[lang]);
        $("#genre-title").text(localisation.genre_title[lang]);
        $("#genre-add-container-hint").text(localisation.at_least_one_genre[lang]);
        $("#included-genre-title").text(localisation.included_genres_title[lang]);
        $("#excluded-genre-title").text(localisation.excluded_genres_title[lang]);
        $("#genre-included-container-hint").text(localisation.not_selected[lang]);
        $("#genre-excluded-container-hint").text(localisation.not_selected[lang]);
        $("#workformat-title").text(localisation.workformat_title[lang]);
        $("#workformat-add-container-hint").text(localisation.at_least_one_workformat[lang]);
        $("#workformat-modal-title").html(`<i class="fa-solid fa-box-archive"></i> ${localisation.workformat_modal_title[lang]}`);
        $("#genre-search-bar").attr("placeholder", localisation.genre_search_placeholder[lang]);
        $("#advanced-panel-switch-label").text(localisation.show_advanced_options[lang]);
        $("#date-range-title").text(localisation.date_title[lang]);
        $("#date-range-label").html(localisation.date_label[lang]);
        $("#dlcount-range-title").text(localisation.dlcount_title[lang]);
        $("#dlcount-range-label-0").html(localisation.dlcount_label_0[lang]);
        $("#dlcount-range-label-1").html(localisation.dlcount_label_1[lang]);
        $("#dlcount-range-label-2").html(localisation.dlcount_label_2[lang]);
        $("#age-title").text(localisation.age_title[lang]);
        $("#age-checkbox-1-label").text(localisation.age_checkbox_1[lang]);
        $("#age-checkbox-2-label").text(localisation.age_checkbox_2[lang]);
        $("#age-checkbox-3-label").text(localisation.age_checkbox_3[lang]);
        $("#misc-title").text(localisation.misc_title[lang]);
        $("#misc-checkbox-1-label").text(localisation.misc_checkbox_1[lang]);
        $("#misc-checkbox-2-label").text(localisation.misc_checkbox_2[lang]);
        $("#misc-checkbox-3-label").text(localisation.misc_checkbox_3[lang]);
        $("#misc-checkbox-4-label").text(localisation.misc_checkbox_4[lang]);
        $("#misc-checkbox-5-label").text(localisation.misc_checkbox_5[lang]);
        $("#popularity-weight-title").text(localisation.popularity_weight_title[lang]);
        $("#popularity-weight-label-1").text(localisation.popularity_weight_label_1[lang]);
        $("#popularity-weight-label-2").text(localisation.popularity_weight_label_2[lang]);
        $("#popularity-weight-enabled").attr("aria-label", localisation.popularity_weight_title[lang]);
        $("#date-range-enabled").attr("aria-label", localisation.date_title[lang]);
        $("#dlcount-range-enabled").attr("aria-label", localisation.dlcount_title[lang]);
        $("#welcome-title").text(localisation.welcome_title[lang]);
        $("#welcome-version").text(`ver ${version}`);
        $("#welcome-subtitle").text(localisation.welcome_subtitle[lang]);
        $("#welcome-start-hint").html(localisation.welcome_start_hint[lang]);
        $("#welcome-start-hint-genres").attr("data-bs-toggle", "modal");
        $("#welcome-start-hint-genres").attr("data-bs-target", "#genre-modal");
        $("#welcome-start-hint-genres").attr("data-genre-action", "add");
        $("#welcome-info").html(localisation.welcome_info[lang]);
        $("#search-info").html(localisation.search_info[lang]);
        $("#catalog-title").text(localisation.catalog_title[lang]);
        $("#catalog-query").attr("placeholder", localisation.catalog_placeholder[lang]);
        $("#catalog-field").attr("aria-label", localisation.catalog_field_label[lang]);
        $("#catalog-field-all").text(localisation.catalog_field_all[lang]);
        $("#catalog-field-title").text(localisation.catalog_field_title[lang]);
        $("#catalog-field-artist").text(localisation.catalog_field_artist[lang]);
        $("#catalog-field-id").text(localisation.catalog_field_id[lang]);
        $("#catalog-search-btn").attr("aria-label", localisation_words.search[lang]);
        $("#catalog-age-btn-label").text(localisation.age_title[lang]);
        $("#catalog-age-1-label").text(localisation.age_checkbox_1[lang]);
        $("#catalog-age-2-label").text(localisation.age_checkbox_2[lang]);
        $("#catalog-age-3-label").text(localisation.age_checkbox_3[lang]);
        updateCatalogAgeSummary();
        applyTheme($("html").attr("data-bs-theme"));
        const next_lang = language_cycle[(language_cycle.indexOf(lang) + 1) % language_cycle.length];
        const language_label = `${localisation.language_button[lang]}: ${language_names[lang]} → ${language_names[next_lang]}`;
        $("#lang-toggle").attr({ "aria-label": language_label, "title": language_label });
        showLanguageGlyph();
        $("#similar-reset-label").text(localisation.reset_label[lang]);
        $("#similar-random-label").text(localisation.random_label[lang]);
        $("#catalog-hint").html(localisation.catalog_hint[lang]);
        $("#catalog-results-title").text(localisation[catalog_title_key || "catalog_results_title"][lang]);
        $("#keyword-tab-label").text(localisation.search_tab_keywords[lang]);
        $("#similar-tab-label").text(localisation.catalog_find_similar[lang]);
        const titles = {
            "#reset-search-btn, #similar-reset-btn": localisation.reset_search[lang],
            "#random-works-btn, #similar-random-btn": localisation.random_works[lang],
            "#preset-save-btn": localisation.preset_save[lang],
            "#preset-load-btn": localisation.preset_load[lang],
        };
        for (const id in titles) {
            $(id).attr({ "title": titles[id], "aria-label": titles[id] });
        }
        $("#preset-save-modal-title").text(localisation.preset_save[lang]);
        $("#preset-load-modal-title").text(localisation.preset_load[lang]);
        $("#preset-name-label").text(localisation.preset_name[lang]);
        $("#preset-save-hint").text(localisation.preset_save_hint[lang]);
        $("#preset-save-submit-label").text(localisation.preset_save_button[lang]);
        $("#preset-save-cancel, #preset-load-cancel").text(localisation.cancel[lang]);
        $("#preset-file-btn-label").text(localisation.preset_open_file[lang]);
    }

    // ---- language button: English -> Japanese -> Traditional Chinese -> Simplified Chinese -> English ----
    var locale_request_id = 0;

    function showInfo() {
        if (info_data) {
            $("#banner-text").html(info_data.length);
            $("#navbar-time").html(info_data.time);
        }
    }

    $("#lang-toggle").click(function () {
        changeLanguage(language_cycle[(language_cycle.indexOf(lang) + 1) % language_cycle.length]);
    });

    // The glyphs are created once; changing the language only moves them, which the CSS transition animates.
    function showLanguageGlyph() {
        const button = $("#lang-toggle");
        if (!button.children().length) {
            button.append(language_cycle.map(code => $("<span>", { "class": "lang-glyph lang-strip-glyph", "aria-hidden": "true" }).text(language_glyphs[code])));
        }
        const count = language_cycle.length;
        const current = language_cycle.indexOf(lang);
        button.children().each(function (index) {
            // -1 is the glyph that just left, 1 the next one, 2 the one after, hidden
            this.style.setProperty("--offset", ((index - current + 1 + count) % count) - 1);
            this.classList.toggle("active", index === current);
        });
    }

    function changeLanguage(next) {
        lang = next;
        lang_raw = next.replace("_", "-");
        try {
            localStorage.setItem("lang", lang);
        } catch (e) { }
        document.documentElement.lang = lang_raw;

        // texts of the page (this also resets the info lines, which are filled in again below)
        setLocaleText(lang);
        showInfo();
        setDateRangeText($("#date-range").val());
        if (!$("#search-info").hasClass("visually-hidden")) {
            const result_info = JSON.parse(localStorage.getItem("last_search_result_info"));
            if (result_info) {
                $("#search-info-count").text(result_info.length);
                $("#search-info-time").text(Math.round(result_info.time * 100) / 100);
            }
        }
        const rjid = $("#rjid").val().toUpperCase();
        if (rjid != "" && !rjid_regex.test(rjid)) {
            $("#rjid-work-name").text(localisation.work_input_hint_format[lang]);
        } else if (rjid != "") {
            showWorkName(rjid);
        }

        // names of the genres and work formats come from the server, in the chosen language
        const request_id = ++locale_request_id;
        $.getJSON("/api/locale/" + lang, data => {
            if (request_id != locale_request_id || data.state != "success") {
                return;
            }
            locale_data = data.locale;
            setGenreLocale(locale_data);
            setWorkFormatLocale(locale_data);
            $("#genre-search-bar").trigger("keyup");
            search_categories.forEach(id => $(`#workformat-${id}`).prop("checked", true));

            const rename_tags = (selector, attribute, table) => $(selector).each(function () {
                const item = locale_data[table][$(this).attr(attribute)];
                if (item) {
                    $(this).html(`${item.name} <i class="fa-solid fa-xmark"></i>`);
                }
            });
            rename_tags("a[data-genre-value]", "data-genre-value", "genres");
            rename_tags("a[data-workformat-value]", "data-workformat-value", "work_formats");

            refreshCatalogView();
            if (!$("#search-info").hasClass("visually-hidden") && localStorage.getItem("last_search_result_list")) {
                getSearchResults(current_page, () => { });
            }
        });
    }

    function addGenre(genre_type, genre_id) {
        genre_id = genre_id.toString();

        search_genres[genre_type].add(genre_id);
        switch (genre_type) {
            case "included":
                removeGenre("excluded", genre_id);
                break;
            case "excluded":
                removeGenre("included", genre_id);
                break;
            default:
                break;
        }

        var genre_html = $("<a>", {
            "class": `btn me-1 ${genre_class[genre_type]} rounded-pill btn-genre`,
            "role": "button",
            "data-genre-value": genre_id
        }).html(`${locale_data["genres"][genre_id]["name"]} <i class="fa-solid fa-xmark"></i>`);

        $("#selected-genre-container").append(genre_html);
        $(`#genre-${genre_type}-container`).append(genre_html.clone());
        if (genre_type == "add") {
            collapse_genres_container.show();
        }
        // hide the hint
        $(`#genre-${genre_type}-container-hint`).css("display", "none");
        $(`#selected-genre-container-hint`).css("display", "none");

        $("#selected-genre-size").text(search_genres[genre_type].size);
    }

    function removeGenre(genre_type, genre_id) {
        genre_id = genre_id.toString();
        search_genres[genre_type].delete(genre_id);

        $(`#selected-genre-container a[data-genre-value=${genre_id}]`).remove();
        $(`#genre-${genre_type}-container a[data-genre-value=${genre_id}]`).remove();
        if (genre_type == "add" && $("#genre-add-container").children().length == 0) {
            collapse_genres_container.hide();
        }
        // show the hint
        if ($(`#genre-${genre_type}-container`).children().length == 0) {
            $(`#genre-${genre_type}-container-hint`).css("display", "block");
        }
        if ($("#selected-genre-container").children().length == 0) {
            $(`#selected-genre-container-hint`).css("display", "block");
        }

        $("#selected-genre-size").text(search_genres[genre_type].size);
    }

    function addWorkFormat(workformat_id) {
        search_categories.add(workformat_id);
        var workformat_category_id = locale_data["work_formats"][workformat_id]["category_id"];
        var category_color = work_format_class[workformat_category_id];

        var workformat_html = $("<a>", {
            "class": `btn me-1 rounded-pill btn-genre text-${category_color}-emphasis bg-${category_color}-subtle border border-${category_color}-subtle`,
            "role": "button",
            "data-workformat-value": workformat_id
        }).html(`${locale_data["work_formats"][workformat_id]["name"]} <i class="fa-solid fa-xmark"></i>`);

        $(`#workformat-add-container`).append(workformat_html);
        $(`#workformat-add-container-hint`).css("display", "none");
    }

    function removeWorkFormat(workformat_id) {
        search_categories.delete(workformat_id);

        $(`#workformat-add-container a[data-workformat-value=${workformat_id}]`).remove();
        if ($(`#workformat-add-container`).children().length == 0) {
            $(`#workformat-add-container-hint`).css("display", "block");
        }
    }

    function setDateRangeText(value) {
        var release_date = monthFunc(months_from_start, value);
        $("#date-range-time").text(release_date.toLocaleDateString(lang_raw, {
            year: 'numeric',
            month: 'long'
        }));
        // print how many years and months ago
        var years = currentDate.getFullYear() - release_date.getFullYear();
        var months = currentDate.getMonth() - release_date.getMonth();
        if (months < 0) {
            years--;
            months += 12;
        }
        var years_str = years > 0 ? years + localisation_words.years[lang] : "";
        var months_str = months > 0 ? months + localisation_words.months[lang] : "";
        var ago_str = years_str + (years_str != "" && months_str != "" ? localisation_words.and_date[lang] : "") + months_str;
        if (ago_str == "") {
            ago_str = localisation_words.less_than_month[lang];
        }
        $("#date-range-ago").text(ago_str);
    }

    function getSearchResults(page, callback) {
        const start = (page - 1) * page_size;
        const end = start + page_size;
        var flag = false;

        // get the result data from local storage
        const result_info = JSON.parse(localStorage.getItem("last_search_result_info"));
        const result_list_all = JSON.parse(localStorage.getItem("last_search_result_list"));
        const result_list = result_list_all.slice(start, end);
        if (result_list.length == 0) {
            // no more results
        } else {
            current_page = page;

            // get the work info from the server
            const result_list_ids = result_list.map(result => result[0]);
            $.ajax({
                url: "/api/works?" + $.param({ rj_id: result_list_ids }, true),
                success: function (data) {
                    if (data.state == "success") {
                        $("#result-card-container").empty();
                        result_list.forEach(result => {
                            // prepare the work info
                            // result = [rj_id, similarity]
                            const rjid = result[0];
                            const similarity = Math.round(result[1] * 100, 1);
                            const work = data.works[rjid];

                            // prepare the html
                            const imgUrl = getImgUrl(rjid)
                            const workName = work.name;
                            const category = locale_data.work_formats[work.type].name;
                            const category_color = work_format_class[locale_data.work_formats[work.type].category_id];
                            const additionTypeTag = work.options.map(option => {
                                if (option in localisation_options) {
                                    option = localisation_options[option][lang];
                                }
                                unknown_option = ["ORW", "RE", "TRS", "workupdate"]
                                if (option != "REV" && option != "TRI" && !unknown_option.includes(option)) {
                                    return `<span class='badge rounded-pill shadow-sm text-dark-emphasis bg-light-subtle border border-dark-subtle'>${option}</span>`
                                } else {
                                    return "";
                                }
                            }).join(" ");
                            const workUrl = `https://www.dlsite.com/${work.siteId}/work/=/product_id/${rjid}.html`
                            const rating = work.rate / 10;
                            const ratingCount = work.rateCount;
                            const dlCount = work.dlCount;
                            const commentUrl = work.reviewCount == 0 ? "#" : `https://www.dlsite.com/${work.siteId}/work/reviewlist/=/product_id/${rjid}.html`;
                            const commentCount = work.reviewCount;
                            const artist = work.maker;
                            const date = work.registDate;
                            const description = work.description;
                            const tags = work.tags.map(genre => {
                                if (genre in locale_data.genres) {
                                    return `<span class='badge rounded-pill shadow-sm text-dark-emphasis bg-primary-subtle border border-primary-subtle'>${locale_data.genres[genre].name}</span>`
                                } else {
                                    return "";
                                }
                            }).join(" ");

                            const workCard = cardTemplate(imgUrl, workName, similarity, category_color, category, additionTypeTag, workUrl, rating, ratingCount, dlCount, commentUrl, commentCount, artist, date, description, tags, rjid);

                            $("#result-card-container").append(workCard);
                        });
                        $("#search-info-start").text(start + 1);
                        $("#search-info-end").text(Math.min(end, result_list_all.length));

                        // if is last page, show the message
                        if (end >= result_list_all.length) {
                            $("#search-end-of-result").css("display", "block");
                            if (result_info.length > end) {
                                $("#search-end-of-result").text(localisation.end_of_result[lang]);
                            } else {
                                $("#search-end-of-result").text(localisation.end_of_result_2[lang]);
                            }
                        } else {
                            $("#search-end-of-result").css("display", "none");
                        }
                        flag = true;
                    } else {
                        console.log(data.message);
                    }
                    callback(flag);
                },
                error: function (xhr, ajaxOptions, thrownError) {
                    console.log(xhr.status);
                    console.log(thrownError);
                    callback(flag);
                },
                timeout: 3000,
            });
        }
    }
});

function setGenreLocale(locale_data) {
    const genres = locale_data.genres;
    const genre_locale_dict = {};

    // Sort the locale data by category
    Object.keys(genres).sort().forEach(genre_id => {
        const genre = genres[genre_id];
        const category = genre.category;
        genre_locale_dict[category] = genre_locale_dict[category] || {};
        genre_locale_dict[category][genre_id] = { name: genre.name, count: genre.count };
    });

    // Put the locale data into the HTML
    $("#category-link-nav, #genre-container").empty();

    for (const category in genre_locale_dict) {
        const category_html = $("<div>", {
            "class": "category-container row p-2 mb-3 me-1 border rounded-3",
            "id": `scroll_${category}`
        }).append(
            $("<p>").html(`<b>${category}</b>`)
        );

        for (const genre_id in genre_locale_dict[category]) {
            const genre = genre_locale_dict[category][genre_id];
            category_html.append(
                $("<div>", { "class": "genre-item form-check" }).append(
                    $("<input>", {
                        "class": "form-check-input focus-ring",
                        "type": "checkbox",
                        "value": genre_id,
                        "id": `genre-${genre_id}`
                    }),
                    $("<label>", {
                        "class": "form-check-label",
                        "for": `genre-${genre_id}`
                    }).html(
                        `${genre["name"]} <span class="badge rounded-pill bg-light-subtle border border-light-subtle text-light-emphasis">${genre["count"]}</span>`
                    )
                )
            );
        }

        $("#category-link-nav").append(
            $("<a>", {
                "class": "nav-link fw-bold",
                "href": `#scroll_${category}`
            }).html(category)
        );
        $("#genre-container").append(category_html);
    }
}

function setWorkFormatLocale(locale_data) {
    const work_formats = locale_data.work_formats;
    const work_format_locale_dict = {};

    // Sort the locale data by category
    Object.keys(work_formats).sort().forEach(work_format_id => {
        const work_format = work_formats[work_format_id];
        const category = work_format.category;
        work_format_locale_dict[category] = work_format_locale_dict[category] || {};
        work_format_locale_dict[category][work_format_id] = work_format.name;
    });

    // Put the locale data into the HTML
    $("#categories-link-nav, #categories-container").empty();

    for (const category in work_format_locale_dict) {
        const category_html = $("<div>", {
            "class": "category-container row p-2 mb-3 me-1 border rounded-3",
            "id": `scroll_${category}`
        }).append(
            $("<p>").append(
                $("<input>", {
                    "class": "form-check-input me-2",
                    "type": "checkbox",
                    "value": category,
                    "id": `workformat-category-${category}`
                }),
                $("<label>", {
                    "class": "form-check-label",
                    "for": `workformat-category-${category}`
                }).html(`<b>${category}</b>`)
            )
        );

        for (const work_format_id in work_format_locale_dict[category]) {
            const work_format_name = work_format_locale_dict[category][work_format_id];
            category_html.append(
                $("<div>", { "class": "col-12 form-check" }).append(
                    $("<input>", {
                        "class": "form-check-input",
                        "type": "checkbox",
                        "value": work_format_id,
                        "id": `workformat-${work_format_id}`
                    }),
                    $("<label>", {
                        "class": "form-check-label",
                        "for": `workformat-${work_format_id}`
                    }).html(work_format_name)
                )
            );
        }

        $("#categories-link-nav").append(
            $("<a>", {
                "class": "nav-link fw-bold",
                "href": `#scroll_${category}`
            }).html(category)
        );
        $("#categories-container").append(category_html);
    }
}

function clearAddGenre() {
    search_genres["add"].clear();
    $("#genre-add-container").empty();
}

function getImgUrl(rjid, siteId) {
    // we need to round up to the nearest 1000
    // RJ01043707 -> RJ01044000
    // RJ210437 -> RJ210000
    if (/^RJ(?:\d{8})$/.test(rjid)) {
        var rjid_int = parseInt(rjid.slice(2, 10));
        rjid_int = Math.ceil(rjid_int / 1000) * 1000;
        rjid_int = rjid_int.toString().padStart(8, "0");
    } else if (/^RJ(?:\d{6})$/.test(rjid)) {
        var rjid_int = parseInt(rjid.slice(2, 8));
        rjid_int = Math.ceil(rjid_int / 1000) * 1000;
        rjid_int = rjid_int.toString().padStart(6, "0");
    } else {
        return "";
    }
    return `https://img.dlsite.jp/resize/images2/work/doujin/RJ${rjid_int}/${rjid}_img_main_240x240.jpg`;
}

function monthFunc(months_from_start, value) {
    const factor = 1;
    try {
        const months_after = Math.log(value / factor + 1) / Math.log(100 / factor + 1) * months_from_start;
        const endDate = new Date(startDate.getFullYear(), startDate.getMonth() + months_after, startDate.getDate());
        return endDate;
    } catch (error) {
        console.error(error);
        return startDate;
    }
}