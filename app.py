import pandas as pd
import streamlit as st
from datetime import datetime
import os

# --- Streamlit Config ---
st.set_page_config(page_title="KAIOS-TS Dashboard_V4", layout="wide")


# --- File Paths ---
LOG_FILE = "data/Log_AnnotationServices.csv"
CONFIG_FILE = "data/Config_AnnotationServices.csv"
TEAM_FILE = "data/Team_Grouping_KAIOS.xlsx"

# --- File Checks ---
for file, label in [(LOG_FILE, "Log"), (CONFIG_FILE, "Config"), (TEAM_FILE, "Team Group")]:
    if not os.path.exists(file):
        st.error(f"{label} file not found: {file}")
        st.stop()

# --- Load Files ---
df_log = pd.read_csv(LOG_FILE)
df_config = pd.read_csv(CONFIG_FILE)
df_team = pd.read_excel(TEAM_FILE)

# --- Preprocess ---
df_team.columns = df_team.columns.str.strip()
df_team['User'] = df_team['User'].astype(str).str.strip()
df_team['Team_Group'] = df_team['Team_Group'].astype(str).str.strip()

df_log['Date'] = df_log['Date'].astype(str).str.strip()
df_log['Log_Date'] = pd.to_datetime(df_log['Date'], format='%d-%b', errors='coerce').dt.date
today_year = datetime.now().year
df_log['Log_Date'] = df_log['Log_Date'].apply(lambda d: d.replace(year=today_year) if pd.notna(d) else d)
df_log.dropna(subset=['Log_Date'], inplace=True)
df_log['Week'] = pd.to_datetime(df_log['Log_Date']).dt.strftime('%Y-W%U')
df_log['Month'] = pd.to_datetime(df_log['Log_Date']).dt.strftime('%Y-%m')

# --- Constants ---
PROD_TARGET_PER_USER = 1200
QC_TARGET_PER_USER = 2000

# --- Logo and Title Header ---
col1, col2, col3 = st.columns([1, 8, 1])  # Make middle column wider
with col1:
    st.image("data/KAIOS_Logo.jpg", use_container_width=True)
with col2:
    st.markdown(
        """
        <h1 style='
            text-align: center;
            font-size: 50px;
            font-weight: 900;
            margin-bottom: 0;
            color: #003366;
        '>KAIOS-TS Dashboard</h1>
        """,
        unsafe_allow_html=True
    )
with col3:
    st.image("data/RMSI_Logo.jpg", use_container_width=True)


# --- Daily Summary --------------------------------------------------------------------------------------------
daily_summary = (
    df_log[df_log['Activity'].isin(['Production', 'QC'])]
    .groupby(['Log_Date', 'Activity'])['Points']
    .sum()
    .unstack(fill_value=0)
    .reset_index()
    .sort_values('Log_Date', ascending=False)
)

st.markdown("### 📊 Daily Summary")
available_dates = sorted(daily_summary['Log_Date'].unique(), reverse=True)
selected_day = st.selectbox("📅 Select Date for Summary:", options=available_dates)

# Selected Day Metrics
selected_day_data = daily_summary[daily_summary['Log_Date'] == selected_day]

prod_today = int(selected_day_data['Production'].iloc[0]) if 'Production' in selected_day_data.columns and not selected_day_data.empty else 0
qc_today = int(selected_day_data['QC'].iloc[0]) if 'QC' in selected_day_data.columns and not selected_day_data.empty else 0

daily_log = df_log[df_log['Log_Date'] == selected_day]
prod_users = daily_log[daily_log['Activity'] == 'Production']['User'].nunique()
qc_users = daily_log[daily_log['Activity'] == 'QC']['User'].nunique()

prod_total_target = PROD_TARGET_PER_USER * prod_users
qc_total_target = QC_TARGET_PER_USER * qc_users

prod_progress = round((prod_today / prod_total_target) * 100, 1) if prod_total_target > 0 else 0
qc_progress = round((qc_today / qc_total_target) * 100, 1) if qc_total_target > 0 else 0

prod_rate_per_hour = round(prod_today / (prod_users * 8), 1) if prod_users > 0 else 0
qc_rate_per_hour = round(qc_today / (qc_users * 8), 1) if qc_users > 0 else 0

# Layout with 4 columns
col1, col2, col3, col4 = st.columns([1, 2, 2, 2])

with col1:
    st.markdown("**🗓️ Date**")
    st.markdown(f"<div style='font-size: 20px; font-weight: bold; color: #3366cc'>{selected_day.strftime('%d-%b-%Y')}</div>", unsafe_allow_html=True)

