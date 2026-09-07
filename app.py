
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Alliz Member Needs Dashboard",
    page_icon="📊",
    layout="wide",
)


# ============================================================
# ALLIZ DASHBOARD STYLE
# ============================================================

ALLIZ_PINK = "#E84A8A"
ALLIZ_PLUM = "#431527"
ALLIZ_BACKGROUND = "#FFF9FC"
ALLIZ_BORDER = "#F0D5E0"


st.markdown(
    f"""
    <style>

    .stApp {{
        background:
            radial-gradient(
                circle at 92% 4%,
                #FCE4EE 0,
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
        background-color: white;
        border: 1px solid {ALLIZ_BORDER};
        border-top: 4px solid {ALLIZ_PINK};
        border-radius: 12px;
        padding: 0.85rem 1rem;
        box-shadow: 0 6px 18px rgba(67, 21, 39, 0.06);
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


    .dashboard-header {{
        display: flex;
        align-items: center;
        margin-bottom: 1.5rem;
        padding: 1.25rem 1.5rem;

        background-color: white;

        border: 1px solid {ALLIZ_BORDER};
        border-left: 6px solid {ALLIZ_PINK};
        border-radius: 16px;

        box-shadow: 0 10px 30px rgba(67, 21, 39, 0.08);
    }}


    .dashboard-title {{
        color: {ALLIZ_PLUM};
        font-size: 2.2rem;
        font-weight: 750;
        line-height: 1.1;
    }}


    .dashboard-subtitle {{
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
    <div class="dashboard-header">

        <div>
            <div class="dashboard-title">
                Alliz Member Needs Dashboard
            </div>

            <div class="dashboard-subtitle">
                Bilingual English / Japanese member-needs analysis
            </div>
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

@st.cache_resource
def get_database_engine():

    return create_engine(
        st.secrets["DATABASE_URL"],
        pool_pre_ping=True,
    )


# ============================================================
# LOAD CLASSIFIED DATA
# ============================================================

@st.cache_data(ttl=600)
def load_data():

    query = text(
        """
        SELECT *
        FROM member_profiles_classified_test
        ORDER BY member_id;
        """
    )

    return pd.read_sql_query(
        query,
        get_database_engine(),
    )


try:

    data = load_data()

except Exception as error:

    st.error(
        "The dashboard could not load the database."
    )

    st.code(
        f"{type(error).__name__}: {error}"
    )

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("Dashboard Filters")


# ---------------------------
# MEMBER TYPE FILTER
# ---------------------------

if "member_type" in data.columns:

    member_type_options = sorted(
        data["member_type"]
        .dropna()
        .astype(str)
        .unique()
    )

    selected_member_types = st.sidebar.multiselect(
        "Member Type",
        options=member_type_options,
        default=member_type_options,
    )

else:

    selected_member_types = []


# ---------------------------
# INDUSTRY FILTER
# ---------------------------

if "industry" in data.columns:

    industry_options = sorted(
        data["industry"]
        .dropna()
        .astype(str)
        .unique()
    )

    selected_industries = st.sidebar.multiselect(
        "Industry",
        options=industry_options,
        default=industry_options,
    )

else:

    selected_industries = []


# ---------------------------
# REQUESTED SUPPORT FILTER
# ---------------------------

if "requested_support" in data.columns:

    support_options = sorted(
        data["requested_support"]
        .dropna()
        .astype(str)
        .unique()
    )

    selected_support = st.sidebar.multiselect(
        "Requested Support",
        options=support_options,
        default=support_options,
    )

else:

    selected_support = []


# ============================================================
# APPLY FILTERS
# ============================================================

filtered_data = data.copy()


if (
    "member_type" in filtered_data.columns
    and selected_member_types
):

    filtered_data = filtered_data[
        filtered_data["member_type"].isin(
            selected_member_types
        )
    ]


if (
    "industry" in filtered_data.columns
    and selected_industries
):

    filtered_data = filtered_data[
        filtered_data["industry"].isin(
            selected_industries
        )
    ]


if (
    "requested_support" in filtered_data.columns
    and selected_support
):

    filtered_data = filtered_data[
        filtered_data["requested_support"].isin(
            selected_support
        )
    ]


# ============================================================
# REFRESH BUTTON
# ============================================================

if st.sidebar.button("Refresh Database Data"):

    st.cache_data.clear()
    st.rerun()


st.sidebar.caption(
    "Environment: Test database  \n"
    "Database operations: SELECT only"
)


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
# OVERVIEW TAB
# ============================================================

with overview_tab:

    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    column1, column2, column3, column4 = st.columns(4)


    column1.metric(
        "Total Members",
        (
            filtered_data["member_id"].nunique()
            if "member_id" in filtered_data.columns
            else len(filtered_data)
        ),
    )


    column2.metric(
        "Member Types",
        (
            filtered_data["member_type"].nunique()
            if "member_type" in filtered_data.columns
            else 0
        ),
    )


    column3.metric(
        "Industries",
        (
            filtered_data["industry"].nunique()
            if "industry" in filtered_data.columns
            else 0
        ),
    )


    if "need_categories" in filtered_data.columns:

        all_needs = (
            filtered_data["need_categories"]
            .dropna()
            .astype(str)
            .str.split("; ")
            .explode()
        )

        total_need_categories = all_needs.nunique()

    else:

        total_need_categories = 0


    column4.metric(
        "Need Categories",
        total_need_categories,
    )


    st.divider()


    # ========================================================
    # MEMBERS BY TYPE
    # ========================================================

    st.subheader("Members by Type")

    if "member_type" in filtered_data.columns:

        member_type_counts = (
            filtered_data["member_type"]
            .value_counts()
        )

        st.bar_chart(
            member_type_counts,
            horizontal=True,
        )

    else:

        st.info(
            "member_type column is not available."
        )


    # ========================================================
    # CLASSIFIED MEMBER NEEDS
    # ========================================================

    st.subheader("Classified Member Needs")


    if "need_categories" in filtered_data.columns:

        exploded_needs = filtered_data.assign(
            need_category=(
                filtered_data["need_categories"]
                .fillna("")
                .astype(str)
                .str.split("; ")
            )
        ).explode(
            "need_category"
        )


        exploded_needs = exploded_needs[
            exploded_needs["need_category"] != ""
        ]


        need_counts = (
            exploded_needs["need_category"]
            .value_counts()
        )


        st.bar_chart(
            need_counts,
            horizontal=True,
        )

    else:

        st.info(
            "need_categories column is not available."
        )


    # ========================================================
    # MEMBERS BY INDUSTRY
    # ========================================================

    st.subheader("Members by Industry")


    if "industry" in filtered_data.columns:

        industry_counts = (
            filtered_data["industry"]
            .value_counts()
        )


        st.bar_chart(
            industry_counts,
            horizontal=True,
        )

    else:

        st.info(
            "industry column is not available."
        )


    # ========================================================
    # MEMBER TYPE VS REQUESTED SUPPORT
    # ========================================================

    st.subheader(
        "Member Type and Requested Support"
    )


    if (
        "member_type" in filtered_data.columns
        and
        "requested_support" in filtered_data.columns
    ):

        comparison_table = pd.crosstab(
            filtered_data["member_type"],
            filtered_data["requested_support"],
        )


        st.dataframe(
            comparison_table,
            use_container_width=True,
        )

    else:

        st.info(
            "Member type or requested support data "
            "is not available."
        )


# ============================================================
# MANUAL REVIEW TAB
# ============================================================

with review_tab:

    st.subheader(
        "Profiles Requiring Manual Review"
    )


    # If your classified table contains this column,
    # use it automatically.

    if "requires_manual_review" in filtered_data.columns:

        review_data = filtered_data[
            filtered_data[
                "requires_manual_review"
            ].fillna(False)
        ]


        st.metric(
            "Profiles Requiring Review",
            len(review_data),
        )


        st.dataframe(
            review_data,
            use_container_width=True,
            hide_index=True,
        )


    elif "classification_status" in filtered_data.columns:

        review_data = filtered_data[
            filtered_data[
                "classification_status"
            ]
            .astype(str)
            .str.contains(
                "review|unclear",
                case=False,
                na=False,
            )
        ]


        st.metric(
            "Profiles Requiring Review",
            len(review_data),
        )


        st.dataframe(
            review_data,
            use_container_width=True,
            hide_index=True,
        )


    else:

        st.info(
            "The classified table does not contain a "
            "manual-review status column."
        )

        st.write(
            "You can still inspect all classified members below."
        )


        st.dataframe(
            filtered_data,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# DATA QUALITY TAB
# ============================================================

with quality_tab:

    st.subheader(
        "Data Quality Overview"
    )


    total_rows = len(filtered_data)

    total_columns = len(
        filtered_data.columns
    )


    missing_values = int(
        filtered_data.isna().sum().sum()
    )


    duplicate_rows = int(
        filtered_data.duplicated().sum()
    )


    quality1, quality2, quality3, quality4 = st.columns(4)


    quality1.metric(
        "Rows",
        total_rows,
    )


    quality2.metric(
        "Columns",
        total_columns,
    )


    quality3.metric(
        "Missing Values",
        missing_values,
    )


    quality4.metric(
        "Duplicate Rows",
        duplicate_rows,
    )


    st.divider()


    st.subheader(
        "Missing Values by Column"
    )


    missing_summary = (
        filtered_data
        .isna()
        .sum()
        .reset_index()
    )


    missing_summary.columns = [
        "Column",
        "Missing Values",
    ]


    missing_summary[
        "Missing Percentage"
    ] = (
        missing_summary["Missing Values"]
        / max(len(filtered_data), 1)
        * 100
    ).round(1)


    missing_summary = (
        missing_summary[
            missing_summary[
                "Missing Values"
            ] > 0
        ]
        .sort_values(
            "Missing Values",
            ascending=False,
        )
    )


    if missing_summary.empty:

        st.success(
            "No missing values found."
        )

    else:

        st.dataframe(
            missing_summary,
            use_container_width=True,
            hide_index=True,
        )


    # ========================================================
    # RAW DATA
    # ========================================================

    with st.expander(
        "View Filtered Member Data"
    ):

        st.dataframe(
            filtered_data,
            use_container_width=True,
            hide_index=True,
        )
