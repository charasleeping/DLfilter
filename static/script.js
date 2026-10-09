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

const version = "alpha 0.5";
const rjid_regex = /^RJ(?:\d{8}|\d{6})$/;
const page_size = 48;

const startDate = new Date(2000, 0, 1);
const currentDate = new Date();
const months_from_start = (currentDate.getFullYear() - startDate.getFullYear()) * 12 + currentDate.getMonth() - startDate.getMonth();

var locale_data = null;
var current_page = 1;

// check the language of the browser
var lang_raw = navigator.language || navigator.userLanguage;
// lang_raw = "ja-JP";
var lang = lang_raw.replace("-", "_");
if (supported_lang.indexOf(lang) == -1) {
    lang = "en_US";
}

$(document).ready(function () {
    // initialize the collapses
    var collapse_carousel = new bootstrap.Collapse($("#carousel-container"), {
        toggle: false
    });
    var collapse_genres_container = new bootstrap.Collapse($("#collapse-genres-container"), {
        toggle: false
    });
    var collapse_welcome_hint = new bootstrap.Collapse($("#welcome-start-hint"), {
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
        $("#banner-text").html(data.length);
        $("#navbar-time").html(data.time);
    });

    // go to top button
    $("#go-top-btn").click(function () {
        $("#result-panel").animate({
            scrollTop: 0
        }, 500);
    });

    // set up interaction for start text
    $("#welcome-start-hint-genres").hover(function () {
        $("#genre-title").css("color", "var(--bs-primary)");
        $(".fa-tags").css("color", "var(--bs-primary)");
    }, function () {
        $("#genre-title").css("color", "");
        $(".fa-tags").css("color", "");
    });
    $("#welcome-start-hint-workid").hover(function () {
        $("#rjid").focus();
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

    // set up the genre when it is clicked
    $("#genre-container").on("change", ".col-4 input[type=checkbox]", function () {
        var genre_id = $(this).val();
        var genre_type = $('#selected-genre-container').attr('data-genre-action');
        if (this.checked) {
            addGenre(genre_type, genre_id);
        } else {
            removeGenre(genre_type, genre_id);
        }
    });
    // set up the work format when it is clicked
    $("#categories-container").on("change", ".col-4 input[type=checkbox]", function () {
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
    $("#dark-toggle").click(function () {
        // data-bs-theme
        if ($("html").attr("data-bs-theme") == "dark") {
            $("html").attr("data-bs-theme", "light");
            $("#dark-toggle").removeClass("btn-outline-light").addClass("btn-outline-dark");
            $("#dark-toggle").html(`<i class="fa-solid fa-moon"></i>`);
        } else {
            $("html").attr("data-bs-theme", "dark");
            $("#dark-toggle").removeClass("btn-outline-dark").addClass("btn-outline-light");
            $("#dark-toggle").html(`<i class="fa-solid fa-sun"></i>`);
        }
    });

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
                            console.log(data["message"]);
                            $("#rjid-work-name").text(localisation.work_not_found[lang]);
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
            $("#rjid-work-name").text(localisation.work_input_hint[lang]);
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
        $(".page-link").removeClass("active");
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
        collapse_carousel.show();
        collapse_welcome_hint.show();
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

    // post the search data to the server
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

        // set the excluded options
        excluded_options = new Set();
        if ($("#misc-checkbox-2").prop("checked")) {
            excluded_options.add("AIG");
        }
        if ($("#misc-checkbox-3").prop("checked")) {
            excluded_options.add("AIP");
        }
        if ($("#misc-checkbox-4").prop("checked")) {
            excluded_options.add("GRO");
        }
        if ($("#misc-checkbox-5").prop("checked")) {
            excluded_options.add("MEN");
        }
        excluded_options = Array.from(excluded_options).join("+") || null;

        // hide the result container and show the loading animation
        $("#loading-spinner-container").removeClass("visually-hidden");
        if (!$("#search-info").hasClass("visually-hidden")) {
            $("#search-info").addClass("visually-hidden");
        }
        if ($("#carousel-container").hasClass("show")) {
            collapse_carousel.hide();
        }
        if ($("#welcome-start-hint").hasClass("show")) {
            collapse_welcome_hint.hide();
        }
        if ($("#result-card-container").hasClass("show")) {
            collapse_result_card_container.hide();
        }

        // send the search data to the server
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
                date: monthFunc(months_from_start, $("#date-range").val()),
                dlcount: $("#dlcount-range").val(),
                weight_func: $("#genre-weight-select").val(),
                excluded_low_rate: $("#misc-checkbox-1").prop("checked"),
                excluded_options: excluded_options,
                // "excluding_interest"
            }),
            contentType: "application/json",
            success: function (data) {
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
                    $(".page-link").first().addClass("active");

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
        $("#rjid-work-name").text(localisation.work_input_hint[lang]);
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
        $("#genre-weight-title").text(localisation.genre_weight_title[lang]);
        $("#genre-weight-option-1").text(localisation.genre_weight_option_1[lang]);
        $("#genre-weight-option-2").text(localisation.genre_weight_option_2[lang]);
        $("#genre-weight-option-3").text(localisation.genre_weight_option_3[lang]);
        $("#genre-weight-option-4").text(localisation.genre_weight_option_4[lang]);
        $("#welcome-title").text(localisation.welcome_title[lang]);
        $("#welcome-version").text(`/${version}`);
        $("#welcome-subtitle").text(localisation.welcome_subtitle[lang]);
        $("#welcome-start-hint").html(localisation.welcome_start_hint[lang]);
        $("#welcome-start-hint-genres").attr("data-bs-toggle", "modal");
        $("#welcome-start-hint-genres").attr("data-bs-target", "#genre-modal");
        $("#welcome-start-hint-genres").attr("data-genre-action", "add");
        $("#welcome-info").html(localisation.welcome_info[lang]);
        $("#search-info").html(localisation.search_info[lang]);
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
                $("<div>", { "class": "col-4 form-check" }).append(
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
                $("<div>", { "class": "col-4 form-check" }).append(
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