with col2:
    st.markdown("**✅ Production Summary**")
    st.markdown(f"<div style='font-size: 24px; font-weight: bold; color: green'>{prod_today:,} Points</div>", unsafe_allow_html=True)
    st.markdown(f"<span style='color: gray;'>👥 {prod_users} resource(s)</span>", unsafe_allow_html=True)
    st.markdown(f"<span style='color: #888;'>🎯 Target: {prod_total_target:,}</span>", unsafe_allow_html=True)
    st.markdown(f"<span style='color: #3366cc;'>📈 Achieved: {prod_progress}%</span>", unsafe_allow_html=True)
    st.markdown(f"<span style='color: #666;'>⏱ Avg Rate/hr: {prod_rate_per_hour}</span>", unsafe_allow_html=True)

with col3:
    st.markdown("**🔍 QC Summary**")
    st.markdown(f"<div style='font-size: 24px; font-weight: bold; color: orange'>{qc_today:,} Points</div>", unsafe_allow_html=True)
    st.markdown(f"<span style='color: gray;'>👥 {qc_users} resource(s)</span>", unsafe_allow_html=True)
    st.markdown(f"<span style='color: #888;'>🎯 Target: {qc_total_target:,}</span>", unsafe_allow_html=True)
    st.markdown(f"<span style='color: #cc6600;'>📈 Achieved: {qc_progress}%</span>", unsafe_allow_html=True)
    st.markdown(f"<span style='color: #666;'>⏱ Avg Rate/hr: {qc_rate_per_hour}</span>", unsafe_allow_html=True)

with col4:
    st.markdown("**📅 Last 5 Days Summary**")

    # Prepare last 5 days Production & QC
    recent_log = df_log[df_log['Activity'].isin(['Production', 'QC'])].copy()
    recent_log_grouped = (
        recent_log.groupby(['Log_Date', 'Activity'])['Points']
        .sum()
        .unstack(fill_value=0)
        .reset_index()
        .sort_values('Log_Date', ascending=False)
        .head(5)
    )

    # Format date for display
    recent_log_grouped['Log_Date'] = pd.to_datetime(recent_log_grouped['Log_Date'], errors='coerce')
    recent_log_grouped['Date'] = recent_log_grouped['Log_Date'].dt.strftime('%d-%b')

    # Final table (only Points, no Achieved %)
    display_5day = recent_log_grouped[['Date', 'Production', 'QC']]
    display_5day = display_5day.rename(columns={
        'Production': 'Prod Points',
        'QC': 'QC Points'
    })

    st.dataframe(display_5day.reset_index(drop=True), hide_index=True, use_container_width=True)


# --- Publication Summary --------------------------------------------------------------------------------

# Get latest update date from log file
latest_updates = df_log.groupby("Publication")["Log_Date"].max().reset_index()
latest_updates.rename(columns={"Log_Date": "Latest_Date"}, inplace=True)

# Custom groupby aggregation with updated Prod_Comp logic
def compute_summary(df):
    def custom_agg(group):
        total_grids = group['Grid'].nunique()
        points = group['Points'].sum()
        output = group['Grid point'].sum()

        # Updated logic for Prod_Comp
        prod_comp = ((group['Latest Status'] == "Comp") |
                     ((group['Latest Status'] == "IP") & (group['Latest Activity'] == "QC"))).sum()

        qc_comp = (group['QC Acceptance'] == "Accepted").sum()

        return pd.Series({
            'Total_Grids': total_grids,
            'Points': points,
            'Output': output,
            'Prod_Comp': prod_comp,
            'QC_Comp': qc_comp
        })

    return df.groupby("Publication").apply(custom_agg).reset_index()

# Apply the summary logic to df_config
summary = compute_summary(df_config)

# Remaining IP calculation
summary['Prod_IP'] = summary['Total_Grids'] - summary['Prod_Comp']
summary['QC_IP'] = summary['Total_Grids'] - summary['QC_Comp']

# Merge with latest update date
summary = pd.merge(summary, latest_updates, on="Publication", how="left")
summary['Latest_Date'] = pd.to_datetime(summary['Latest_Date'])

# Fill nulls and calculate percentage completion
summary[['Points', 'Output']] = summary[['Points', 'Output']].fillna(0).astype(int)
summary['%_Completion'] = summary.apply(
    lambda row: round((row['Prod_Comp'] / row['Total_Grids']) * 100, 1) if row['Total_Grids'] > 0 else 0.0,
    axis=1
)

