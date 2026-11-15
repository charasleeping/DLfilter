/* One state and one request path for keyword, browse and similarity discovery. */
const search_genres = { add: new Set(), included: new Set(), excluded: new Set() };
const search_categories = new Set();
const genre_class = { add: "text-primary-emphasis bg-primary-subtle border", included: "text-success-emphasis bg-success-subtle border", excluded: "text-danger-emphasis bg-danger-subtle border" };
const work_format_class = { Game: "primary", Manga: "success", "CG + Illustrations": "info", Novel: "light", Video: "primary", "Voice / ASMR": "warning", Music: "warning", "Tools / Accessories": "light", Miscellaneous: "light" };
const rjid_regex = /^(?:RJ|BJ|VJ)(?:[0-9]{8}|[0-9]{6})$/;
const normalizeProductId = value => String(value || "").normalize("NFKC").trim().toUpperCase();
const page_size = 48;
const version = "2.1";
const popularity_weight_func = [1, 4, 2];
const startDate = new Date(2000, 0, 1);
const currentDate = new Date();
const months_from_start = (currentDate.getFullYear() - 2000) * 12 + currentDate.getMonth();
const SETTINGS_KEY = "dlfilter.search.v1";
function readSettings() {
    try {
        const saved = JSON.parse(localStorage.getItem(SETTINGS_KEY));
        return saved && saved.version === 1 && saved.settings && typeof saved.settings === "object" ? saved : null;
    } catch (_) { return null; }
}
const saved_settings = readSettings();
var lang_raw = navigator.language || "en-US";
var lang = lang_raw.replace("-", "_");
try { lang = saved_settings?.language || localStorage.getItem("lang") || lang; } catch (_) { }
if (!supported_lang.includes(lang)) lang = "en_US";
lang_raw = lang.replace("_", "-");
var locale_data = null;

