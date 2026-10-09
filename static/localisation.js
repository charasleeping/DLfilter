const supported_lang = ["en_US", "ja_JP", "zh_CN", "zh_TW"];
// the order the language button cycles through
const language_cycle = ["en_US", "ja_JP", "zh_TW", "zh_CN"];
const language_names = {
    en_US: "English",
    ja_JP: "日本語",
    zh_TW: "繁體中文",
    zh_CN: "简体中文"
};
// one glyph per language, shown on the button that switches to it
const language_glyphs = {
    en_US: "A",
    ja_JP: "あ",
    zh_TW: "繁",
    zh_CN: "简"
};
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
        zh_CN: "分类",
        zh_TW: "分類"
    },
    workformat: {
        en_US: "product format",
        en_US_capital: "Product format",
        en_US_plural: "product formats",
        en_US_plural_capital: "Product formats",
        ja_JP: "作品形式",
        zh_CN: "作品形式",
        zh_TW: "作品形式"
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
        en_US: localisation_words.workformat.en_US_plural_capital,
        ja_JP: localisation_words.workformat.ja_JP,
        zh_CN: localisation_words.workformat.zh_CN,
        zh_TW: localisation_words.workformat.zh_TW
    },
    workformat_modal_title: {
        en_US: `Select ${localisation_words.workformat.en_US_plural}`,
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
        en_US: `Select at least one ${localisation_words.workformat.en_US}.`,
        ja_JP: "作品形式を1つ以上選択してください。",
        zh_CN: `请至少选择一种${localisation_words.workformat.zh_CN}。`,
        zh_TW: `請至少選擇一種${localisation_words.workformat.zh_TW}。`
    },
    show_advanced_options: {
        en_US: "Show advanced options",
        ja_JP: "詳細オプションを表示",
        zh_CN: "显示高级选项",
        zh_TW: "顯示進階選項"
    },
    date_title: {
        en_US: "Release date",
        ja_JP: "販売開始日",
        zh_CN: "发售日期",
        zh_TW: "發售開始日"
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
    popularity_weight_title: {
        en_US: "Popularity weight",
        ja_JP: "人気度の重み",
        zh_CN: "热门度权重",
        zh_TW: "熱門度權重"
    },
    popularity_weight_label_1: {
        en_US: "Less popular",
        ja_JP: "人気が低い",
        zh_CN: "较冷门",
        zh_TW: "較冷門"
    },
    popularity_weight_label_2: {
        en_US: "Popular",
        ja_JP: "人気が高い",
        zh_CN: "较热门",
        zh_TW: "較熱門"
    },
    age_title: {
        en_US: "Age",
        ja_JP: "年齢指定",
        zh_CN: "年龄指定",
        zh_TW: "年齡指定"
    },
    age_checkbox_1: {
        en_US: "All Ages",
        ja_JP: "全年齢向け",
        zh_CN: "全年龄",
        zh_TW: "全年齡向"
    },
    age_checkbox_2: {
        en_US: "R15",
        ja_JP: "R15",
        zh_CN: "R15",
        zh_TW: "R15限定"
    },
    age_checkbox_3: {
        en_US: "R18",
        ja_JP: "R18",
        zh_CN: "R18",
        zh_TW: "R18"
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
        ja_JP: "AI一部利用",
        zh_CN: "部分使用AI",
        zh_TW: "部分AI使用"
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
        en_US: "RJ number of your favourite work",
        ja_JP: "好きな作品のRJ番号",
        zh_CN: "您喜欢的作品的 RJ 号",
        zh_TW: "您喜歡的作品的 RJ 號"
    },
    rjid_title: {
        en_US: "Copy tags from",
        ja_JP: "タグのコピー元",
        zh_CN: "复制标签自",
        zh_TW: "複製標籤自"
    },
    work_input_hint_format: {
        en_US: "Invalid RJ ID (e.g. RJ123456 or RJ01234567)",
        ja_JP: "無効な RJ 番号（例：RJ123456 または RJ01234567）",
        zh_CN: "无效的 RJ 号（例如 RJ123456 或 RJ01234567）",
        zh_TW: "無效的 RJ 號（例如 RJ123456 或 RJ01234567）"
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
        en_US: `Start with some <span id="welcome-start-hint-keywords">keywords</span>, <span id="welcome-start-hint-genres">${localisation_words.genre.en_US_plural}</span>, or the <span id="welcome-start-hint-workid">RJ ID</span>.`,
        ja_JP: `<span id="welcome-start-hint-keywords">キーワード</span>、<span id="welcome-start-hint-genres">${localisation_words.genre.ja_JP}</span>、または<span id="welcome-start-hint-workid">RJ 番号</span>から始めましょう。`,
        zh_CN: `从<span id="welcome-start-hint-keywords">关键词</span>、<span id="welcome-start-hint-genres">${localisation_words.genre.zh_CN}</span>或<span id="welcome-start-hint-workid">RJ 号</span>开始。`,
        zh_TW: `從<span id="welcome-start-hint-keywords">關鍵字</span>、<span id="welcome-start-hint-genres">${localisation_words.genre.zh_TW}</span>或<span id="welcome-start-hint-workid">RJ 號</span>開始。`
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
    work_not_in_local_db: {
        en_US: "This RJ ID is not in the local catalog. The database may be out of date, the record may be missing, or the work may belong to another DLsite category.",
        ja_JP: "この RJ 番号はローカルデータベースにありません。データベースが古い、記録が欠けている、または DLsite の別カテゴリの作品である可能性があります。",
        zh_CN: "本地数据库中没有此 RJ 号。可能是数据库未更新、记录缺失，或该作品属于 DLsite 的其他分类。",
        zh_TW: "本機資料庫中沒有此 RJ 號。可能是資料庫未更新、紀錄缺失，或該作品屬於 DLsite 的其他分類。"
    },
    catalog_title: {
        en_US: "Search by",
        ja_JP: "検索方法",
        zh_CN: "搜索方式",
        zh_TW: "搜尋方式"
    },
    catalog_age_any: {
        en_US: "Any",
        ja_JP: "指定なし",
        zh_CN: "不限",
        zh_TW: "不限"
    },
    language_button: {
        en_US: "Language",
        ja_JP: "言語",
        zh_CN: "语言",
        zh_TW: "語言"
    },
    theme_to_dark: {
        en_US: "Switch to dark theme",
        ja_JP: "ダークテーマに切り替え",
        zh_CN: "切换到深色主题",
        zh_TW: "切換到深色主題"
    },
    theme_to_light: {
        en_US: "Switch to light theme",
        ja_JP: "ライトテーマに切り替え",
        zh_CN: "切换到浅色主题",
        zh_TW: "切換到淺色主題"
    },
    catalog_placeholder: {
        en_US: "Title, circle or RJ ID",
        ja_JP: "作品名・サークル名・RJ 番号",
        zh_CN: "作品名、社团名或 RJ 号",
        zh_TW: "作品名、社團名或 RJ 號"
    },
    catalog_field_label: {
        en_US: "Search in",
        ja_JP: "検索対象",
        zh_CN: "搜索范围",
        zh_TW: "搜尋範圍"
    },
    catalog_field_all: {
        en_US: "All",
        ja_JP: "すべて",
        zh_CN: "全部",
        zh_TW: "全部"
    },
    catalog_field_title: {
        en_US: "Title",
        ja_JP: "作品名",
        zh_CN: "作品名",
        zh_TW: "作品名"
    },
    catalog_field_artist: {
        en_US: "Circle",
        ja_JP: "サークル",
        zh_CN: "社团",
        zh_TW: "社團"
    },
    catalog_field_id: {
        en_US: "RJ ID",
        ja_JP: "RJ 番号",
        zh_CN: "RJ 号",
        zh_TW: "RJ 號"
    },
    catalog_hint: {
        en_US: "Searches the local database.<br>Width and letter case are ignored.",
        ja_JP: "ローカルデータベースを検索します。<br>全角・半角、大文字・小文字は区別しません。",
        zh_CN: "搜索本地数据库，<br>不区分全角半角与大小写。",
        zh_TW: "搜尋本機資料庫，<br>不區分全形半形與大小寫。"
    },
    catalog_results_title: {
        en_US: "Works found",
        ja_JP: "作品検索結果",
        zh_CN: "作品搜索结果",
        zh_TW: "作品搜尋結果"
    },
    catalog_searching: {
        en_US: "Searching…",
        ja_JP: "検索中…",
        zh_CN: "搜索中…",
        zh_TW: "搜尋中…"
    },
    catalog_summary: {
        en_US: "{total} works <span class=\"vr mx-2\"></span> Showing {start} - {end}",
        ja_JP: "{total} 件の作品 <span class=\"vr mx-2\"></span> {start} - {end} 件目を表示中",
        zh_CN: "共 {total} 件作品 <span class=\"vr mx-2\"></span> 显示第 {start} - {end} 件",
        zh_TW: "共 {total} 件作品 <span class=\"vr mx-2\"></span> 顯示第 {start} - {end} 件"
    },
    catalog_no_results: {
        en_US: "No works in the local database match this search.",
        ja_JP: "ローカルデータベースに一致する作品はありません。",
        zh_CN: "本地数据库中没有符合的作品。",
        zh_TW: "本機資料庫中沒有符合的作品。"
    },
    catalog_error: {
        en_US: "The search failed. Please try again.",
        ja_JP: "検索に失敗しました。もう一度お試しください。",
        zh_CN: "搜索失败，请重试。",
        zh_TW: "搜尋失敗，請再試一次。"
    },
    catalog_find_similar: {
        en_US: "Find similar",
        ja_JP: "似た作品を探す",
        zh_CN: "查找相似作品",
        zh_TW: "尋找相似作品"
    },
    catalog_previous_page: {
        en_US: "Previous page",
        ja_JP: "前のページ",
        zh_CN: "上一页",
        zh_TW: "上一頁"
    },
    catalog_next_page: {
        en_US: "Next page",
        ja_JP: "次のページ",
        zh_CN: "下一页",
        zh_TW: "下一頁"
    },
    search_tab_keywords: {
        en_US: "Find works",
        ja_JP: "作品を探す",
        zh_CN: "查找作品",
        zh_TW: "尋找作品"
    },
    reset_search: {
        en_US: "Reset search",
        ja_JP: "検索をリセット",
        zh_CN: "重置搜索",
        zh_TW: "重設搜尋"
    },
    random_works: {
        en_US: "Random works",
        ja_JP: "ランダムな作品",
        zh_CN: "随机作品",
        zh_TW: "隨機作品"
    },
    reset_label: {
        en_US: "Reset",
        ja_JP: "リセット",
        zh_CN: "重置",
        zh_TW: "重設"
    },
    random_label: {
        en_US: "Random",
        ja_JP: "ランダム",
        zh_CN: "随机",
        zh_TW: "隨機"
    },
    random_results_title: {
        en_US: "Random picks",
        ja_JP: "ランダムピックアップ",
        zh_CN: "随机推荐",
        zh_TW: "隨機推薦"
    },
    random_summary: {
        en_US: "{count} random works from the local database",
        ja_JP: "ローカルデータベースからランダムに選んだ {count} 件の作品",
        zh_CN: "从本地数据库随机选出 {count} 件作品",
        zh_TW: "從本機資料庫隨機選出 {count} 件作品"
    },
    preset_save: {
        en_US: "Save preset",
        ja_JP: "プリセットを保存",
        zh_CN: "保存预设",
        zh_TW: "儲存預設"
    },
    preset_load: {
        en_US: "Load preset",
        ja_JP: "プリセットを読み込む",
        zh_CN: "载入预设",
        zh_TW: "載入預設"
    },
    preset_name: {
        en_US: "Preset name",
        ja_JP: "プリセット名",
        zh_CN: "预设名称",
        zh_TW: "預設名稱"
    },
    preset_save_hint: {
        en_US: `Saves the RJ ID, ${localisation_words.genre.en_US_plural}, ${localisation_words.workformat.en_US_plural} and advanced options to the presets folder. A preset with the same name is replaced.`,
        ja_JP: `RJ 番号・${localisation_words.genre.ja_JP}・${localisation_words.workformat.ja_JP}・詳細オプションを presets フォルダに保存します。同じ名前のプリセットは上書きされます。`,
        zh_CN: `将 RJ 号、${localisation_words.genre.zh_CN}、${localisation_words.workformat.zh_CN}和高级选项保存到 presets 文件夹。同名预设会被覆盖。`,
        zh_TW: `將 RJ 號、${localisation_words.genre.zh_TW}、${localisation_words.workformat.zh_TW}和進階選項儲存到 presets 資料夾。同名預設會被覆寫。`
    },
    preset_save_button: {
        en_US: "Save",
        ja_JP: "保存",
        zh_CN: "保存",
        zh_TW: "儲存"
    },
    preset_name_invalid: {
        en_US: "Use up to 60 letters, digits, spaces, - or _.",
        ja_JP: "60 文字以内の文字・数字・スペース・-・_ を使用してください。",
        zh_CN: "请使用最多 60 个字母、数字、空格、- 或 _。",
        zh_TW: "請使用最多 60 個字母、數字、空格、- 或 _。"
    },
    preset_too_many: {
        en_US: "The presets folder is full. Delete some presets first.",
        ja_JP: "presets フォルダがいっぱいです。先にプリセットを削除してください。",
        zh_CN: "presets 文件夹已满，请先删除一些预设。",
        zh_TW: "presets 資料夾已滿，請先刪除一些預設。"
    },
    preset_save_failed: {
        en_US: "The preset could not be saved.",
        ja_JP: "プリセットを保存できませんでした。",
        zh_CN: "无法保存预设。",
        zh_TW: "無法儲存預設。"
    },
    preset_none: {
        en_US: "No presets saved yet.",
        ja_JP: "保存されたプリセットはまだありません。",
        zh_CN: "还没有保存的预设。",
        zh_TW: "還沒有儲存的預設。"
    },
    preset_load_failed: {
        en_US: "The preset could not be loaded.",
        ja_JP: "プリセットを読み込めませんでした。",
        zh_CN: "无法载入预设。",
        zh_TW: "無法載入預設。"
    },
    preset_open_file: {
        en_US: "Open another file…",
        ja_JP: "別のファイルを開く…",
        zh_CN: "打开其他文件…",
        zh_TW: "開啟其他檔案…"
    },
    cancel: {
        en_US: "Cancel",
        ja_JP: "キャンセル",
        zh_CN: "取消",
        zh_TW: "取消"
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