# --- Publication Display ---
st.subheader("📘 Publication Summary (Top 5 by Latest Date)")

date_options = ['Show All'] + sorted(summary['Latest_Date'].dropna().dt.date.unique(), reverse=True)
selected_option = st.selectbox("📅 Filter by Publication Date:", options=date_options)

if selected_option == 'Show All':
    display_df = summary.sort_values("Latest_Date", ascending=False)
else:
    selected_date = pd.to_datetime(selected_option)
    filtered_df = summary[summary['Latest_Date'].dt.date == selected_date.date()]
    if len(filtered_df) < 5:
        extra = summary[summary['Latest_Date'].dt.date < selected_date.date()]
        extra_needed = 5 - len(filtered_df)
        extra_sorted = extra.sort_values("Latest_Date", ascending=False).head(extra_needed)
        display_df = pd.concat([filtered_df, extra_sorted]).sort_values("Latest_Date", ascending=False)
    else:
        display_df = filtered_df.sort_values("Latest_Date", ascending=False)

st.dataframe(display_df, use_container_width=True)

@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

csv = convert_df(display_df)
st.download_button("📥 Download Publication Summary CSV", csv, "publication_summary.csv", "text/csv")



# --- USER-WISE SUMMARY -----------------------------------------------------------------------------------------------
st.markdown("---")
col1, col2 = st.columns([4, 1])
with col1:
    st.subheader("👤 User-wise Summary")
with col2:
    st.markdown(
        """
        <div style='text-align: right; font-size: 14px; color: gray; margin-top: 15px;'>
            🎯 <b>Prod Target</b>: 1200/day<br>
            🎯 <b>QC Target</b>: 2000/day
        </div>
        """, 
        unsafe_allow_html=True
    )



view_mode = st.radio("Select Summary Type:", ["Day", "Week", "Month"], horizontal=True)

def get_day_multiplier(view_mode):
    if view_mode == 'Day': return 1
    elif view_mode == 'Week': return 5
    elif view_mode == 'Month': return 22
    return 1

if view_mode == 'Day':
    options = sorted(df_log['Log_Date'].unique(), reverse=True)
    selected = st.selectbox("🗓️ Select Date:", options=options)
    log_selected = df_log[df_log['Log_Date'] == selected]
elif view_mode == 'Week':
    options = sorted(df_log['Week'].unique(), reverse=True)
    selected = st.selectbox("🗓️ Select Week:", options=options)
    log_selected = df_log[df_log['Week'] == selected]
elif view_mode == 'Month':
    options = sorted(df_log['Month'].unique(), reverse=True)
    selected = st.selectbox("🗓️ Select Month:", options=options)
    log_selected = df_log[df_log[view_mode] == selected]

# ✅ Filter valid records
valid_rows = log_selected[
    log_selected['Status'].isin(['Comp', 'IP']) &
    log_selected['Activity'].isin(['Production', 'QC'])
].copy()

# ✅ Group Points by User + Activity
point_sums = valid_rows.groupby(['User', 'Activity'])['Points'].sum().reset_index(name='Points')
user_report = point_sums.pivot(index='User', columns='Activity', values='Points').fillna(0).reset_index()
user_report['Total'] = user_report.get('Production', 0) + user_report.get('QC', 0)

# --- Efficiency ---
day_multiplier = get_day_multiplier(view_mode)
user_report['Prod_Eff'] = (user_report.get('Production', 0) / (PROD_TARGET_PER_USER * day_multiplier) * 100).fillna(0).round(1)
user_report['QC_Eff'] = (user_report.get('QC', 0) / (QC_TARGET_PER_USER * day_multiplier) * 100).fillna(0).round(1)

# --- Quality Calculation ---
qc_feedback = log_selected[log_selected['QC Feedback to'].notnull()].copy()
quality = qc_feedback.groupby('QC Feedback to').agg(
    QC_Error_Sum=('Error', 'sum'),
    QC_Error_Points=('Points', 'sum')
).reset_index()
quality['Quality'] = (100 - ((quality['QC_Error_Sum'] / quality['QC_Error_Points']) * 100)).fillna(100).round(1)
quality.rename(columns={'QC Feedback to': 'User'}, inplace=True)

user_report = pd.merge(user_report, quality[['User', 'Quality']], on='User', how='left')
user_report['Quality'] = user_report['Quality'].fillna(100)

