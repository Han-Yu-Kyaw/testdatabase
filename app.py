
import json
import re
import unicodedata

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text


# ============================================================
# PAGE CONFIG
# ============================================================

st.title("Dashboard")

st.set_page_config(
    page_title="Alliz Member Needs Dashboard",
    page_icon="📊",
    layout="wide",
)


# ============================================================
# ALLIZ STYLE
# ============================================================

ALLIZ_PINK = "#FF3A8B"
ALLIZ_PLUM = "#431527"
ALLIZ_BLUSH = "#FFC4DC"
ALLIZ_MINT = "#4EBFB4"
ALLIZ_CORAL = "#FF9782"
ALLIZ_BACKGROUND = "#F4F1F2"
ALLIZ_BORDER = "#ECE8EA"

OTHER = "Other or Unclear"


st.markdown(
    f"""
    <style>

    .stApp {{
        background:
            radial-gradient(
                circle at 92% 4%,
                {ALLIZ_BLUSH}55 0,
                transparent 24rem
            ),
            linear-gradient(
                180deg,
                #FFF9FC 0%,
                {ALLIZ_BACKGROUND} 100%
            );
        color: {ALLIZ_PLUM};
    }}

    [data-testid="stHeader"] {{
        background-color: rgba(255, 249, 252, 0.88);
    }}

    .block-container {{
        max-width: 1480px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }}

    h1, h2, h3 {{
        color: {ALLIZ_PLUM};
    }}

    [data-testid="stSidebar"] {{
        background-color: #FFF5F9;
        border-right: 1px solid {ALLIZ_BORDER};
    }}

    [data-testid="stMetric"] {{
        background-color: rgba(255,255,255,0.96);
        border: 1px solid {ALLIZ_BORDER};
        border-top: 4px solid {ALLIZ_PINK};
        border-radius: 12px;
        padding: 0.85rem 1rem;
        box-shadow: 0 6px 18px rgba(67,21,39,0.06);
    }}

    [data-testid="stMetricValue"] {{
        color: {ALLIZ_PLUM};
    }}

    .stTabs [data-baseweb="tab-list"] {{
        border-bottom: 1px solid {ALLIZ_BORDER};
        gap: 0.75rem;
    }}

    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        color: {ALLIZ_PINK};
    }}

    [data-testid="stDataFrame"] {{
        background-color: white;
        border: 1px solid {ALLIZ_BORDER};
        border-radius: 12px;
        overflow: hidden;
    }}

    .alliz-header {{
        margin-bottom: 1.35rem;
        padding: 1.25rem 1.5rem;
        background-color: rgba(255,255,255,0.96);
        border: 1px solid {ALLIZ_BORDER};
        border-left: 6px solid {ALLIZ_PINK};
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(67,21,39,0.08);
    }}

    .alliz-logo {{
        color: {ALLIZ_PINK};
        font-size: 1.25rem;
        font-weight: 800;
        margin-bottom: 0.25rem;
    }}

    .alliz-title {{
        color: {ALLIZ_PLUM};
        font-size: 2.25rem;
        font-weight: 750;
        line-height: 1.1;
    }}

    .alliz-subtitle {{
        margin-top: 0.45rem;
        color: #6A4956;
        font-size: 1rem;
    }}

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="alliz-header">
        <div class="alliz-logo">alliz</div>
        <div class="alliz-title">Member Needs Dashboard</div>
        <div class="alliz-subtitle">
            Bilingual English / Japanese member-needs analysis
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


DATABASE_URL = st.secrets["DATABASE_URL"]



try:
    USE_TEST_TABLES = (
        str(st.secrets["USE_TEST_TABLES"]).lower() == "false"
    )
except Exception:
    USE_TEST_TABLES = true


if USE_TEST_TABLES:

    table_names = {
        "profiles": "test_user_public_profiles",
        "biographies": "test_biographies",
        "professions": "test_professions",
        "educations": "test_university_educations",
    }

else:

    table_names = {
        "profiles": "user_public_profiles",
        "biographies": "biographies",
        "professions": "professions",
        "educations": "university_educations",
    }


# ============================================================
# DATABASE CONNECTION
# ============================================================

@st.cache_resource
def get_database_engine():

    return create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )


# ============================================================
# LOAD FOUR DATABASE TABLES
# ============================================================

@st.cache_data(
    ttl=600,
    show_spinner="Loading member data..."
)
def load_source_data():

    engine = get_database_engine()

    profiles_table = table_names["profiles"]
    biographies_table = table_names["biographies"]
    professions_table = table_names["professions"]
    educations_table = table_names["educations"]


    profiles_query = text(
        f"""
        SELECT
            id AS member_id,
            language,
            gender,
            goal,
            open_to,
            open_to_visibility,
            specialty,
            updated_at,
            completed_at
        FROM {profiles_table}
        ORDER BY id;
        """
    )


    biographies_query = text(
        f"""
        SELECT
            id AS biography_id,
            user_public_profile_id AS member_id,
            profile AS biography_text,
            updated_at AS biography_updated_at
        FROM {biographies_table}
        ORDER BY user_public_profile_id, id;
        """
    )


    professions_query = text(
        f"""
        SELECT
            id AS profession_id,
            user_public_profile_id AS member_id,
            company,
            title,
            department,
            start_year,
            start_month,
            end_year,
            end_month,
            updated_at AS profession_updated_at
        FROM {professions_table}
        ORDER BY user_public_profile_id, id;
        """
    )


    educations_query = text(
        f"""
        SELECT
            id AS education_id,
            user_public_profile_id AS member_id,
            school_name,
            major,
            year_of_study,
            is_currently_enrolled,
            graduation_year,
            graduation_month,
            updated_at AS education_updated_at
        FROM {educations_table}
        ORDER BY user_public_profile_id, id;
        """
    )


    with engine.connect() as connection:

        profiles = pd.read_sql_query(
            profiles_query,
            connection,
        )

        biographies = pd.read_sql_query(
            biographies_query,
            connection,
        )

        professions = pd.read_sql_query(
            professions_query,
            connection,
        )

        educations = pd.read_sql_query(
            educations_query,
            connection,
        )


    return (
        profiles,
        biographies,
        professions,
        educations,
    )


# ============================================================
# TEXT CLEANING
# ============================================================

def normalize_value(value):

    if value is None:
        return ""

    if isinstance(value, dict):

        parts = [
            normalize_value(item)
            for item in value.values()
        ]

        return " ".join(
            part for part in parts if part
        )

    if isinstance(
        value,
        (list, tuple, set),
    ):

        parts = [
            normalize_value(item)
            for item in value
        ]

        return " ".join(
            part for part in parts if part
        )

    try:

        if pd.isna(value):
            return ""

    except (TypeError, ValueError):

        pass


    text_value = str(value).strip()


    # PostgreSQL JSON / JSONB may arrive as JSON strings.
    if text_value.startswith(("[", "{")):

        try:

            return normalize_value(
                json.loads(text_value)
            )

        except (
            json.JSONDecodeError,
            TypeError,
        ):

            pass


    text_value = unicodedata.normalize(
        "NFKC",
        text_value,
    )

    return re.sub(
        r"\s+",
        " ",
        text_value,
    ).strip()


# ============================================================
# COMBINE RELATED RECORDS
# ============================================================

def combine_text(values):

    combined_values = []

    for value in values:

        clean_value = normalize_value(value)

        if (
            clean_value
            and clean_value not in combined_values
        ):

            combined_values.append(
                clean_value
            )

    return "; ".join(
        combined_values
    )


# ============================================================
# CLASSIFICATION RULES
# ============================================================

goal_rules = {

    "Networking": [
        "network",
        "connection",
        "connect",
        "ネットワーク",
        "人脈",
        "つながり",
        "繋がり",
        "交流",
        "コネクション",
    ],

    "Career and Job Support": [
        "job",
        "career",
        "employment",
        "work opportunity",
        "work experience",
        "professional experience",
        "internship experience",
        "intern",
        "仕事",
        "就職",
        "転職",
        "キャリア",
        "求人",
        "就活",
        "働く",
        "実務経験を得たい",
        "インターン経験",
        "インターン",
    ],

    "Learning and Skills": [
        "learn",
        "skill",
        "training",
        "technical",
        "data",
        "coding",
        "gain experience",
        "get experience",
        "build experience",
        "practical experience",
        "hands-on experience",
        "学ぶ",
        "学習",
        "スキル",
        "研修",
        "勉強",
        "技術",
        "データ",
        "プログラミング",
        "経験を積みたい",
        "経験を積む",
        "実践的な経験",
    ],

    "Mentorship": [
        "mentor",
        "guidance",
        "advisor",
        "mentee",
        "メンター",
        "メンタリング",
        "指導",
        "助言",
        "相談",
        "アドバイス",
    ],

    "Entrepreneurship": [
        "business",
        "startup",
        "entrepreneur",
        "founder",
        "ビジネス",
        "スタートアップ",
        "起業",
        "創業",
        "事業",
        "経営",
    ],

    "Community Contribution": [
        "community",
        "contribute",
        "volunteer",
        "support others",
        "コミュニティ",
        "地域",
        "貢献",
        "ボランティア",
        "支援",
        "サポート",
    ],
}


opportunity_rules = {

    "Networking Opportunities": [
        "network",
        "connection",
        "event",
        "ネットワーク",
        "人脈",
        "つながり",
        "繋がり",
        "交流",
        "イベント",
        "交流会",
    ],

    "Mentorship Opportunities": [
        "mentor",
        "guidance",
        "advisor",
        "mentee",
        "メンター",
        "メンタリング",
        "指導",
        "助言",
        "相談",
        "アドバイス",
    ],

    "Jobs and Career Opportunities": [
        "job",
        "career",
        "employment",
        "work opportunity",
        "仕事",
        "就職",
        "転職",
        "キャリア",
        "求人",
        "就活",
    ],

    "Learning Opportunities": [
        "learn",
        "skill",
        "training",
        "workshop",
        "seminar",
        "technical",
        "gain experience",
        "get experience",
        "build experience",
        "practical experience",
        "hands-on experience",
        "学ぶ",
        "学習",
        "スキル",
        "研修",
        "ワークショップ",
        "セミナー",
        "講座",
        "技術",
        "経験を積みたい",
        "経験を積む",
        "実践的な経験",
    ],

    "Collaboration and Projects": [
        "collaborat",
        "project",
        "partner",
        "team",
        "協力",
        "共同",
        "協業",
        "プロジェクト",
        "パートナー",
        "仲間",
        "チーム",
    ],

    "Entrepreneurship Opportunities": [
        "business",
        "startup",
        "entrepreneur",
        "founder",
        "ビジネス",
        "スタートアップ",
        "起業",
        "創業",
        "事業",
        "経営",
    ],
}


industry_rules = {

    "Technology and Data": [
        "technology",
        "data",
        "software",
        "developer",
        "coding",
        "engineer",
        "computer science",
        "information technology",
        "it",
        "programming",
        "web development",
        "app development",
        "テクノロジー",
        "データ",
        "ソフトウェア",
        "開発",
        "プログラミング",
        "エンジニア",
        "技術",
        "コンピュータサイエンス",
        "情報技術",
        "ウェブ開発",
        "アプリ開発",
    ],

    "Business and Entrepreneurship": [
        "business",
        "startup",
        "entrepreneur",
        "founder",
        "operations",
        "business management",
        "general management",
        "operations management",
        "business administration",
        "ビジネス",
        "スタートアップ",
        "起業",
        "創業",
        "経営",
        "事業",
        "運営",
        "管理",
    ],

    "Marketing and Communications": [
        "marketing",
        "media",
        "communication",
        "brand",
        "sales",
        "customer support",
        "マーケティング",
        "メディア",
        "広報",
        "コミュニケーション",
        "ブランド",
        "営業",
        "カスタマーサポート",
    ],

    "Education": [
        "education",
        "teacher",
        "university",
        "school",
        "learning",
        "教育",
        "教師",
        "教員",
        "大学",
        "学校",
        "学習",
    ],

    "Finance": [
        "finance",
        "financial",
        "accounting",
        "banking",
        "investment",
        "金融",
        "財務",
        "会計",
        "銀行",
        "投資",
    ],

    "Design and Creative": [
        "design",
        "designer",
        "graphic design",
        "visual design",
        "product design",
        "ui design",
        "ux design",
        "creative",
        "illustration",
        "デザイン",
        "デザイナー",
        "グラフィックデザイン",
        "ビジュアルデザイン",
        "プロダクトデザイン",
        "uiデザイン",
        "uxデザイン",
        "クリエイティブ",
        "イラスト",
    ],
}


# ============================================================
# CLASSIFICATION FUNCTIONS
# ============================================================

def prepare_for_matching(value):

    return normalize_value(
        value
    ).casefold()


def classify_first_match(
    text_value,
    rules,
    default=OTHER,
):

    normalized_text = prepare_for_matching(
        text_value
    )

    for category, keywords in rules.items():

        if any(
            keyword.casefold() in normalized_text
            for keyword in keywords
        ):

            return category

    return default


def classify_multiple(
    text_value,
    rules,
    default=OTHER,
):

    normalized_text = prepare_for_matching(
        text_value
    )

    matches = []

    for category, keywords in rules.items():

        if any(
            keyword.casefold() in normalized_text
            for keyword in keywords
        ):

            matches.append(
                category
            )

    if matches:
        return "; ".join(matches)

    return default


# ============================================================
# BUILD MEMBER-LEVEL DATASET
# ============================================================

def build_member_dataset(
    profiles_df,
    biographies_df,
    professions_df,
    educations_df,
):

    profiles_clean = (
        profiles_df
        .drop_duplicates(
            subset="member_id"
        )
        .copy()
    )

    biographies_clean = (
        biographies_df
        .drop_duplicates(
            subset="biography_id"
        )
        .copy()
    )

    professions_clean = (
        professions_df
        .drop_duplicates(
            subset="profession_id"
        )
        .copy()
    )

    educations_clean = (
        educations_df
        .drop_duplicates(
            subset="education_id"
        )
        .copy()
    )


    for column in [
        "language",
        "gender",
        "goal",
        "open_to",
        "open_to_visibility",
        "specialty",
    ]:

        profiles_clean[column] = (
            profiles_clean[column]
            .apply(normalize_value)
        )


    biographies_clean[
        "biography_text"
    ] = biographies_clean[
        "biography_text"
    ].apply(normalize_value)


    for column in [
        "company",
        "title",
        "department",
    ]:

        professions_clean[column] = (
            professions_clean[column]
            .apply(normalize_value)
        )


    for column in [
        "school_name",
        "major",
        "year_of_study",
    ]:

        educations_clean[column] = (
            educations_clean[column]
            .apply(normalize_value)
        )


    biography_summary = (
        biographies_clean
        .groupby(
            "member_id",
            as_index=False,
        )
        .agg(
            biography_text=(
                "biography_text",
                combine_text,
            )
        )
    )


    profession_summary = (
        professions_clean
        .groupby(
            "member_id",
            as_index=False,
        )
        .agg(
            companies=(
                "company",
                combine_text,
            ),

            job_titles=(
                "title",
                combine_text,
            ),

            departments=(
                "department",
                combine_text,
            ),

            profession_count=(
                "profession_id",
                "nunique",
            ),
        )
    )


    education_summary = (
        educations_clean
        .groupby(
            "member_id",
            as_index=False,
        )
        .agg(
            schools=(
                "school_name",
                combine_text,
            ),

            majors=(
                "major",
                combine_text,
            ),

            is_currently_enrolled=(
                "is_currently_enrolled",
                "max",
            ),

            education_count=(
                "education_id",
                "nunique",
            ),
        )
    )


    member_df = (
        profiles_clean

        .merge(
            biography_summary,
            on="member_id",
            how="left",
            validate="one_to_one",
        )

        .merge(
            profession_summary,
            on="member_id",
            how="left",
            validate="one_to_one",
        )

        .merge(
            education_summary,
            on="member_id",
            how="left",
            validate="one_to_one",
        )
    )


    text_fields = [
        "goal",
        "open_to",
        "specialty",
        "biography_text",
        "companies",
        "job_titles",
        "departments",
        "schools",
        "majors",
    ]


    for column in text_fields:

        member_df[column] = (
            member_df[column]
            .fillna("")
        )


    member_df[
        "profession_count"
    ] = (
        member_df[
            "profession_count"
        ]
        .fillna(0)
        .astype(int)
    )


    member_df[
        "education_count"
    ] = (
        member_df[
            "education_count"
        ]
        .fillna(0)
        .astype(int)
    )


    member_df[
        "is_currently_enrolled"
    ] = (
        member_df[
            "is_currently_enrolled"
        ]
        .fillna(False)
        .astype(bool)
    )


    return member_df


# ============================================================
# ADD DERIVED CLASSIFICATIONS
# ============================================================

def add_derived_fields(member_df):

    member_df = member_df.copy()


    text_fields = [
        "goal",
        "open_to",
        "specialty",
        "biography_text",
        "companies",
        "job_titles",
        "departments",
        "schools",
        "majors",
    ]


    member_df[
        "analysis_text"
    ] = (
        member_df[text_fields]
        .astype(str)
        .agg(" ".join, axis=1)
        .apply(prepare_for_matching)
    )


    industry_fields = [
        "specialty",
        "biography_text",
        "companies",
        "job_titles",
        "departments",
        "majors",
    ]


    member_df[
        "industry_text"
    ] = (
        member_df[
            industry_fields
        ]
        .astype(str)
        .agg(" ".join, axis=1)
        .apply(prepare_for_matching)
    )


    member_df[
        "goal_category"
    ] = member_df[
        "goal"
    ].apply(
        lambda value:
        classify_first_match(
            value,
            goal_rules,
        )
    )


    member_df[
        "opportunity_category"
    ] = (
        member_df[
            [
                "open_to",
                "goal",
                "biography_text",
            ]
        ]
        .astype(str)
        .agg(" ".join, axis=1)
        .apply(
            lambda value:
            classify_multiple(
                value,
                opportunity_rules,
            )
        )
    )


    member_df[
        "industry_category"
    ] = member_df[
        "industry_text"
    ].apply(
        lambda value:
        classify_first_match(
            value,
            industry_rules,
        )
    )


    def classify_career_stage(row):

        job_text = prepare_for_matching(
            row["job_titles"]
        )


        senior_keywords = [
            "founder",
            "owner",
            "director",
            "head",
            "manager",
            "lead",
            "senior",
            "代表",
            "創業者",
            "経営者",
            "取締役",
            "部長",
            "課長",
            "マネージャー",
            "リーダー",
            "シニア",
        ]


        entry_keywords = [
            "intern",
            "junior",
            "assistant",
            "graduate",
            "entry",
            "インターン",
            "ジュニア",
            "アシスタント",
            "新卒",
            "初級",
        ]


        if bool(
            row["is_currently_enrolled"]
        ):

            return "Student"


        if any(
            keyword.casefold() in job_text
            for keyword in senior_keywords
        ):

            return "Senior or Leadership"


        if any(
            keyword.casefold() in job_text
            for keyword in entry_keywords
        ):

            return "Entry Level"


        if job_text:

            return "Professional"


        return "Not Specified"


    member_df[
        "career_stage"
    ] = member_df.apply(
        classify_career_stage,
        axis=1,
    )


    completeness_fields = [
        "goal",
        "open_to",
        "specialty",
        "biography_text",
        "job_titles",
        "majors",
    ]


    member_df[
        "profile_completeness_pct"
    ] = (
        member_df[
            completeness_fields
        ]
        .apply(
            lambda row:
            row.astype(str)
            .str.strip()
            .ne("")
            .mean()
            * 100,
            axis=1,
        )
        .round(1)
    )


    japanese_character_pattern = (
        r"[぀-ヿ㐀-䶿一-鿿]"
    )


    member_df[
        "contains_japanese"
    ] = (
        member_df[
            "analysis_text"
        ]
        .str.contains(
            japanese_character_pattern,
            regex=True,
            na=False,
        )
    )


    member_df[
        "is_japanese_profile"
    ] = (
        member_df[
            "contains_japanese"
        ]
        |
        member_df[
            "language"
        ].str.contains(
            "Japanese|日本語",
            case=False,
            na=False,
            regex=True,
        )
    )


    member_df[
        "requires_manual_review"
    ] = (
        (
            member_df[
                "goal_category"
            ] == OTHER
        )
        |
        (
            member_df[
                "opportunity_category"
            ] == OTHER
        )
        |
        (
            member_df[
                "industry_category"
            ] == OTHER
        )
    )


    def review_reason(row):

        reasons = []

        if (
            row["goal_category"]
            == OTHER
        ):
            reasons.append("Goal")

        if (
            row[
                "opportunity_category"
            ]
            == OTHER
        ):
            reasons.append(
                "Opportunity"
            )

        if (
            row[
                "industry_category"
            ]
            == OTHER
        ):
            reasons.append(
                "Industry"
            )

        return "; ".join(reasons)


    member_df[
        "review_reason"
    ] = member_df.apply(
        review_reason,
        axis=1,
    )


    return member_df


# ============================================================
# LOAD AND PROCESS DATA
# ============================================================

try:

    source_data = load_source_data()

    member_analysis_df = (
        add_derived_fields(
            build_member_dataset(
                *source_data
            )
        )
    )

except Exception as error:

    st.error(
        "The dashboard could not load the data."
    )

    st.code(
        f"{type(error).__name__}: {error}"
    )

    st.stop()


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.header("Filters")


language_options = sorted(
    member_analysis_df[
        "language"
    ]
    .replace(
        "",
        "Not specified",
    )
    .unique()
)


language_filter = (
    st.sidebar.multiselect(
        "Language",
        language_options,
    )
)


goal_filter = (
    st.sidebar.multiselect(
        "Goal category",
        sorted(
            member_analysis_df[
                "goal_category"
            ].unique()
        ),
    )
)


opportunity_options = sorted(
    {
        category

        for value in member_analysis_df[
            "opportunity_category"
        ]

        for category in value.split(
            "; "
        )
    }
)


opportunity_filter = (
    st.sidebar.multiselect(
        "Opportunity category",
        opportunity_options,
    )
)


industry_filter = (
    st.sidebar.multiselect(
        "Industry category",
        sorted(
            member_analysis_df[
                "industry_category"
            ].unique()
        ),
    )
)


career_filter = (
    st.sidebar.multiselect(
        "Career stage",
        sorted(
            member_analysis_df[
                "career_stage"
            ].unique()
        ),
    )
)


review_filter = (
    st.sidebar.selectbox(
        "Review status",

        [
            "All profiles",
            "Needs manual review",
            "Classified without review",
        ],
    )
)


# ============================================================
# APPLY FILTERS
# ============================================================

filtered_df = (
    member_analysis_df.copy()
)


if language_filter:

    language_values = (
        filtered_df[
            "language"
        ]
        .replace(
            "",
            "Not specified",
        )
    )

    filtered_df = (
        filtered_df[
            language_values.isin(
                language_filter
            )
        ]
    )


if goal_filter:

    filtered_df = filtered_df[
        filtered_df[
            "goal_category"
        ].isin(goal_filter)
    ]


if opportunity_filter:

    filtered_df = filtered_df[
        filtered_df[
            "opportunity_category"
        ].apply(
            lambda value:
            any(
                selected
                in value.split("; ")

                for selected
                in opportunity_filter
            )
        )
    ]


if industry_filter:

    filtered_df = filtered_df[
        filtered_df[
            "industry_category"
        ].isin(industry_filter)
    ]


if career_filter:

    filtered_df = filtered_df[
        filtered_df[
            "career_stage"
        ].isin(career_filter)
    ]


if (
    review_filter
    == "Needs manual review"
):

    filtered_df = filtered_df[
        filtered_df[
            "requires_manual_review"
        ]
    ]


elif (
    review_filter
    == "Classified without review"
):

    filtered_df = filtered_df[
        ~filtered_df[
            "requires_manual_review"
        ]
    ]


# ============================================================
# REFRESH
# ============================================================

if st.sidebar.button(
    "Refresh database data"
):

    st.cache_data.clear()
    st.rerun()


if USE_TEST_TABLES:

    st.sidebar.caption(
        "Environment: Personal test database  \n"
        "Tables: test_*  \n"
        "Database operations: SELECT only"
    )

else:

    st.sidebar.caption(
        "Environment: Alliz database  \n"
        "Tables: production  \n"
        "Database operations: SELECT only"
    )


# ============================================================
# SUMMARY FUNCTIONS
# ============================================================

def category_summary(
    dataframe,
    column,
):

    if dataframe.empty:

        return pd.DataFrame(
            columns=[
                column,
                "member_count",
            ]
        )


    summary = (
        dataframe[
            column
        ]
        .value_counts(
            dropna=False
        )
        .reset_index()
    )


    summary.columns = [
        column,
        "member_count",
    ]


    return summary


def opportunity_summary(
    dataframe,
):

    if dataframe.empty:

        return pd.DataFrame(
            columns=[
                "opportunity_category",
                "member_count",
            ]
        )


    exploded = (
        dataframe.assign(
            opportunity_category=(
                dataframe[
                    "opportunity_category"
                ]
                .str.split("; ")
            )
        )
        .explode(
            "opportunity_category"
        )
    )


    return category_summary(
        exploded,
        "opportunity_category",
    )


def unclear_value_summary(
    dataframe,
    category_column,
    source_column,
):

    unclear = dataframe[
        dataframe[
            category_column
        ] == OTHER
    ]


    if unclear.empty:

        return pd.DataFrame(
            columns=[
                source_column,
                "affected_members",
            ]
        )


    result = (
        unclear.groupby(
            source_column,
            dropna=False,
        )[
            "member_id"
        ]
        .nunique()
        .reset_index(
            name="affected_members"
        )
        .sort_values(
            "affected_members",
            ascending=False,
        )
    )


    return result


# ============================================================
# DASHBOARD TABS
# ============================================================

overview_tab, review_tab, quality_tab = st.tabs(
    [
        "Overview",
        "Manual Review",
        "Data Quality",
    ]
)


# ============================================================
# OVERVIEW
# ============================================================

with overview_tab:

    metric_1, metric_2, metric_3, metric_4, metric_5 = (
        st.columns(5)
    )


    metric_1.metric(
        "Filtered members",
        filtered_df[
            "member_id"
        ].nunique(),
    )


    metric_2.metric(
        "Japanese profiles",
        int(
            filtered_df[
                "is_japanese_profile"
            ].sum()
        ),
    )


    metric_3.metric(
        "Needs review",
        int(
            filtered_df[
                "requires_manual_review"
            ].sum()
        ),
    )


    metric_4.metric(
        "Average completeness",

        (
            f"""
            {
                filtered_df[
                    "profile_completeness_pct"
                ].mean()
            :.1f}%
            """

            if not filtered_df.empty

            else "0.0%"
        ),
    )


    metric_5.metric(
        "Currently enrolled",
        int(
            filtered_df[
                "is_currently_enrolled"
            ].sum()
        ),
    )


    st.divider()


    # --------------------------------------------------------
    # SUMMARY CHARTS
    # --------------------------------------------------------

    goal_summary_df = (
        category_summary(
            filtered_df,
            "goal_category",
        )
    )


    opportunity_summary_df = (
        opportunity_summary(
            filtered_df
        )
    )


    industry_summary_df = (
        category_summary(
            filtered_df,
            "industry_category",
        )
    )


    career_summary_df = (
        category_summary(
            filtered_df,
            "career_stage",
        )
    )


    chart_1, chart_2 = (
        st.columns(2)
    )


    with chart_1:

        st.subheader(
            "Members by Goal Category"
        )

        if not goal_summary_df.empty:

            st.bar_chart(
                goal_summary_df.set_index(
                    "goal_category"
                )[
                    "member_count"
                ]
            )


    with chart_2:

        st.subheader(
            "Members by Opportunity Category"
        )

        if not opportunity_summary_df.empty:

            st.bar_chart(
                opportunity_summary_df.set_index(
                    "opportunity_category"
                )[
                    "member_count"
                ]
            )


    chart_3, chart_4 = (
        st.columns(2)
    )


    with chart_3:

        st.subheader(
            "Members by Industry Category"
        )

        if not industry_summary_df.empty:

            st.bar_chart(
                industry_summary_df.set_index(
                    "industry_category"
                )[
                    "member_count"
                ]
            )


    with chart_4:

        st.subheader(
            "Members by Career Stage"
        )

        if not career_summary_df.empty:

            st.bar_chart(
                career_summary_df.set_index(
                    "career_stage"
                )[
                    "member_count"
                ]
            )


    # --------------------------------------------------------
    # MEMBER RESULTS
    # --------------------------------------------------------

    st.subheader(
        "Filtered Member Results"
    )


    dashboard_columns = [
        "member_id",
        "gender",
        "language",
        "goal_category",
        "opportunity_category",
        "industry_category",
        "career_stage",
        "profile_completeness_pct",
        "profession_count",
        "education_count",
        "requires_manual_review",
    ]


    st.dataframe(
        filtered_df[
            dashboard_columns
        ].sort_values(
            "member_id"
        ),
        hide_index=True,
        use_container_width=True,
    )


# ============================================================
# MANUAL REVIEW
# ============================================================

with review_tab:

    review_queue = (
        filtered_df[
            filtered_df[
                "requires_manual_review"
            ]
        ]
        .copy()
    )


    japanese_review_count = int(
        review_queue[
            "is_japanese_profile"
        ].sum()
    )


    non_japanese_review_count = (
        len(review_queue)
        - japanese_review_count
    )


    review_1, review_2, review_3 = (
        st.columns(3)
    )


    review_1.metric(
        "Profiles requiring review",
        len(review_queue),
    )


    review_2.metric(
        "Japanese requiring review",
        japanese_review_count,
    )


    review_3.metric(
        "Non-Japanese requiring review",
        non_japanese_review_count,
    )


    st.caption(
        "A profile enters the queue when its goal, "
        "opportunity, or industry classification is "
        "'Other or Unclear'."
    )


    review_scope = st.radio(
        "Review group",
        [
            "All",
            "Japanese",
            "Non-Japanese",
        ],
        horizontal=True,
    )


    scoped_review = (
        review_queue.copy()
    )


    if review_scope == "Japanese":

        scoped_review = (
            scoped_review[
                scoped_review[
                    "is_japanese_profile"
                ]
            ]
        )


    elif review_scope == "Non-Japanese":

        scoped_review = (
            scoped_review[
                ~scoped_review[
                    "is_japanese_profile"
                ]
            ]
        )


    review_columns = [
        "member_id",
        "language",
        "review_reason",
        "goal",
        "open_to",
        "specialty",
        "job_titles",
        "departments",
        "majors",
        "goal_category",
        "opportunity_category",
        "industry_category",
        "career_stage",
    ]


    show_biography = st.checkbox(
        "Show biography text in review table",
        value=False,
    )


    if show_biography:

        review_columns.insert(
            6,
            "biography_text",
        )


    st.dataframe(
        scoped_review[
            review_columns
        ].sort_values(
            "member_id"
        ),
        hide_index=True,
        use_container_width=True,
        height=460,
    )


    st.subheader(
        "Repeated Unclear Values"
    )


    unclear_goal_tab, unclear_opportunity_tab, unclear_industry_tab = (
        st.tabs(
            [
                "Goals",
                "Opportunities",
                "Industries",
            ]
        )
    )


    with unclear_goal_tab:

        st.dataframe(
            unclear_value_summary(
                filtered_df,
                "goal_category",
                "goal",
            ),
            hide_index=True,
            use_container_width=True,
        )


    with unclear_opportunity_tab:

        st.dataframe(
            unclear_value_summary(
                filtered_df,
                "opportunity_category",
                "open_to",
            ),
            hide_index=True,
            use_container_width=True,
        )


    with unclear_industry_tab:

        st.dataframe(
            unclear_value_summary(
                filtered_df,
                "industry_category",
                "specialty",
            ),
            hide_index=True,
            use_container_width=True,
        )


# ============================================================
# DATA QUALITY
# ============================================================

with quality_tab:

    profiles_df, biographies_df, professions_df, educations_df = (
        source_data
    )


    quality_rows = []


    for (
        table_name,
        dataframe,
        primary_key,
    ) in [

        (
            table_names["profiles"],
            profiles_df,
            "member_id",
        ),

        (
            table_names["biographies"],
            biographies_df,
            "biography_id",
        ),

        (
            table_names["professions"],
            professions_df,
            "profession_id",
        ),

        (
            table_names["educations"],
            educations_df,
            "education_id",
        ),
    ]:


        quality_rows.append(
            {
                "table": table_name,
                "rows": len(dataframe),
                "columns": len(
                    dataframe.columns
                ),
                "duplicate_primary_keys": int(
                    dataframe[
                        primary_key
                    ].duplicated().sum()
                ),
                "total_missing_values": int(
                    dataframe
                    .isna()
                    .sum()
                    .sum()
                ),
            }
        )


    quality_report = (
        pd.DataFrame(
            quality_rows
        )
    )


    quality_1, quality_2, quality_3, quality_4 = (
        st.columns(4)
    )


    quality_1.metric(
        "Source Tables",
        4,
    )


    quality_2.metric(
        "Member Profiles",
        len(profiles_df),
    )


    quality_3.metric(
        "Total Source Rows",
        (
            len(profiles_df)
            + len(biographies_df)
            + len(professions_df)
            + len(educations_df)
        ),
    )


    quality_4.metric(
        "Members Requiring Review",
        int(
            member_analysis_df[
                "requires_manual_review"
            ].sum()
        ),
    )


    st.subheader(
        "Source Table Quality"
    )


    st.dataframe(
        quality_report,
        hide_index=True,
        use_container_width=True,
    )


    st.subheader(
        "Profile Missingness"
    )


    missing_summary = (
        profiles_df
        .isna()
        .sum()
        .reset_index()
    )


    missing_summary.columns = [
        "column",
        "missing_values",
    ]


    missing_summary[
        "missing_percentage"
    ] = (
        missing_summary[
            "missing_values"
        ]
        / max(
            len(profiles_df),
            1,
        )
        * 100
    ).round(1)


    st.dataframe(
        missing_summary,
        hide_index=True,
        use_container_width=True,
    )
