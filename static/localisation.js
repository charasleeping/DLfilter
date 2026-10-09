const supported_lang = ["en_US", "ja_JP", "zh_CN", "zh_TW"];
const localisation_words = {
    search: {
        en_US: "Search",
        ja_JP: "検索",
        zh_CN: "搜索",
        zh_TW: "搜尋"
    },
    genre: {
        en_US: "genre",
        en_US_capital: "Genre",
        en_US_plural: "genres",
        en_US_plural_capital: "Genres",
        ja_JP: "ジャンル",
        zh_CN: "属性",
        zh_TW: "屬性"
    },
    workformat: {
        en_US: "work format",
        en_US_capital: "Work format",
        ja_JP: "作品形式",
        zh_CN: "作品类型",
        zh_TW: "作品類型"
    },
    zero: {
        en_US: "zero",
        ja_JP: "ゼロ",
        zh_CN: "零",
        zh_TW: "零"
    },
    years: {
        en_US: " years",
        ja_JP: "年",
        zh_CN: "年",
        zh_TW: "年"
    },
    months: {
        en_US: " months",
        ja_JP: "ヶ月",
        zh_CN: "个月",
        zh_TW: "個月"
    },
    and_date: {
        en_US: " and ",
        ja_JP: "",
        zh_CN: "",
        zh_TW: ""
    },
    less_than_month: {
        en_US: "less than a month",
        ja_JP: "1ヶ月未満",
        zh_CN: "少于一个月",
        zh_TW: "少於一個月"
    },

}