# Merge team group
user_report = pd.merge(user_report, df_team[['User', 'Team_Group']], on='User', how='left')
user_report['Team_Group'] = user_report['Team_Group'].fillna("Unassigned")

# --- Filters ---
col1, col2 = st.columns(2)
with col1:
    selected_team = st.selectbox("Filter by Team Group:", ['All'] + sorted(user_report['Team_Group'].unique()))
with col2:
    selected_user = st.selectbox("Filter by User:", ['All'] + sorted(user_report['User'].unique()))

if selected_team != 'All':
    user_report = user_report[user_report['Team_Group'] == selected_team]
if selected_user != 'All':
    user_report = user_report[user_report['User'] == selected_user]

# Rearrange Columns
user_report = user_report[['User', 'Production', 'QC', 'Total', 'Prod_Eff', 'QC_Eff', 'Quality', 'Team_Group']]
st.dataframe(user_report.sort_values(by=['Prod_Eff', 'QC_Eff'], ascending=False), use_container_width=True)

# Download CSV
csv_user = convert_df(user_report)
filename = f"user_summary_{view_mode.lower()}_{selected}.csv"
st.download_button("📅 Download User Summary CSV", csv_user, filename, "text/csv")

# --- Weekly Summary -----------------------------------------------------------------------------------------------------
st.subheader("📅 Weekly User Summary")

# Week selector with unique key
available_weeks = sorted(df_log['Week'].dropna().unique(), reverse=True)
selected_weeks = st.multiselect(
    "Select Week(s) to View",
    options=available_weeks,
    default=available_weeks[0],
    key="weekly_summary_weeks"
)

if selected_weeks:
    WEEKLY_WORKING_DAYS = 5

    # Filter log by selected weeks
    df_week = df_log[df_log['Week'].isin(selected_weeks)]

    # --- Production Pivot ---
    prod_weekly = df_week[df_week['Activity'] == 'Production']
    prod_pivot = prod_weekly.groupby(['User', 'Week'])['Points'].sum().unstack(fill_value=0)
    prod_pivot = prod_pivot.reindex(columns=selected_weeks, fill_value=0)
    prod_pivot.columns = [f'Prod_{w}' for w in prod_pivot.columns]
    prod_pivot = prod_pivot.reset_index()
    prod_pivot['Total_Prod'] = prod_pivot.loc[:, prod_pivot.columns.str.startswith('Prod_')].sum(axis=1)

    # --- QC Pivot ---
    qc_weekly = df_week[df_week['Activity'] == 'QC']
    qc_pivot = qc_weekly.groupby(['User', 'Week'])['Points'].sum().unstack(fill_value=0)
    qc_pivot = qc_pivot.reindex(columns=selected_weeks, fill_value=0)
    qc_pivot.columns = [f'QC_{w}' for w in qc_pivot.columns]
    qc_pivot = qc_pivot.reset_index()
    qc_pivot['Total_QC'] = qc_pivot.loc[:, qc_pivot.columns.str.startswith('QC_')].sum(axis=1)

    # --- Merge both ---
    weekly_data = pd.merge(prod_pivot, qc_pivot, on='User', how='outer').fillna(0)
    weekly_data['Total'] = weekly_data['Total_Prod'] + weekly_data['Total_QC']

    # --- Efficiency ---
    total_weeks = len(selected_weeks)
    weekly_data['Prod_Eff'] = (weekly_data['Total_Prod'] / (PROD_TARGET_PER_USER * WEEKLY_WORKING_DAYS * total_weeks) * 100).astype(int)
    weekly_data['QC_Eff'] = (weekly_data['Total_QC'] / (QC_TARGET_PER_USER * WEEKLY_WORKING_DAYS * total_weeks) * 100).astype(int)

    # --- Quality ---
    qc_feedback = df_week[df_week['QC Feedback to'].notnull()]
    quality_week = qc_feedback.groupby('QC Feedback to').agg(
        QC_Error_Sum=('Error', 'sum'),
        QC_Error_Points=('Points', 'sum')
    ).reset_index()
    quality_week['Quality'] = 100 - ((quality_week['QC_Error_Sum'] / quality_week['QC_Error_Points']) * 100)
    quality_week['Quality'] = quality_week['Quality'].fillna(100).astype(int)
    quality_week.rename(columns={'QC Feedback to': 'User'}, inplace=True)

    # Merge quality
    final_weekly_report = pd.merge(weekly_data, quality_week[['User', 'Quality']], on='User', how='left')
    final_weekly_report['Quality'] = final_weekly_report['Quality'].fillna(100).astype(int)

    # Display
    st.dataframe(
        final_weekly_report.sort_values(by=['Prod_Eff', 'QC_Eff', 'Quality'], ascending=False),
        use_container_width=True
    )

    # Download button
    csv_weekly = convert_df(final_weekly_report)
    filename_week = f"weekly_summary_{'_'.join(selected_weeks)}.csv"
    st.download_button("📥 Download Weekly Summary CSV", csv_weekly, filename_week, "text/csv")

