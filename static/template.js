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