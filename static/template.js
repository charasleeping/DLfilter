function cardTemplate(
    imgUrl,
    workName,
    similarity,
    category_color,
    category,
    additionTypeTag,
    workUrl,
    rating,
    ratingCount,
    dlCount,
    commentUrl,
    commentCount,
    artist,
    date,
    desciption,
    Tags,
    rjid) {
    const cardTemplate = `
    <div class="col-xxl-3 col-xl-4 col-sm-6 col-12">
        <div class="work-card rounded-3 shadow-sm">
            <div class="work-thumb">
                <a data-bs-toggle="collapse" href="#collapse-${rjid}" role="button">
                    <img src="${imgUrl}" 
                        class="rounded-3 shadow-sm" alt="${workName}"
                        onerror="this.src='https://www.dlsite.com/images/web/home/no_img_main.gif'; this.classList.add('alternative-image');">
                        </a>
                <div class="work-badge-container px-2">
                    <span class="badge rounded-pill shadow-sm text-dark-emphasis bg-primary-subtle border border-primary-subtle">${similarity}%</span>
                    <span class="badge rounded-pill shadow-sm text-${category_color}-emphasis bg-${category_color}-subtle border border-${category_color}-subtle">${category}</span>
                    ${additionTypeTag}
                </div>
                <div class="work-info-container rounded-bottom-3 p-2">
                    <div class="work-info-title px-1 pb-1"><b>${workName}</b></div>
                    <div class="row justify-content-start">
                        <div class="col-8">
                            <a href="${workUrl}" target="_blank"
                                class="badge work-info-badge rounded-pill shadow-sm border border-light-subtle">
                                <i class="fa-solid fa-star"></i> ${rating} (${ratingCount})
                                <span class="vr mx-2"></span>
                                <i class="fa-solid fa-download"></i> ${dlCount}
                            </a>
                        </div>
                        <div class="col-4 text-end">
                            <a href="${commentUrl}" target="_blank"
                                class="badge work-info-badge rounded-pill shadow-sm border border-light-subtle">
                                <i class="fa-solid fa-comment"></i> ${commentCount}
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            <div class="collapse" id="collapse-${rjid}">
                <div class="px-3 pt-2 pb-3 work-card-content">
                    <div><b>${artist}</b> - ${date}</div>
                    <small>${desciption}</small>
                    <div class="mt-1">
                        ${Tags}
                        <span class="badge rounded-pill shadow-sm text-dark-emphasis bg-primary-subtle border border-primary-subtle"></span>
                    </div>
                </div>
            </div>
        </div>
    </div>
  `;
    return cardTemplate;
}

// Card for local catalogue search results. Built from DOM nodes so database text is never parsed as HTML.
function catalogCardTemplate(work, find_similar_label) {
    const rjid = work.index;
    const badge = (classes, text) => $("<span>", { "class": `badge rounded-pill shadow-sm ${classes}` }).text(text);
    const icon = name => $("<i>", { "class": `fa-solid ${name}` });

    const work_format = locale_data && locale_data.work_formats[work.type];
    const category = work_format ? work_format.name : work.type;
    const category_color = (work_format && work_format_class[work_format.category_id]) || "light";
    const hidden_options = ["REV", "TRI", "ORW", "RE", "TRS", "workupdate"];
    const option_badges = work.options
        .filter(option => !hidden_options.includes(option))
        .map(option => badge(
            "text-dark-emphasis bg-light-subtle border border-dark-subtle",
            option in localisation_options ? localisation_options[option][lang] : option
        ));
    const genre_badges = work.tags
        .filter(genre => locale_data && genre in locale_data.genres)
        .map(genre => badge("text-dark-emphasis bg-primary-subtle border border-primary-subtle", locale_data.genres[genre].name));

    const site = encodeURIComponent(work.siteId || "maniax");
    const product = encodeURIComponent(rjid);
    const work_url = `https://www.dlsite.com/${site}/work/=/product_id/${product}.html`;
    const review_url = `https://www.dlsite.com/${site}/work/reviewlist/=/product_id/${product}.html`;
    const collapse_id = `catalog-collapse-${rjid}`;

    const image = $("<img>", { "class": "rounded-3 shadow-sm", "src": getImgUrl(rjid), "alt": work.name || rjid, "loading": "lazy" })
        .one("error", function () {
            this.src = "https://www.dlsite.com/images/web/home/no_img_main.gif";
            this.classList.add("alternative-image");
        });

    const info = $("<div>", { "class": "work-info-container rounded-bottom-3 p-2" }).append(
        $("<div>", { "class": "work-info-title px-1 pb-1" }).append($("<b>").text(work.name || rjid)),
        $("<div>", { "class": "row justify-content-start" }).append(
            $("<div>", { "class": "col-8" }).append(
                $("<a>", { "href": work_url, "target": "_blank", "rel": "noopener noreferrer", "class": "badge work-info-badge rounded-pill shadow-sm border border-light-subtle" }).append(
                    icon("fa-star"), ` ${(work.rate || 0) / 10} (${work.rateCount || 0})`,
                    $("<span>", { "class": "vr mx-2" }),
                    icon("fa-download"), ` ${work.dlCount || 0}`
                )
            ),
            $("<div>", { "class": "col-4 text-end" }).append(
                $("<a>", { "href": work.reviewCount ? review_url : work_url, "target": "_blank", "rel": "noopener noreferrer", "class": "badge work-info-badge rounded-pill shadow-sm border border-light-subtle" }).append(
                    icon("fa-comment"), ` ${work.reviewCount || 0}`
                )
            )
        )
    );

    const thumb = $("<div>", { "class": "work-thumb" }).append(
        $("<a>", { "data-bs-toggle": "collapse", "href": `#${collapse_id}`, "role": "button" }).append(image),
        $("<div>", { "class": "work-badge-container px-2" }).append(
            badge(`text-${category_color}-emphasis bg-${category_color}-subtle border border-${category_color}-subtle`, category),
            " ", option_badges.flatMap(b => [b, " "])
        ),
        info
    );

    const find_similar = rjid_regex.test(rjid)
        ? $("<button>", { "type": "button", "class": "btn btn-sm btn-outline-primary rounded-pill catalog-find-similar", "data-rjid": rjid })
            .append(icon("fa-wand-magic-sparkles"), " ", $("<span>").text(find_similar_label))
        : null;

    const details = $("<div>", { "class": "collapse", "id": collapse_id }).append(
        $("<div>", { "class": "px-3 pt-2 pb-3 work-card-content" }).append(
            $("<div>").append($("<b>").text(work.maker || ""), document.createTextNode(` - ${work.registDate || ""} - ${rjid}`)),
            $("<small>", { "class": "catalog-description" }).text(work.description || ""),
            $("<div>", { "class": "mt-1" }).append(genre_badges.flatMap(b => [b, " "]))
        )
    );

    return $("<div>", { "class": "col-xxl-3 col-xl-4 col-sm-6 col-12" }).append(
        $("<div>", { "class": "work-card catalog-card rounded-3 shadow-sm" }).append(
            thumb,
            $("<div>", { "class": "px-3 pt-2 pb-2 d-flex justify-content-between align-items-center gap-2" }).append(
                $("<small>", { "class": "text-truncate text-body-secondary" }).text(work.maker || ""),
                find_similar
            ),
            details
        )
    );
}