else:
    st.warning("Please select at least one week to view the summary.")

# --- Monthly Summary ---------------------------------------------------------------------------------------------------
st.subheader("📅 Monthly User Summary")

# Month Selector with unique key
available_months = sorted(df_log['Month'].dropna().unique(), reverse=True)
selected_months = st.multiselect(
    "Select Month(s) to View",
    options=available_months,
    default=available_months[0],
    key="monthly_summary_months"
)

if selected_months:
    MONTHLY_WORKING_DAYS = 22
    total_months = len(selected_months)

    # Filter log by selected months
    df_month = df_log[df_log['Month'].isin(selected_months)]

    # --- Production Pivot ---
    prod_monthly = df_month[df_month['Activity'] == 'Production']
    prod_pivot = prod_monthly.groupby(['User', 'Month'])['Points'].sum().unstack(fill_value=0)
    prod_pivot = prod_pivot.reindex(columns=selected_months, fill_value=0)
    prod_pivot.columns = [f'Prod_{m}' for m in prod_pivot.columns]
    prod_pivot = prod_pivot.reset_index()
    prod_pivot['Total_Prod'] = prod_pivot.loc[:, prod_pivot.columns.str.startswith('Prod_')].sum(axis=1)

    # --- QC Pivot ---
    qc_monthly = df_month[df_month['Activity'] == 'QC']
    qc_pivot = qc_monthly.groupby(['User', 'Month'])['Points'].sum().unstack(fill_value=0)
    qc_pivot = qc_pivot.reindex(columns=selected_months, fill_value=0)
    qc_pivot.columns = [f'QC_{m}' for m in qc_pivot.columns]
    qc_pivot = qc_pivot.reset_index()
    qc_pivot['Total_QC'] = qc_pivot.loc[:, qc_pivot.columns.str.startswith('QC_')].sum(axis=1)

    # --- Merge Production & QC ---
    monthly_data = pd.merge(prod_pivot, qc_pivot, on='User', how='outer').fillna(0)
    monthly_data['Total'] = monthly_data['Total_Prod'] + monthly_data['Total_QC']

    # --- Efficiency ---
    monthly_data['Prod_Eff'] = (
        monthly_data['Total_Prod'] / (PROD_TARGET_PER_USER * MONTHLY_WORKING_DAYS * total_months) * 100
    ).astype(int)
    monthly_data['QC_Eff'] = (
        monthly_data['Total_QC'] / (QC_TARGET_PER_USER * MONTHLY_WORKING_DAYS * total_months) * 100
    ).astype(int)

    # --- Quality ---
    qc_feedback = df_month[df_month['QC Feedback to'].notnull()]
    quality_month = qc_feedback.groupby('QC Feedback to').agg(
        QC_Error_Sum=('Error', 'sum'),
        QC_Error_Points=('Points', 'sum')
    ).reset_index()
    quality_month['Quality'] = 100 - ((quality_month['QC_Error_Sum'] / quality_month['QC_Error_Points']) * 100)
    quality_month['Quality'] = quality_month['Quality'].fillna(100).astype(int)
    quality_month.rename(columns={'QC Feedback to': 'User'}, inplace=True)

    # Merge quality into monthly report
    final_monthly_report = pd.merge(monthly_data, quality_month[['User', 'Quality']], on='User', how='left')
    final_monthly_report['Quality'] = final_monthly_report['Quality'].fillna(100).astype(int)

    # Display
    st.dataframe(
        final_monthly_report.sort_values(by=['Prod_Eff', 'QC_Eff', 'Quality'], ascending=False),
        use_container_width=True
    )

    # Download button
    csv_monthly = convert_df(final_monthly_report)
    filename_month = f"monthly_summary_{'_'.join(selected_months)}.csv"
    st.download_button("📥 Download Monthly Summary CSV", csv_monthly, filename_month, "text/csv")

else:
    st.warning("Please select at least one month to view the summary.")