const localisation = {
    not_selected: {
        en_US: "Not selected.",
        ja_JP: "選択されていません。",
        zh_CN: "尚未选择。",
        zh_TW: "尚未選擇。"
    },
    genre_title: {
        en_US: localisation_words.genre.en_US_plural_capital,
        ja_JP: localisation_words.genre.ja_JP,
        zh_CN: localisation_words.genre.zh_CN,
        zh_TW: localisation_words.genre.zh_TW
    },
    workformat_title: {
        en_US: localisation_words.workformat.en_US_capital,
        ja_JP: localisation_words.workformat.ja_JP,
        zh_CN: localisation_words.workformat.zh_CN,
        zh_TW: localisation_words.workformat.zh_TW
    },
    workformat_modal_title: {
        en_US: `Select ${localisation_words.workformat.en_US}`,
        ja_JP: `${localisation_words.workformat.ja_JP}を選択`,
        zh_CN: `选择${localisation_words.workformat.zh_CN}`,
        zh_TW: `選擇${localisation_words.workformat.zh_TW}`
    },
    included_genres_title: {
        en_US: `Included ${localisation_words.genre.en_US_plural}`,
        ja_JP: `含まれる${localisation_words.genre.ja_JP}`,
        zh_CN: `包含的${localisation_words.genre.zh_CN}`,
        zh_TW: `包含的${localisation_words.genre.zh_TW}`
    },
    excluded_genres_title: {
        en_US: `Excluded ${localisation_words.genre.en_US_plural}`,
        ja_JP: `除外された${localisation_words.genre.ja_JP}`,
        zh_CN: `排除的${localisation_words.genre.zh_CN}`,
        zh_TW: `排除的${localisation_words.genre.zh_TW}`
    },
    search_genres_modal_title: {
        en_US: `Select ${localisation_words.genre.en_US_plural}`,
        ja_JP: `${localisation_words.genre.ja_JP}を選択`,
        zh_CN: `选择${localisation_words.genre.zh_CN}`,
        zh_TW: `選擇${localisation_words.genre.zh_TW}`
    },
    included_genres_modal_title: {
        en_US: `Select included ${localisation_words.genre.en_US_plural}`,
        ja_JP: `含めたい${localisation_words.genre.ja_JP}を選択`,
        zh_CN: `选择想包含的${localisation_words.genre.zh_CN}`,
        zh_TW: `選擇想包含的${localisation_words.genre.zh_TW}`
    },
    excluded_genres_modal_title: {
        en_US: `Select excluded ${localisation_words.genre.en_US_plural}`,
        ja_JP: `除外したい${localisation_words.genre.ja_JP}を選択`,
        zh_CN: `选择想排除的${localisation_words.genre.zh_CN}`,
        zh_TW: `選擇想排除的${localisation_words.genre.zh_TW}`
    },
    selected_search_genres_desp: {
        en_US: `Only the first 10 ${localisation_words.genre.en_US_plural} will be searched. ${localisation_words.genre.en_US_plural_capital} that have been added for <b>searching</b>:`,
        ja_JP: `最初の10個の${localisation_words.genre.ja_JP}のみ検索されます。<b>検索</b> に追加された${localisation_words.genre.ja_JP}：`,
        zh_CN: `只有前10个${localisation_words.genre.zh_CN}会被搜索。已添加到 <b>搜索</b> 的${localisation_words.genre.zh_CN}：`,
        zh_TW: `只有前10個${localisation_words.genre.zh_TW}會被搜尋。已添加到 <b>搜尋</b> 的${localisation_words.genre.zh_TW}：`
    },
    selected_included_genres_desp: {
        en_US: `Only the first 5 ${localisation_words.genre.en_US_plural} will be filtered. ${localisation_words.genre.en_US_plural_capital} that have been <b>included</b>:`,
        ja_JP: `最初の5つの${localisation_words.genre.ja_JP}のみフィルタリングされます。<b>含まれる</b> ${localisation_words.genre.ja_JP}：`,
        zh_CN: `只有前5个${localisation_words.genre.zh_CN}会被筛选。已 <b>包含</b> 的${localisation_words.genre.zh_CN}：`,
        zh_TW: `只有前5個${localisation_words.genre.zh_TW}會被篩選。已 <b>包含</b> 的${localisation_words.genre.zh_TW}：`
    },
    selected_excluded_genres_desp: {
        en_US: `Only the first 5 ${localisation_words.genre.en_US_plural} will be filtered. ${localisation_words.genre.en_US_plural_capital} that have been <b>excluded</b>:`,
        ja_JP: `最初の5つの${localisation_words.genre.ja_JP}のみフィルタリングされます。<b>除外された</b> ${localisation_words.genre.ja_JP}：`,
        zh_CN: `只有前5个${localisation_words.genre.zh_CN}会被筛选。已 <b>排除</b> 的${localisation_words.genre.zh_CN}：`,
        zh_TW: `只有前5個${localisation_words.genre.zh_TW}會被篩選。已 <b>排除</b> 的${localisation_words.genre.zh_TW}：`
    },
    genre_search_placeholder: {
        en_US: `What ${localisation_words.genre.en_US_plural} are you looking for?`,
        ja_JP: `お探しの${localisation_words.genre.ja_JP}はなんですか？`,
        zh_CN: `您在寻找什么${localisation_words.genre.zh_CN}呢？`,
        zh_TW: `您在尋找什麼${localisation_words.genre.zh_TW}呢？`
    },
    at_least_one_genre: {
        en_US: `Select at least one ${localisation_words.genre.en_US}.`,
        ja_JP: `${localisation_words.genre.ja_JP}を1つ以上選択してください。`,
        zh_CN: `请至少选择一种${localisation_words.genre.zh_CN}。`,
        zh_TW: `請至少選擇一種${localisation_words.genre.zh_TW}。`
    },
    at_least_one_workformat: {
        en_US: "Select at least one work format.",
        ja_JP: "作品形式を1つ以上選択してください。",
        zh_CN: "请至少选择一种作品类型。",
        zh_TW: "請至少選擇一種作品類型。"
    },
    show_advanced_options: {
        en_US: "Show advanced options",
        ja_JP: "詳細オプションを表示",
        zh_CN: "显示高级选项",
        zh_TW: "顯示進階選項"
    },
    date_title: {
        en_US: "Release date",
        ja_JP: "発売日",
        zh_CN: "发售日",
        zh_TW: "發售日"
    },
    date_label: {
        en_US: `After <span id="date-range-time">-</span> (<span id="date-range-ago">-</span> ago)`,
        ja_JP: `<span id="date-range-time">-</span>以降（<span id="date-range-ago">-</span>前）`,
        zh_CN: `在 <span id="date-range-time">-</span> 之后（<span id="date-range-ago">-</span>前）`,
        zh_TW: `在 <span id="date-range-time">-</span> 之後（<span id="date-range-ago">-</span>前）`
    },
    dlcount_title: {
        en_US: "Download count",
        ja_JP: "ダウンロード数",
        zh_CN: "下载数",
        zh_TW: "下載數"
    },
    dlcount_label_0: {
        en_US: "*Changing the value may lower the accuracy of the result.",
        ja_JP: "※変更すると結果が精度が低くなる可能性があります。",
        zh_CN: "※更改该值可能会降低搜索的精确度。",
        zh_TW: "※更改該值可能會降低搜尋的精確度。"
    },
    dlcount_label_1: {
        en_US: "Lower",
        ja_JP: "低い",
        zh_CN: "较低",
        zh_TW: "較低"
    },
    dlcount_label_2: {
        en_US: "Higher",
        ja_JP: "高い",
        zh_CN: "较高",
        zh_TW: "較高"
    },
    genre_weight_title: {
        en_US: `${localisation_words.genre.en_US_capital} weight`,
        ja_JP: `${localisation_words.genre.ja_JP}の重み`,
        zh_CN: `${localisation_words.genre.zh_CN}权重`,
        zh_TW: `${localisation_words.genre.zh_TW}權重`
    },
    genre_weight_option_1: {
        en_US: "No weight",
        ja_JP: "なし",
        zh_CN: "无权重",
        zh_TW: "無權重"
    },
    genre_weight_option_2: {
        en_US: `Lower popular ${localisation_words.genre.en_US_plural}`,
        ja_JP: `人気${localisation_words.genre.ja_JP}の重みを下げる`,
        zh_CN: `降低热门${localisation_words.genre.zh_CN}的权重`,
        zh_TW: `降低熱門${localisation_words.genre.zh_TW}的權重`
    },
    genre_weight_option_3: {
        en_US: `Lower unpopular ${localisation_words.genre.en_US_plural}`,
        ja_JP: `人気のない${localisation_words.genre.ja_JP}の重みを下げる`,
        zh_CN: `降低冷门${localisation_words.genre.zh_CN}的权重`,
        zh_TW: `降低冷門${localisation_words.genre.zh_TW}的權重`
    },
    genre_weight_option_4: {
        en_US: `Lower popular and unpopular ${localisation_words.genre.en_US_plural}`,
        ja_JP: `人気と人気のない${localisation_words.genre.ja_JP}の重みを下げる`,
        zh_CN: `降低热门和冷门${localisation_words.genre.zh_CN}的权重`,
        zh_TW: `降低熱門和冷門${localisation_words.genre.zh_TW}的權重`
    },
    age_title: {
        en_US: "Age",
        ja_JP: "年齢指定",
        zh_CN: "年龄指定",
        zh_TW: "年齡指定"
    },
    age_checkbox_1: {
        en_US: "All ages",
        ja_JP: "全年齢向け",
        zh_CN: "全年龄向",
        zh_TW: "全年齡向"
    },
    age_checkbox_2: {
        en_US: "R-rated",
        ja_JP: "R指定",
        zh_CN: "R指定・成人指定",
        zh_TW: "R指定・成人指定"
    },
    age_checkbox_3: {
        en_US: "Adult",
        ja_JP: "成人向け",
        zh_CN: "成人向",
        zh_TW: "成人向"
    },
    misc_title: {
        en_US: "Excluded contents",
        ja_JP: "除外する内容",
        zh_CN: "排除的内容",
        zh_TW: "排除的內容"
    },
    misc_checkbox_1: {
        en_US: "Low or no-rated works",
        ja_JP: "低評価・無評価の作品",
        zh_CN: "低评价・无评价的作品",
        zh_TW: "低評價・無評價的作品"
    },
    misc_checkbox_2: {
        en_US: "AI-generated works",
        ja_JP: "AI生成作品",
        zh_CN: "AI生成作品",
        zh_TW: "AI生成作品"
    },
    misc_checkbox_3: {
        en_US: "Partially AI-generated works",
        ja_JP: "AI一部利用作品",
        zh_CN: "部分使用AI生成的作品",
        zh_TW: "部分使用AI生成的作品"
    },
    misc_checkbox_4: {
        en_US: "Guro works",
        ja_JP: "グロ作品",
        zh_CN: "猎奇作品",
        zh_TW: "獵奇作品"
    },
    misc_checkbox_5: {
        en_US: "Gay works",
        ja_JP: "ゲイ作品",
        zh_CN: "男同作品",
        zh_TW: "男同作品"
    },
    work_not_found: {
        en_US: "Cannot find the work.",
        ja_JP: "作品が見つかりません。",
        zh_CN: "找不到作品。",
        zh_TW: "找不到作品。"
    },
    error_occurred: {
        en_US: "An error occurred.",
        ja_JP: "エラーが発生しました。",
        zh_CN: "发生了错误。",
        zh_TW: "發生了錯誤。"
    },
    work_input: {
        en_US: "What is the RJ number of your favourite work?",
        ja_JP: "好きな作品のRJ番号はなんですか？",
        zh_CN: "您喜欢的作品的 RJ 号是？",
        zh_TW: "您喜歡的作品的 RJ 號是？"
    },
    work_input_hint: {
        en_US: `Add ${localisation_words.genre.en_US} by work ID`,
        ja_JP: `作品 ID で${localisation_words.genre.ja_JP}を追加`,
        zh_CN: `通过作品 ID 添加${localisation_words.genre.zh_CN}`,
        zh_TW: `透過作品 ID 新增${localisation_words.genre.zh_TW}`
    },
    work_input_hint_format: {
        en_US: "Invalid work ID (e.g. RJ123456 or RJ01234567)",
        ja_JP: "無効な作品 ID（例：RJ123456 または RJ01234567）",
        zh_CN: "无效的作品 ID（例如 RJ123456 或 RJ01234567）",
        zh_TW: "無效的作品 ID（例如 RJ123456 或 RJ01234567）"
    },
    welcome_title: {
        en_US: "Welcome to DLfilter.",
        ja_JP: "DLfilter へようこそ。",
        zh_CN: "欢迎来到 DLfilter。",
        zh_TW: "歡迎來到 DLfilter。"
    },
    welcome_subtitle: {
        en_US: "Discover your perfect match on DLsite - Semantic search powered by AI",
        ja_JP: "DLsite で理想の作品を探しましょう・AIによるセマンティック検索",
        zh_CN: "AI 驱动的语义搜索・在 DLsite 寻找您理想中的作品",
        zh_TW: "AI 驅動的語義搜尋・在 DLsite 尋找您理想中的作品"
    },
    welcome_start_hint: {
        en_US: `Start by adding <span id="welcome-start-hint-genres">${localisation_words.genre.en_US_plural}</span> or typing the <span id="welcome-start-hint-workid">work ID<span> in the search panel.`,
        ja_JP: `検索パネルに <span id="welcome-start-hint-genres">${localisation_words.genre.ja_JP}</span> を追加するか、<span id="welcome-start-hint-workid">作品 ID</span> を入力して始めましょう。`,
        zh_CN: `在搜索面板中添加 <span id="welcome-start-hint-genres">${localisation_words.genre.zh_CN}</span> 或输入 <span id="welcome-start-hint-workid">作品 ID</span> 以开始。`,
        zh_TW: `在搜尋面板中新增 <span id="welcome-start-hint-genres">${localisation_words.genre.zh_TW}</span> 或輸入 <span id="welcome-start-hint-workid">作品 ID</span> 以開始。`
    },
    welcome_info: {
        en_US: `Collection of <span id="banner-text">-</span> works since the millennium <span class="vr mx-2"></span> Last updated on <span id="navbar-time">-</span>`,
        ja_JP: `ミレニアム以降の <span id="banner-text">-</span> 作品を収録 <span class="vr mx-2"></span> 最終更新：<span id="navbar-time">-</span>`,
        zh_CN: `收录了千禧年以来的 <span id="banner-text">-</span> 件作品 <span class="vr mx-2"></span> 最后更新：<span id="navbar-time">-</span>`,
        zh_TW: `收錄了千禧年以來的 <span id="banner-text">-</span> 件作品 <span class="vr mx-2"></span> 最後更新：<span id="navbar-time">-</span>`
    },
    search_info: {
        en_US: `<span id="search-info-count">-</span> works (<span id="search-info-time">-</span> seconds) <span class="vr mx-2"></span> Showing <span id="search-info-start"></span> - <span id="search-info-end"></span> results:`,
        ja_JP: `<span id="search-info-count">-</span> 件の作品（<span id="search-info-time">-</span> 秒）<span class="vr mx-2"></span> <span id="search-info-start"></span> - <span id="search-info-end"></span> 件目を表示中：`,
        zh_CN: `找到 <span id="search-info-count">-</span> 件作品（搜索耗时 <span id="search-info-time">-</span> 秒）<span class="vr mx-2"></span> 显示 <span id="search-info-start"></span> - <span id="search-info-end"></span> 件结果：`,
        zh_TW: `找到 <span id="search-info-count">-</span> 件作品（搜尋花費 <span id="search-info-time">-</span> 秒）<span class="vr mx-2"></span> 顯示 <span id="search-info-start"></span> - <span id="search-info-end"></span> 件結果：`
    },
    end_of_result: {
        en_US: "All the most relevant results are here.",
        ja_JP: "関連性の高い結果はすべて表示された。",
        zh_CN: "最相关的结果都在这里了。",
        zh_TW: "最相關的結果都在這裡了。"
    },
    end_of_result_2: {
        en_US: "All results are shown. Try to refine your search for more results.",
        ja_JP: "すべての結果が表示された。検索条件を変更してみてください。",
        zh_CN: "已显示所有结果。尝试更改搜索条件以获得更多。",
        zh_TW: "已顯示所有結果。嘗試更改搜尋條件以獲得更多。"
    },

}