$(document).ready(function () {
    let ready = false, restoring = false, request_id = 0, copy_id = 0, locale_id = 0;
    let reference_id = "", reference_name = "", view = null, query_snapshot = null, random_view = false;
    let last_preset_name = "", copy_open = false, return_copy_focus = false;
    var catalog_title_key = "catalog_results_title";
    const collapse_welcome_banner = bootstrap.Collapse.getOrCreateInstance("#welcome-banner", { toggle: false });
    const copy_content = document.getElementById("copy-tags-content");
    const popover = new bootstrap.Popover(document.getElementById("copy-tags-btn"), {
        trigger: "manual", html: true, sanitize: false, placement: "right", fallbackPlacements: ["bottom", "left", "top"],
        content: () => copy_content, customClass: "copy-tags-popover", container: "body",
    });
    function t(key) { return localisation[key]?.[lang] || key; }
    function showSearchTab() { document.getElementById("search-panel").scrollIntoView({ block: "start", behavior: "smooth" }); }
    function updateCatalogAgeSummary() { }
    function showLanguageGlyph() {
        const button = $("#lang-toggle");
        const initial = !button.children().length;
        if (initial) {
            button.addClass("lang-initializing").append(language_cycle.map(code => $("<span>", {
                class: "lang-glyph lang-strip-glyph", "aria-hidden": "true"
            }).text(language_glyphs[code])));
        }
        const current = language_cycle.indexOf(lang), count = language_cycle.length;
        button.children().each(function (index) {
            this.style.setProperty("--offset", ((index - current + 1 + count) % count) - 1);
            this.classList.toggle("active", index === current);
        });
        if (initial) requestAnimationFrame(() => requestAnimationFrame(() => button.removeClass("lang-initializing")));
    }
    function renderWelcome() {
        $(".welcome-section-highlight").removeClass("welcome-section-highlight");
        const targets = { keywords: "catalog-search-form", genres: "genre-selection-section", formats: "format-selection-section" };
        const template = localisation.welcome_links[lang];
        const labels = localisation.welcome_link_labels[lang];
        const container = $("#welcome-start-hint").empty();
        template.split(/(\{keywords\}|\{genres\}|\{formats\})/).forEach(part => {
            const key = part.slice(1, -1);
            if (Object.hasOwn(targets, key)) container.append($("<button>", { type: "button", class: "welcome-hint-link", "data-section": targets[key], "data-term": key }).text(labels[key]));
            else container.append(document.createTextNode(part));
        });
    }
    function updateWelcomeHighlights() {
        $(".welcome-section-highlight").removeClass("welcome-section-highlight");
        $(".welcome-hint-link").each(function () {
            if (this.matches(":hover") || this === document.activeElement) document.getElementById(this.dataset.section).classList.add("welcome-section-highlight");
        });
    }
    $("#welcome-start-hint").on("mouseenter mouseleave focusin focusout", ".welcome-hint-link", () => requestAnimationFrame(updateWelcomeHighlights))
        .on("click", ".welcome-hint-link", function () {
            const target = this.dataset.term === "keywords" ? document.getElementById("catalog-query") : document.getElementById(this.dataset.term === "genres" ? "genre-title" : "workformat-title");
            target.scrollIntoView({ block: "nearest", behavior: "smooth" }); target.focus({ preventScroll: true });
        });
    function showInfo() { $.getJSON("/api/info").done(d => { if (d.state === "success") { $("#banner-text").text(d.length); $("#navbar-time").text(d.time); } }); }
    function applyTheme(theme) {
        theme = theme === "dark" ? "dark" : "light";
        document.documentElement.dataset.bsTheme = theme;
        $("#dark-toggle").attr({ "aria-label": t(theme === "dark" ? "theme_to_light" : "theme_to_dark"), title: t(theme === "dark" ? "theme_to_light" : "theme_to_dark") })
            .html(`<svg class="theme-icon" viewBox="0 0 24 24" width="1.6em" height="1.6em" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${theme === "dark" ? '<path d="M19.5 17.5A9 9 0 1 1 9.5 3.3C5 11 11 19 19.5 17.5Z"/>' : '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>'}</svg>`);
        $("#dark-toggle, #lang-toggle").toggleClass("btn-outline-light", theme === "dark").toggleClass("btn-outline-dark", theme !== "dark");
    }
    function refreshLabels() {
        setLocaleText(lang);
        $("#search-title").html(`<i class="fa-solid fa-magnifying-glass"></i> ${localisation_words.search[lang]}`);
        $("#catalog-hint").html(t("unified_hint"));
        $("#catalog-query").attr("placeholder", t("product_search_placeholder"));
        $("#catalog-field-id").text(t("product_id"));
        $("#rjid").attr("placeholder", "RJ123456 / BJ01234567 / VJ01234567");
        $("#copy-tags-btn").attr({ "aria-label": t("copy_tags"), title: t("copy_tags") });
        $("#copy-tags-submit").text(t("copy_button"));
        $("#rjid-title").text(t("copy_tags"));
        $("#genre-add-container-hint, #workformat-add-container-hint").text(t("not_selected"));
        $("#scoring-hint").text(t("scoring_hint"));
        renderWelcome();
        $("#reference-work").empty();
        if (reference_id) $("#reference-work").append($("<span>").text(`${t("reference_work")}: ${reference_name || reference_id} `),
            $("<button>", { type: "button", class: "btn btn-sm btn-link", id: "clear-reference", "aria-label": t("clear_reference") }).text("×"));
        document.documentElement.lang = lang_raw;
        setDateRangeText($("#date-range").val());
        showInfo();
    }
    function invalidate() { request_id++; $("#catalog-spinner").addClass("d-none"); }
    function persist() {
        if (!ready || restoring) return;
        try {
            localStorage.setItem(SETTINGS_KEY, JSON.stringify({ version: 1, settings: currentPreset(), language: lang, theme: document.documentElement.dataset.bsTheme }));
            localStorage.setItem("lang", lang);
        } catch (_) { }
    }
    function changed() { invalidate(); persist(); }
    function currentPreset() {
        const slider = (name, id) => ({ enabled: $(`#${name}`).prop("checked"), value: Number($(`#${id}`).val()) });
        return { q: $("#catalog-query").val(), field: $("#catalog-field").val(), rj_id: reference_id,
            genres: [...search_genres.add], included_genres: [...search_genres.included], excluded_genres: [...search_genres.excluded], categories: [...search_categories],
            popularity_weight: slider("popularity-weight-enabled", "popularity-weight-range"), release_date: slider("date-range-enabled", "date-range"),
            download_count: slider("dlcount-range-enabled", "dlcount-range"), ages: [1, 2, 3].map(i => $(`#age-checkbox-${i}`).prop("checked")),
            excluded_contents: [1, 2, 3, 4, 5].map(i => $(`#misc-checkbox-${i}`).prop("checked")), advanced_options_open: $("#advanced-options-panel").hasClass("show") };
    }
    const default_preset = currentPreset();
    function renderSelections() {
        for (const type of ["add", "included", "excluded"]) {
            const container = $(`#genre-${type}-container`).empty();
            search_genres[type].forEach(id => container.append($("<button>", { type: "button", class: `btn me-1 rounded-pill btn-genre ${genre_class[type]}`, "data-remove-genre": id, "data-type": type }).text(`${locale_data.genres[id].name} ×`)));
            $(`#genre-${type}-container-hint`).toggle(search_genres[type].size === 0);
        }
        $("#workformat-add-container").empty().append([...search_categories].map(id => $("<button>", { type: "button", class: "btn btn-genre rounded-pill bg-primary-subtle me-1", "data-remove-format": id }).text(`${locale_data.work_formats[id].name} ×`)));
        $("#workformat-add-container-hint").toggle(search_categories.size === 0);
        updateSliders();
    }
    function updateSliders() {
        $(".advanced-option").each(function () {
            const scoring = $(this).find("#popularity-weight-enabled, #dlcount-range-enabled").length > 0;
            const unavailable = scoring && search_genres.add.size === 0;
            const on = $(this).find("input[role=switch]").prop("checked");
            $(this).find("input[role=switch]").prop("disabled", unavailable);
            $(this).find("input[type=range]").prop("disabled", unavailable || !on);
            $(this).toggleClass("is-off", unavailable || !on).find(".btn-add").toggleClass("disabled", unavailable || !on);
        });
        $("#scoring-hint").toggle(search_genres.add.size === 0);
    }
    function applyPreset(raw) {
        const p = raw && typeof raw === "object" && !Array.isArray(raw) ? { ...default_preset, ...raw } : default_preset;
        restoring = true;
        copy_id++;
        for (const [type, key] of [["add", "genres"], ["included", "included_genres"], ["excluded", "excluded_genres"]]) {
            search_genres[type].clear();
            if (Array.isArray(p[key])) p[key].map(String).filter(id => Object.hasOwn(locale_data.genres, id)).forEach(id => search_genres[type].add(id));
        }
        search_genres.excluded.forEach(id => search_genres.included.delete(id));
        search_categories.clear();
        if (Array.isArray(p.categories)) p.categories.map(String).filter(id => Object.hasOwn(locale_data.work_formats, id)).forEach(id => search_categories.add(id));
        reference_id = rjid_regex.test(normalizeProductId(p.rj_id)) ? normalizeProductId(p.rj_id) : "";
        reference_name = "";
        $("#rjid").val(reference_id); $("#rjid-work-name").empty();
        $("#catalog-query").val(typeof p.q === "string" ? p.q.slice(0, 100) : "");
        $("#catalog-field").val(["all", "title", "artist", "id"].includes(p.field) ? p.field : "all");
        for (const [key, enabled, range] of [["popularity_weight", "popularity-weight-enabled", "popularity-weight-range"], ["release_date", "date-range-enabled", "date-range"], ["download_count", "dlcount-range-enabled", "dlcount-range"]]) {
            const option = p[key] || default_preset[key];
            $(`#${enabled}`).prop("checked", option.enabled === true);
            $(`#${range}`).val(Number.isFinite(Number(option.value)) ? Number(option.value) : default_preset[key].value);
        }
        for (const [key, count, prefix] of [["ages", 3, "age"], ["excluded_contents", 5, "misc"]]) {
            const flags = Array.isArray(p[key]) && p[key].length === count ? p[key] : default_preset[key];
            flags.forEach((on, i) => $(`#${prefix}-checkbox-${i + 1}`).prop("checked", on === true));
        }
        const panel = bootstrap.Collapse.getOrCreateInstance("#advanced-options-panel", { toggle: false });
        p.advanced_options_open ? panel.show() : panel.hide();
        renderSelections(); refreshLabels(); restoring = false; changed();
    }
    function requestParams() {
        const p = currentPreset();
        const params = { q: p.q.trim(), field: p.field, ages: p.ages.map(x => x ? "1" : "0").join(""), excluded_low_rate: p.excluded_contents[0] };
        for (const key of ["genres", "included_genres", "excluded_genres", "categories"]) {
            const ids = p[key].slice(0, key === "included_genres" || key === "excluded_genres" ? 5 : undefined);
            if (ids.length) params[key] = ids.join("+");
        }
        params.excluded_options = ["AIG", "AIP", "GRO", "MEN"].filter((_, i) => p.excluded_contents[i + 1]).join("+");
        if (reference_id) params.rj_id = reference_id;
        if (p.release_date.enabled) {
            const date = monthFunc(months_from_start, p.release_date.value);
            params.since = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-01`;
        }
        params.weight_func = p.popularity_weight.enabled ? popularity_weight_func[p.popularity_weight.value] : 4;
        params.dlcount = p.download_count.enabled ? p.download_count.value : 50;
        return params;
    }
    function renderView() {
        if (!view) return;
        $("#catalog-card-container").empty().append(view.results.map(w => catalogCardTemplate(w, t("copy_tags"))));
        $("#catalog-results-title").text(t(random_view ? "random_results_title" : "catalog_results_title"));
        const total = random_view ? view.results.length : view.total;
        $("#catalog-status").text(!total ? t("catalog_no_results") : random_view ? t("random_summary").replace("{count}", total) : t("catalog_summary").replace(/<[^>]*>/g, " ").replace("{total}", total).replace("{start}", view.results.length ? (view.page - 1) * page_size + 1 : 0).replace("{end}", Math.min(view.page * page_size, total)));
        const pages = random_view ? 1 : Math.ceil(total / page_size), current = view.page || 1;
        const container = $("#catalog-pagination").empty();
        if (pages > 1) {
            const add = (label, page, disabled, active = false) => container.append($("<li>", { class: `page-item ${active ? "active" : ""} ${disabled ? "disabled" : ""}` }).append($("<button>", { type: "button", class: "page-link", "data-page": page, disabled, "aria-current": active ? "page" : null }).text(label)));
            add("‹", current - 1, current === 1);
            const visible = [...new Set([1, current - 1, current, current + 1, pages])].filter(p => p > 0 && p <= pages).sort((a, b) => a - b);
            let previous = 0;
            visible.forEach(p => { if (p - previous > 1) add("…", 0, true); add(p, p, false, p === current); previous = p; });
            add("›", current + 1, current === pages);
        }
    }
    function runSearch(page = 1, random = false, newQuery = true) {
        if (!ready) return;
        if (newQuery) { query_snapshot = requestParams(); persist(); }
        const token = ++request_id;
        random_view = random; view = null;
        $("#catalog-results-section").removeClass("d-none"); collapse_welcome_banner.hide();
        $("#catalog-card-container, #catalog-pagination").empty();
        $("#catalog-status").text(t("catalog_searching")); $("#catalog-spinner").removeClass("d-none");
        const params = { ...query_snapshot, page, page_size, count: page_size };
        if (random) { delete params.genres; delete params.rj_id; }
        $.ajax({ url: random ? "/api/random" : "/api/search", data: params, dataType: "json", timeout: 60000 })
            .done(data => { if (token !== request_id) return; if (data.state !== "success") { $("#catalog-status").text(t("catalog_error")); return; } view = data; renderView(); })
            .fail(() => { if (token === request_id) $("#catalog-status").text(t("catalog_error")); })
            .always(() => { if (token === request_id) $("#catalog-spinner").addClass("d-none"); });
    }
    function copyTags(id) {
        const workno = normalizeProductId(id), token = ++copy_id;
        if (!rjid_regex.test(workno)) { $("#rjid-work-name").text(t("product_id_invalid")); return; }
        $("#rjid-work-name").text(t("catalog_searching"));
        $.ajax({ url: "/api/works", data: { rj_id: workno }, dataType: "json", timeout: 10000 })
            .done(data => {
                if (token !== copy_id) return;
                if (data.state !== "success") { $("#rjid-work-name").text(t("catalog_error")); return; }
                const work = data.works[workno];
                if (!work || !work.index) { $("#rjid-work-name").text(t("work_not_in_local_db")); return; }
                const tags = (work.tags || []).filter(id => Object.hasOwn(locale_data.genres, id));
                if (!tags.length) { $("#rjid-work-name").text(t("no_copy_tags")); return; }
                tags.forEach(id => search_genres.add.add(id));
                reference_id = workno; reference_name = work.name; $("#rjid").val(workno);
                renderSelections(); refreshLabels(); $("#rjid-work-name").text(work.name); changed();
            }).fail(() => { if (token === copy_id) $("#rjid-work-name").text(t("catalog_error")); });
    }
    function hideCopy(returnFocus = false) {
        copy_open = false; return_copy_focus = returnFocus; popover.hide();
        $("#copy-tags-btn").attr("aria-expanded", "false");
    }
    $("#copy-tags-btn").on("click", () => {
        copy_open = !copy_open;
        $("#copy-tags-btn").attr("aria-expanded", String(copy_open));
        copy_open ? popover.show() : hideCopy();
    });
    $("#copy-tags-btn").on("shown.bs.popover", () => {
        if (!copy_open) { popover.hide(); return; }
        $("#copy-tags-btn").attr("aria-expanded", "true"); document.getElementById("rjid").focus();
    }).on("hidden.bs.popover", () => {
        document.getElementById("copy-tags-store").append(copy_content);
        $("#copy-tags-btn").attr("aria-expanded", "false");
        if (return_copy_focus) { return_copy_focus = false; document.getElementById("copy-tags-btn").focus({ preventScroll: true }); }
    });
    $(document).on("click", event => {
        if (!$(event.target).closest("#copy-tags-btn, .copy-tags-popover, .catalog-find-similar").length) hideCopy();
    }).on("keydown", event => {
        if (event.key === "Escape" && copy_open) { event.preventDefault(); event.stopPropagation(); hideCopy(true); }
    });
    $("#copy-tags-form").on("submit", event => { event.preventDefault(); copyTags($("#rjid").val()); });
    $("#rjid").on("input", () => { copy_id++; $("#rjid-work-name").empty(); });
    $("#reference-work").on("click", "#clear-reference", () => { reference_id = reference_name = ""; copy_id++; refreshLabels(); changed(); });
    $("#catalog-card-container").on("click", ".catalog-find-similar", function () { copy_open = true; $("#copy-tags-btn").attr("aria-expanded", "true"); popover.show(); $("#rjid").val($(this).attr("data-rjid")); copyTags($(this).attr("data-rjid")); });
    $("#catalog-search-form").on("submit", event => { event.preventDefault(); runSearch(); });
    $("#search-btn").on("click", () => runSearch());
    $("#similar-random-btn").on("click", () => runSearch(1, true));
    $("#catalog-pagination").on("click", "button[data-page]:not(:disabled)", function () { runSearch(Number($(this).attr("data-page")), false, false); });
    $("#similar-reset-btn").on("click", () => { applyPreset(default_preset); view = query_snapshot = null; hideCopy(); $("#catalog-results-section").addClass("d-none"); $("#catalog-card-container, #catalog-pagination").empty(); collapse_welcome_banner.show(); });
    $("#search-panel").on("input change", "input, select", function () { if (this.id !== "rjid") { updateSliders(); setDateRangeText($("#date-range").val()); changed(); } });
    $("#advanced-options-panel").on("shown.bs.collapse hidden.bs.collapse", persist);
    $("#search-terms-container").on("click", "[data-remove-genre]", function () { search_genres[$(this).attr("data-type")].delete($(this).attr("data-remove-genre")); renderSelections(); changed(); })
        .on("click", "[data-remove-format]", function () { search_categories.delete($(this).attr("data-remove-format")); renderSelections(); changed(); });
    $("#genre-modal").on("show.bs.modal", function (event) {
        const type = $(event.relatedTarget).attr("data-genre-action") || "add";
        $(this).attr("data-action", type);
        $("#genre-container input").each(function () { this.checked = search_genres[type].has(this.value); });
        $("#genre-modal-title").text(t(type === "add" ? "search_genres_modal_title" : `${type}_genres_modal_title`));
        $("#modal-desc").text(t("selected_genres_hint"));
        $("#selected-genre-container").empty();
    });
    $("#genre-container").on("change", "input", function () {
        const type = $("#genre-modal").attr("data-action"), id = this.value;
        this.checked ? search_genres[type].add(id) : search_genres[type].delete(id);
        if (this.checked && type !== "add") search_genres[type === "included" ? "excluded" : "included"].delete(id);
        renderSelections(); changed();
    });
    $("#btn-genre-clear").on("click", () => { search_genres[$("#genre-modal").attr("data-action")].clear(); $("#genre-container input").prop("checked", false); renderSelections(); changed(); });
    $("#genre-search-bar").on("input", function () {
        const q = this.value.toLocaleLowerCase();
        $("#genre-container .genre-item").each(function () { $(this).toggle($(this).text().toLocaleLowerCase().includes(q)); });
    });
    $("#workformat-modal").on("show.bs.modal", () => { $("#categories-container div input").each(function () { this.checked = search_categories.has(this.value); }); });
    $("#categories-container").on("change", "input", function () {
        const ids = Object.hasOwn(locale_data.work_formats, this.value) ? [this.value] : $(this).closest(".category-container").find("div input").map((_, x) => x.value).get();
        ids.forEach(id => this.checked ? search_categories.add(id) : search_categories.delete(id));
        $(this).closest(".category-container").find("div input").each(function () { this.checked = search_categories.has(this.value); });
        renderSelections(); changed();
    });
    for (const [button, input, value] of [["date", "date-range", 5], ["dlcount", "dlcount-range", 50], ["popularity-weight", "popularity-weight-range", 1]]) {
        $(`#${button}-reset-btn`).on("click", function () { if ($(this).hasClass("disabled")) return; $(`#${input}`).val(value).trigger("input"); });
    }
    let themeTransition = null;
    $("#dark-toggle").on("click", function () {
        if (themeTransition) return;
        const next = document.documentElement.dataset.bsTheme === "dark" ? "light" : "dark";
        const update = () => { applyTheme(next); persist(); };
        if (!document.startViewTransition) { update(); return; }
        const rect = this.getBoundingClientRect();
        const x = rect.left + rect.width / 2, y = rect.top + rect.height / 2;
        const radius = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));
        const transition = document.startViewTransition(update);
        themeTransition = transition;
        transition.ready.then(() => {
            if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
            document.documentElement.animate(
                { clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${radius}px at ${x}px ${y}px)`] },
                { duration: 600, easing: "ease-in-out", pseudoElement: "::view-transition-new(root)" }
            );
        }).catch(() => { });
        transition.finished.catch(() => { }).finally(() => { themeTransition = null; });
    });
    function changeLanguage(next) {
        lang = next; lang_raw = next.replace("_", "-"); refreshLabels(); persist();
        const token = ++locale_id;
        $.getJSON("/api/locale/" + lang).done(data => {
            if (token !== locale_id || data.state !== "success") return;
            locale_data = data.locale; setGenreLocale(locale_data); setWorkFormatLocale(locale_data); renderSelections(); renderView();
        });
    }
    $("#lang-toggle").on("click", () => changeLanguage(language_cycle[(language_cycle.indexOf(lang) + 1) % language_cycle.length]));
    $("#preset-save-modal").on("show.bs.modal", () => {
        $("#preset-name").val(last_preset_name).removeClass("is-invalid");
        $.getJSON("/api/presets").done(data => $("#preset-name-list").empty().append(data.presets.map(p => $("<option>", { value: p.name }))));
    });
    $("#preset-save-form").on("submit", event => {
        event.preventDefault(); const name = $("#preset-name").val().trim();
        if (!/^[\p{L}\p{N}\p{M}_\- ]{1,60}$/u.test(name)) { $("#preset-name").addClass("is-invalid"); $("#preset-save-error").text(t("preset_name_invalid")); return; }
        $("#preset-save-submit").prop("disabled", true);
        $.ajax({ type: "PUT", url: "/api/presets/" + encodeURIComponent(name), data: JSON.stringify(currentPreset()), contentType: "application/json" })
            .done(() => { last_preset_name = name; bootstrap.Modal.getOrCreateInstance("#preset-save-modal").hide(); })
            .fail(xhr => { $("#preset-name").addClass("is-invalid"); $("#preset-save-error").text(t(xhr.status === 409 ? "preset_too_many" : "preset_save_failed")); })
            .always(() => $("#preset-save-submit").prop("disabled", false));
    });
    function finishPresetLoad(p, name) {
        applyPreset(p); last_preset_name = name;
        const modal = bootstrap.Modal.getOrCreateInstance("#preset-load-modal");
        $("#preset-load-modal").one("shown.bs.modal", () => modal.hide());
        modal.hide();
    }
    $("#preset-load-modal").on("show.bs.modal", () => {
        $("#preset-list").empty(); $("#preset-list-status").removeClass("d-none").text(t("catalog_searching"));
        $.getJSON("/api/presets").done(data => {
            $("#preset-folder").text(data.folder + "/"); $("#preset-list-status").text(data.presets.length ? "" : t("preset_none"));
            $("#preset-list").append(data.presets.map(p => $("<button>", { type: "button", class: "list-group-item list-group-item-action", "data-preset": p.name }).text(p.name)));
        }).fail(() => $("#preset-list-status").text(t("preset_load_failed")));
    });
    $("#preset-list").on("click", "[data-preset]", function () { const name = $(this).attr("data-preset"); $.getJSON("/api/presets/" + encodeURIComponent(name)).done(d => finishPresetLoad(d.preset, name)).fail(() => $("#preset-list-status").text(t("preset_load_failed"))); });
    $("#preset-file-btn").on("click", () => $("#preset-file-input").val("").trigger("click"));
    $("#preset-file-input").on("change", function () {
        const file = this.files[0]; if (!file) return;
        const fail = () => $("#preset-list-status").removeClass("d-none").text(t("preset_load_failed"));
        if (file.size > 100000) { fail(); return; }
        file.text().then(text => { const p = JSON.parse(text); if (!p || typeof p !== "object" || Array.isArray(p)) throw Error(); finishPresetLoad(p, file.name.replace(/\.json$/i, "")); }).catch(fail);
    });
    function setDateRangeText(value) { $("#date-range-time").text(monthFunc(months_from_start, value).toLocaleDateString(lang_raw, { year: "numeric", month: "long" })); $("#date-range-ago").text(""); }
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

    applyTheme(saved_settings?.theme || "light"); refreshLabels();
    $("#search-btn, #similar-random-btn, #preset-save-btn, #preset-load-btn, #copy-tags-btn").prop("disabled", true);
    $.getJSON("/api/locale/" + lang).done(data => {
        if (data.state !== "success") return;
        locale_data = data.locale; setGenreLocale(locale_data); setWorkFormatLocale(locale_data);
        applyPreset(saved_settings?.settings || default_preset); ready = true; persist();
        $("#search-btn, #similar-random-btn, #preset-save-btn, #preset-load-btn, #copy-tags-btn").prop("disabled", false);
    }).fail(() => $("#scoring-hint").text(t("catalog_error")));
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

function getImgUrl(id, imageUrl) {
    if (typeof imageUrl === "string") {
        try { const url = new URL(imageUrl, "https://img.dlsite.jp"); if (url.protocol === "https:" && url.hostname === "img.dlsite.jp") return url.href; } catch (_) { }
    }
    if (!rjid_regex.test(id)) return "";
    const prefix = id.slice(0, 2), digits = id.slice(2);
    const bucket = String(Math.ceil(Number(digits) / 1000) * 1000).padStart(digits.length, "0");
    const folder = { RJ: "doujin", BJ: "books", VJ: "professional" }[prefix];
    return `https://img.dlsite.jp/resize/images2/work/${folder}/${prefix}${bucket}/${id}_img_main_240x240.jpg`;
}
function monthFunc(months, value) { return new Date(2000, Math.floor(Math.log(Number(value) + 1) / Math.log(101) * months), 1); }