const localisation_options = {
    // unknown options: ORW, RE, TRS, workupdate
    // language
    JPN: {
        en_US: "🇯🇵",
        ja_JP: "🇯🇵",
        zh_CN: "🇯🇵",
        zh_TW: "🇯🇵"
    },
    ENG: {
        en_US: "🇺🇸",
        ja_JP: "🇺🇸",
        zh_CN: "🇺🇸",
        zh_TW: "🇺🇸"
    },
    CHI: {
        en_US: "🇨🇳",
        ja_JP: "🇨🇳",
        zh_CN: "🇨🇳",
        zh_TW: "🇨🇳"
    },
    CHI_HANS: {
        en_US: "🇨🇳",
        ja_JP: "🇨🇳",
        zh_CN: "🇨🇳",
        zh_TW: "🇨🇳"
    },
    CHI_HANT: {
        en_US: "🇹🇼",
        ja_JP: "🇹🇼",
        zh_CN: "🇭🇰",
        zh_TW: "🇹🇼"
    },
    KO_KR: {
        en_US: "🇰🇷",
        ja_JP: "🇰🇷",
        zh_CN: "🇰🇷",
        zh_TW: "🇰🇷"
    },
    FRA: {
        en_US: "🇫🇷",
        ja_JP: "🇫🇷",
        zh_CN: "🇫🇷",
        zh_TW: "🇫🇷"
    },
    ITA: {
        en_US: "🇮🇹",
        ja_JP: "🇮🇹",
        zh_CN: "🇮🇹",
        zh_TW: "🇮🇹"
    },
    GER: {
        en_US: "🇩🇪",
        ja_JP: "🇩🇪",
        zh_CN: "🇩🇪",
        zh_TW: "🇩🇪"
    },
    ESP: {
        en_US: "🇪🇸",
        ja_JP: "🇪🇸",
        zh_CN: "🇪🇸",
        zh_TW: "🇪🇸"
    },
    NM: {
        en_US: "🌐",
        ja_JP: "🌐",
        zh_CN: "🌐",
        zh_TW: "🌐"
    },
    DOT: {
        en_US: "DLsite Official Translation",
        ja_JP: "DLsite 公式翻訳",
        zh_CN: "DLsite 官方翻译",
        zh_TW: "DLsite 官方翻譯"
    },
    VET: {
        en_US: "Recommended Translation",
        ja_JP: "おすすめ翻訳",
        zh_CN: "推荐翻译",
        zh_TW: "推薦翻譯"
    },
    IDN: {
        en_US: "Foreign Circle (🇮🇩)",
        ja_JP: "海外サークル（🇮🇩）",
        zh_CN: "海外社团（🇮🇩）",
        zh_TW: "海外社團（🇮🇩）"
    },
    // work type
    SND: {
        en_US: "🔊",
        ja_JP: "🔊",
        zh_CN: "🔊",
        zh_TW: "🔊"
    },
    MS2: {
        en_US: "🎵",
        ja_JP: "🎵",
        zh_CN: "🎵",
        zh_TW: "🎵"
    },
    MV2: {
        en_US: "🎞️",
        ja_JP: "🎞️",
        zh_CN: "🎞️",
        zh_TW: "🎞️"
    },
    WPD: {
        en_US: "PDF",
        ja_JP: "PDF",
        zh_CN: "PDF",
        zh_TW: "PDF"
    },
    WAP: {
        en_US: "APK",
        ja_JP: "APK",
        zh_CN: "APK",
        zh_TW: "APK"
    },
    DLP: {
        en_US: "Browser compatible",
        ja_JP: "ブラウザ対応",
        zh_CN: "浏览器相容",
        zh_TW: "瀏覽器相容"
    },
    VRO: {
        en_US: "VR only",
        ja_JP: "VR専用",
        zh_CN: "VR专用",
        zh_TW: "VR專用"
    },
    VRS: {
        en_US: "VR supported",
        ja_JP: "VR対応",
        zh_CN: "支持VR",
        zh_TW: "對應VR"
    },
    VRI: {
        en_US: "Imagine",
        ja_JP: "Imagine",
        zh_CN: "Imagine",
        zh_TW: "Imagine"
    },
    // content type
    GRO: {
        en_US: "Guro",
        ja_JP: "グロ",
        zh_CN: "猎奇",
        zh_TW: "獵奇"
    },
    MEN: {
        en_US: "Gay",
        ja_JP: "ゲイ",
        zh_CN: "男同",
        zh_TW: "男同"
    },
    AIG: {
        en_US: "AI Generated",
        ja_JP: "AI生成",
        zh_CN: "AI生成",
        zh_TW: "AI生成"
    },
    AIP: {
        en_US: "Partial AI",
        ja_JP: "部分AI",
        zh_CN: "部分AI",
        zh_TW: "部分AI"
    },
    // misc
    OLY: {
        en_US: "DLsite only",
        ja_JP: "DLsite限定",
        zh_CN: "DLsite限定",
        zh_TW: "DLsite限定"
    },
}