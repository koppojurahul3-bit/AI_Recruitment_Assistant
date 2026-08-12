import streamlit as st
import analyzer
import pandas as pd
import time


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Recruitment Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# GLOBAL STYLING
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background-color: #0B1120;
    }

    section[data-testid="stSidebar"] {
        background-color: #07101F;
    }

    div[data-testid="stMetric"] {
        background-color: #111827;
        border: 1px solid #1E293B;
        border-radius: 12px;
        padding: 15px;
    }

    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "👥 Candidates",
        "💼 Jobs",
        "📄 Resume Analysis",
        "📊 Reports",
        "📈 Analytics",
        "⚙️ Settings"
    ]
)


# ============================================================
# HEADER
# ============================================================

st.title("🤖 AI Recruitment Assistant")

st.write(
    "Upload resumes and a Job Description to rank candidates, "
    "evaluate skills, and generate AI-powered hiring recommendations."
)


# ============================================================
# FILE UPLOAD
# ============================================================

uploaded_files = st.file_uploader(
    "Upload Resume(s) (PDF)",
    type=["pdf"],
    accept_multiple_files=True
)

job_file = st.file_uploader(
    "Upload Job Description (PDF)",
    type=["pdf"]
)


# ============================================================
# DEFAULT VARIABLES
# ============================================================

results = []
csv_df = pd.DataFrame()

highest_ats = 0
highest_match = 0
average_score = 0
top_candidate = "None"
processing_time = 0

job_description = ""
job_keywords = []


# ============================================================
# ANALYZE RESUMES
# ============================================================

if uploaded_files and job_file:

    start_time = time.time()

    with st.spinner("🔄 Analyzing resumes..."):

        # ----------------------------------------------------
        # JOB DESCRIPTION
        # ----------------------------------------------------

        job_description = analyzer.extract_text(job_file)

        job_keywords = analyzer.extract_job_skills(
            job_description
        )

        # ----------------------------------------------------
        # PROCESS RESUMES
        # ----------------------------------------------------

        for uploaded_file in uploaded_files:

            resume_text = analyzer.extract_text(
                uploaded_file
            )

            categories, keywords = analyzer.detect_skills(
                resume_text
            )

            email = analyzer.extract_email(
                resume_text
            )

            phone = analyzer.extract_phone(
                resume_text
            )

            linkedin = analyzer.extract_linkedin(
                resume_text
            )

            github = analyzer.extract_github(
                resume_text
            )

            experience = analyzer.extract_experience(
                resume_text
            )

            education = analyzer.extract_education(
                resume_text
            )

            projects = analyzer.extract_projects(
                resume_text
            )

            certifications = analyzer.extract_certifications(
                resume_text
            )

            soft_skills = analyzer.extract_soft_skills(
                resume_text
            )

            # ------------------------------------------------
            # SCORES
            # ------------------------------------------------

            score = analyzer.calculate_ats_score(
                keywords,
                job_keywords
            )

            match_percentage = analyzer.calculate_resume_match(
                resume_text,
                job_description
            )

            candidate_score = analyzer.calculate_candidate_score(
                match_percentage,
                score
            )

            # ------------------------------------------------
            # ROLE
            # ------------------------------------------------

            role = analyzer.recommend_role(
                categories
            )

            # ------------------------------------------------
            # MISSING SKILLS
            # ------------------------------------------------

            missing_skills = []

            for skill in job_keywords:

                if skill not in keywords:

                    missing_skills.append(skill)

            # ------------------------------------------------
            # AI ANALYSIS
            # ------------------------------------------------

            strengths = analyzer.generate_strengths(
                categories
            )

            weaknesses = analyzer.generate_weaknesses(
                missing_skills
            )

            suggestions = analyzer.generate_suggestions(
                weaknesses
            )

            recommendation = analyzer.hiring_recommendation(
                match_percentage,
                score
            )

            summary = analyzer.generate_candidate_summary(
                strengths,
                weaknesses,
                recommendation,
                candidate_score
            )

            # ------------------------------------------------
            # SAVE RESULT
            # ------------------------------------------------

            results.append(
                {
                    "filename": uploaded_file.name,

                    "email": email,
                    "phone": phone,
                    "linkedin": linkedin,
                    "github": github,

                    "experience": experience,
                    "education": education,
                    "projects": projects,
                    "certifications": certifications,
                    "soft_skills": soft_skills,

                    "categories": categories,
                    "keywords": keywords,

                    "strengths": strengths,
                    "weaknesses": weaknesses,
                    "suggestions": suggestions,
                    "summary": summary,

                    "score": score,
                    "missing_skills": missing_skills,
                    "match_percentage": match_percentage,

                    "role": role,
                    "recommendation": recommendation,
                    "candidate_score": candidate_score
                }
            )


    # ========================================================
    # SORT RESULTS
    # ========================================================

    results.sort(
        key=lambda x: x["match_percentage"],
        reverse=True
    )


    # ========================================================
    # CREATE CSV DATA
    # ========================================================

    csv_data = []

    for rank, result in enumerate(
        results,
        start=1
    ):

        csv_data.append(
            {
                "Rank": rank,

                "Candidate": result["filename"],

                "Role": result["role"],

                "ATS Score": result["score"],

                "Resume Match": result["match_percentage"],

                "Candidate Score": result["candidate_score"],

                "Recommendation": result["recommendation"],

                "Projects": "; ".join(
                    project["name"]
                    for project in result["projects"]
                ),

                "Certifications": "; ".join(
                    result["certifications"]
                ),

                "Soft Skills": "; ".join(
                    result["soft_skills"]
                )
            }
        )


    csv_df = pd.DataFrame(csv_data)


    # ========================================================
    # CALCULATE DASHBOARD VALUES
    # ========================================================

    if not csv_df.empty:

        highest_ats = csv_df["ATS Score"].max()

        highest_match = csv_df["Resume Match"].max()

        average_score = round(
            csv_df["Candidate Score"].mean(),
            2
        )

        top_candidate = csv_df.iloc[0]["Candidate"]


    end_time = time.time()

    processing_time = round(
        end_time - start_time,
        2
    )


# ============================================================
# DASHBOARD PAGE
# ============================================================

if page == "🏠 Dashboard":

    st.header("📊 Recruitment Dashboard")

    st.write(
        "Overview of your candidate pipeline and hiring insights."
    )

    # --------------------------------------------------------
    # NO DATA
    # --------------------------------------------------------

    if csv_df.empty:

        st.info(
            "📄 No candidates analyzed yet. "
            "Upload resume(s) and a Job Description to begin."
        )

    else:

        # ----------------------------------------------------
        # KPI CARDS
        # ----------------------------------------------------

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "👥 Candidates",
                len(results)
            )

        with col2:

            st.metric(
                "🛡️ Highest ATS",
                f"{highest_ats}%"
            )

        with col3:

            st.metric(
                "🎯 Highest Match",
                f"{round(highest_match, 2)}%"
            )

        with col4:

            st.metric(
                "⭐ Average Score",
                average_score
            )


        st.divider()


        # ----------------------------------------------------
        # TOP CANDIDATE
        # ----------------------------------------------------

        st.subheader("🏆 Top Candidate")

        top_result = results[0]

        top1, top2, top3 = st.columns(3)

        with top1:

            st.metric(
                "Candidate",
                top_result["filename"]
            )

        with top2:

            st.metric(
                "Candidate Score",
                f"{round(top_result['candidate_score'], 2)}/100"
            )

        with top3:

            st.metric(
                "Recommendation",
                top_result["recommendation"]
            )

        st.write(
            f"🎓 **Recommended Role:** {top_result['role']}"
        )


        st.divider()


        # ----------------------------------------------------
        # CANDIDATE RANKING
        # ----------------------------------------------------

        st.subheader("🏅 Candidate Ranking")

        ranking_df = csv_df[
            [
                "Rank",
                "Candidate",
                "Role",
                "ATS Score",
                "Resume Match",
                "Candidate Score",
                "Recommendation"
            ]
        ].copy()

        ranking_df["ATS Score"] = ranking_df[
            "ATS Score"
        ].apply(
            lambda x: f"{x}%"
        )

        ranking_df["Resume Match"] = ranking_df[
            "Resume Match"
        ].apply(
            lambda x: f"{round(x, 2)}%"
        )

        ranking_df["Candidate Score"] = ranking_df[
            "Candidate Score"
        ].apply(
            lambda x: f"{round(x, 2)}/100"
        )

        st.dataframe(
            ranking_df,
            use_container_width=True,
            hide_index=True
        )


        st.divider()


        # ----------------------------------------------------
        # EXPORT
        # ----------------------------------------------------

        st.subheader("📥 Export Results")

        csv = csv_df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            label="📥 Download CSV Report",
            data=csv,
            file_name="Candidate_Report.csv",
            mime="text/csv"
        )


        st.success(
            f"✅ Analysis completed in {processing_time} seconds"
        )


# ============================================================
# CANDIDATES PAGE
# ============================================================

elif page == "👥 Candidates":

    st.header("👥 Candidates")

    st.write(
        "Search, filter, and review evaluated candidates."
    )


    if not results:

        st.info(
            "📄 No candidates available. "
            "Upload resumes and a Job Description first."
        )

    else:

        # ----------------------------------------------------
        # SEARCH
        # ----------------------------------------------------

        search_text = st.text_input(
            "🔎 Search candidates",
            placeholder="Search by candidate name or resume..."
        )


        # ----------------------------------------------------
        # FILTERS
        # ----------------------------------------------------

        filter1, filter2, filter3 = st.columns(3)

        with filter1:

            recommendation_filter = st.selectbox(
                "📌 Recommendation",
                [
                    "All",
                    "Recommended",
                    "Not Recommended"
                ]
            )

        with filter2:

            sort_option = st.selectbox(
                "↕ Sort by",
                [
                    "Candidate Score",
                    "ATS Score",
                    "Resume Match",
                    "Rank"
                ]
            )

        with filter3:

            order_option = st.selectbox(
                "Order",
                [
                    "Highest → Lowest",
                    "Lowest → Highest"
                ]
            )


        # ----------------------------------------------------
        # PREPARE DATA
        # ----------------------------------------------------

        candidates_df = csv_df.copy()


        # Search

        if search_text:

            search_lower = search_text.lower()

            candidates_df = candidates_df[
                candidates_df["Candidate"]
                .str.lower()
                .str.contains(
                    search_lower,
                    na=False
                )
            ]


        # Recommendation filter

        if recommendation_filter == "Recommended":

            candidates_df = candidates_df[
                candidates_df["Recommendation"]
                .str.contains(
                    "Recommended",
                    case=False,
                    na=False
                )
                &
                ~candidates_df["Recommendation"]
                .str.contains(
                    "Not Recommended",
                    case=False,
                    na=False
                )
            ]

        elif recommendation_filter == "Not Recommended":

            candidates_df = candidates_df[
                candidates_df["Recommendation"]
                .str.contains(
                    "Not Recommended",
                    case=False,
                    na=False
                )
            ]


        # ----------------------------------------------------
        # SORT
        # ----------------------------------------------------

        sort_columns = {
            "Candidate Score": "Candidate Score",
            "ATS Score": "ATS Score",
            "Resume Match": "Resume Match",
            "Rank": "Rank"
        }

        selected_column = sort_columns[
            sort_option
        ]

        candidates_df = candidates_df.sort_values(
            by=selected_column,
            ascending=(
                order_option == "Lowest → Highest"
            )
        )


        st.write(
            f"Showing **{len(candidates_df)}** candidate(s)"
        )


        # ----------------------------------------------------
        # RANKING TABLE
        # ----------------------------------------------------

        st.subheader("🏆 Candidate Ranking")

        display_df = candidates_df[
            [
                "Rank",
                "Candidate",
                "Role",
                "ATS Score",
                "Resume Match",
                "Candidate Score",
                "Recommendation"
            ]
        ].copy()

        display_df["ATS Score"] = display_df[
            "ATS Score"
        ].apply(
            lambda x: f"{x}%"
        )

        display_df["Resume Match"] = display_df[
            "Resume Match"
        ].apply(
            lambda x: f"{round(x, 2)}%"
        )

        display_df["Candidate Score"] = display_df[
            "Candidate Score"
        ].apply(
            lambda x: f"{round(x, 2)}/100"
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )


        st.divider()


        # ============================================================
        # INDIVIDUAL CANDIDATE PROFILE
        # ============================================================

        st.divider()

        st.markdown("## 👤 Candidate Analysis")
        st.caption("Select a candidate to view detailed recruitment insights.")

        # ------------------------------------------------------------
        # CANDIDATE SELECTOR
        # ------------------------------------------------------------

        candidate_names = [
            result["filename"]
            for result in results
        ]

        selected_candidate = st.selectbox(
            "Select Candidate",
            candidate_names,
            key="candidate_profile_selector"
        )

        # ------------------------------------------------------------
        # FIND SELECTED CANDIDATE
        # ------------------------------------------------------------

        selected_result = None
        selected_rank = None

        for rank, result in enumerate(results, start=1):

            if result["filename"] == selected_candidate:

                selected_result = result
                selected_rank = rank
                break


        # ------------------------------------------------------------
        # DISPLAY PROFILE
        # ------------------------------------------------------------

        if selected_result:

            result = selected_result
            rank = selected_rank

            # ========================================================
            # HEADER
            # ========================================================

            with st.container(border=True):

                header_left, header_right = st.columns([2.5, 1])

                with header_left:

                    st.markdown(
                        f"### 👤 {result['filename']}"
                    )

                    st.write(
                        f"🎓 **Recommended Role:** {result['role']}"
                    )

                    st.write(
                        f"🏅 **Rank:** #{rank}"
                    )

                    # Contact information
                    contact1, contact2 = st.columns(2)

                    with contact1:

                        st.write(
                            f"📧 **Email:** {result['email']}"
                        )

                        st.write(
                            f"📱 **Phone:** {result['phone']}"
                        )

                    with contact2:

                        st.write(
                            f"💼 **LinkedIn:** {result['linkedin']}"
                        )

                        st.write(
                            f"💻 **GitHub:** {result['github']}"
                        )

                with header_right:

                    score = result["candidate_score"]

                    if score >= 90:

                        candidate_status = "🌟 Excellent"

                    elif score >= 75:

                        candidate_status = "🟢 Strong Candidate"

                    elif score >= 60:

                        candidate_status = "🟡 Average"

                    else:

                        candidate_status = "🔴 Needs Improvement"

                    st.metric(
                        "Candidate Score",
                        f"{round(score, 2)}/100"
                    )

                    st.success(candidate_status)


            # ========================================================
            # PERFORMANCE CARDS
            # ========================================================

            st.markdown("### 📊 Candidate Performance")

            metric1, metric2, metric3, metric4 = st.columns(4)

            with metric1:

                st.metric(
                    "🛡️ ATS Score",
                    f"{result['score']}%"
                )

            with metric2:

                st.metric(
                    "🎯 Resume Match",
                    f"{round(result['match_percentage'], 2)}%"
                )

            with metric3:

                st.metric(
                    "⭐ Candidate Score",
                    f"{round(result['candidate_score'], 2)}/100"
                )

            with metric4:

                st.metric(
                    "🏆 Rank",
                    f"#{rank}"
                )


            # ========================================================
            # SKILLS SECTION
            # ========================================================

            st.markdown("### 🧠 Skills Analysis")

            skill1, skill2, skill3 = st.columns(3)

            # --------------------------------------------------------
            # SKILL COVERAGE
            # --------------------------------------------------------

            with skill1:

                with st.container(border=True):

                    st.markdown("#### 🎯 Skill Coverage")

                    matched_count = len(result["keywords"])
                    missing_count = len(result["missing_skills"])

                    total_skills = (
                        matched_count + missing_count
                    )

                    if total_skills > 0:

                        skill_coverage = round(
                            (matched_count / total_skills) * 100,
                            2
                        )

                    else:

                        skill_coverage = 0

                    st.metric(
                        "Coverage",
                        f"{skill_coverage}%"
                    )

                    st.write(
                        f"Matched Skills: **{matched_count}**"
                    )

                    st.write(
                        f"Missing Skills: **{missing_count}**"
                    )


            # --------------------------------------------------------
            # MATCHED SKILLS
            # --------------------------------------------------------

            with skill2:

                with st.container(border=True):

                    st.markdown("#### 🧠 Matched Skills")

                    if result["keywords"]:

                        skill_cols = st.columns(2)

                        for index, skill in enumerate(
                            result["keywords"]
                        ):

                            with skill_cols[
                                index % 2
                            ]:

                                st.success(skill)

                    else:

                        st.info(
                            "No technologies detected."
                        )


            # --------------------------------------------------------
            # SKILLS GAP
            # --------------------------------------------------------

            with skill3:

                with st.container(border=True):

                    st.markdown("#### ⚠️ Skills Gap")

                    if result["missing_skills"]:

                        for skill in result["missing_skills"]:

                            st.warning(skill)

                    else:

                        st.success(
                            "No major skill gaps detected."
                        )


            # ========================================================
            # EXPERIENCE + EDUCATION
            # ========================================================

            st.markdown("### 🎓 Experience & Education")

            experience_col, education_col = st.columns(2)

            # --------------------------------------------------------
            # EXPERIENCE
            # --------------------------------------------------------

            with experience_col:

                with st.container(border=True):

                    st.markdown("#### 💼 Experience")

                    if result["experience"] == 0:

                        st.metric(
                            "Total Experience",
                            "Fresher"
                        )

                    else:

                        st.metric(
                            "Total Experience",
                            f"{result['experience']} years"
                        )

                    st.caption(
                        "Professional experience detected from resume."
                    )


            # --------------------------------------------------------
            # EDUCATION
            # --------------------------------------------------------

            with education_col:

                with st.container(border=True):

                    st.markdown("#### 🎓 Education")

                    if not result["education"]:

                        st.info(
                            "Education details not found."
                        )

                    else:

                        for education in result["education"]:

                            st.markdown(
                                f"**{education['degree']}**"
                            )

                            st.write(
                                f"📚 Field: {education['field']}"
                            )

                            st.write(
                                f"🏫 Institution: "
                                f"{education['institution']}"
                            )

                            st.write(
                                f"📅 Year: {education['year']}"
                            )

                            st.divider()


            # ========================================================
            # PROJECTS + CERTIFICATIONS
            # ========================================================

            project_col, certification_col = st.columns(2)

            # --------------------------------------------------------
            # PROJECTS
            # --------------------------------------------------------

            with project_col:

                with st.container(border=True):

                    st.markdown("### 🚀 Projects")

                    if not result["projects"]:

                        st.info(
                            "No projects detected."
                        )

                    else:

                        for project in result["projects"]:

                            st.markdown(
                                f"#### 📌 {project['name']}"
                            )

                            if project["description"]:

                                for description in project[
                                    "description"
                                ]:

                                    st.write(
                                        f"• {description}"
                                    )

                            else:

                                st.caption(
                                    "No project description detected."
                                )

                            if project["technologies"]:

                                st.write(
                                    "**Technologies**"
                                )

                                tech_cols = st.columns(3)

                                for index, technology in enumerate(
                                    project["technologies"]
                                ):

                                    with tech_cols[
                                        index % 3
                                    ]:

                                        st.success(
                                            technology
                                        )

                            st.divider()


            # --------------------------------------------------------
            # CERTIFICATIONS
            # --------------------------------------------------------

            with certification_col:

                with st.container(border=True):

                    st.markdown("### 🏆 Certifications")

                    if not result["certifications"]:

                        st.info(
                            "No certifications detected."
                        )

                    else:

                        for certification in result[
                            "certifications"
                        ]:

                            st.success(
                                f"✓ {certification}"
                            )


            # ========================================================
            # STRENGTHS + SOFT SKILLS
            # ========================================================

            strength_col, soft_col = st.columns(2)

            # --------------------------------------------------------
            # STRENGTHS
            # --------------------------------------------------------

            with strength_col:

                with st.container(border=True):

                    st.markdown("### 💪 Strengths")

                    if not result["strengths"]:

                        st.info(
                            "No major strengths detected."
                        )

                    else:

                        for strength in result["strengths"]:

                            st.success(
                                strength
                            )


            # --------------------------------------------------------
            # SOFT SKILLS
            # --------------------------------------------------------

            with soft_col:

                with st.container(border=True):

                    st.markdown("### 🧠 Soft Skills")

                    if not result["soft_skills"]:

                        st.info(
                            "No soft skills detected."
                        )

                    else:

                        soft_cols = st.columns(2)

                        for index, skill in enumerate(
                            result["soft_skills"]
                        ):

                            with soft_cols[
                                index % 2
                            ]:

                                st.success(skill)


            # ========================================================
            # AREAS FOR IMPROVEMENT + AI SUGGESTIONS
            # ========================================================

            improvement_col, suggestion_col = st.columns(2)

            # --------------------------------------------------------
            # WEAKNESSES
            # --------------------------------------------------------

            with improvement_col:

                with st.container(border=True):

                    st.markdown(
                        "### ⚠️ Areas for Improvement"
                    )

                    if not result["weaknesses"]:

                        st.success(
                            "No major weaknesses detected."
                        )

                    else:

                        for weakness in result["weaknesses"]:

                            st.warning(
                                weakness
                            )


            # --------------------------------------------------------
            # AI SUGGESTIONS
            # --------------------------------------------------------

            with suggestion_col:

                with st.container(border=True):

                    st.markdown(
                        "### 💡 AI Suggestions"
                    )

                    if not result["suggestions"]:

                        st.success(
                            "No suggestions required."
                        )

                    else:

                        for suggestion in result["suggestions"]:

                            st.info(
                                suggestion
                            )


            # ========================================================
            # AI SUMMARY
            # ========================================================

            with st.container(border=True):

                st.markdown(
                    "### 📝 AI Candidate Summary"
                )

                st.info(
                    result["summary"]
                )


            # ========================================================
            # PERFORMANCE BARS
            # ========================================================

            with st.container(border=True):

                st.markdown(
                    "### 📈 Overall Performance"
                )

                st.write(
                    f"🛡️ ATS Score — {result['score']}%"
                )

                st.progress(
                    min(
                        int(result["score"]),
                        100
                    )
                )

                st.write(
                    f"🎯 Resume Match — "
                    f"{round(result['match_percentage'], 2)}%"
                )

                st.progress(
                    min(
                        int(result["match_percentage"]),
                        100
                    )
                )

                st.write(
                    f"⭐ Candidate Score — "
                    f"{round(result['candidate_score'], 2)}/100"
                )

                st.progress(
                    min(
                        int(result["candidate_score"]),
                        100
                    )
                )


            # ========================================================
            # HIRING RECOMMENDATION
            # ========================================================

            st.markdown("### 🤖 Hiring Recommendation")

            recommendation = result["recommendation"]

            if "Not Recommended" in recommendation:

                st.warning(
                    f"⚠️ {recommendation}"
                )

            else:

                st.success(
                    f"✅ {recommendation}"
                )


            # ========================================================
            # PDF REPORT
            # ========================================================

            st.markdown("### 📄 Candidate Report")

            pdf_filename = (
                f"{result['filename']}_Report.pdf"
            )

            try:

                analyzer.generate_pdf_report(
                    result,
                    pdf_filename
                )

                with open(
                    pdf_filename,
                    "rb"
                ) as pdf_file:

                    pdf_data = pdf_file.read()

                st.download_button(
                    label="📄 Download PDF Report",
                    data=pdf_data,
                    file_name=pdf_filename,
                    mime="application/pdf",
                    key=f"candidate_pdf_{rank}"
                )

            except Exception as error:

                st.error(
                    f"Unable to generate PDF report: {error}"
                )

# ============================================================
# JOBS PAGE
# ============================================================

if page == "💼 Jobs":

    st.markdown("## 💼 Job Details")

    st.caption(
        "Review the active job description, required skills, "
        "qualifications, responsibilities, and hiring requirements."
    )

    # --------------------------------------------------------
    # CHECK JOB DESCRIPTION
    # --------------------------------------------------------

    if not job_file:

        st.info(
            "📄 No Job Description uploaded yet."
        )

        st.write(
            "Upload a Job Description PDF from the upload section "
            "above to view job details here."
        )

    else:

        # ----------------------------------------------------
        # EXTRACT JOB DESCRIPTION
        # ----------------------------------------------------

        try:

            job_text = analyzer.extract_text(
                job_file
            )

        except Exception as error:

            st.error(
                f"Unable to read Job Description: {error}"
            )

            job_text = ""

        if job_text:

            # ------------------------------------------------
            # EXTRACT REQUIRED SKILLS
            # ------------------------------------------------

            detected_categories, detected_keywords = (
                analyzer.detect_skills(job_text)
            )

            job_keywords_display = detected_keywords

            # ------------------------------------------------
            # JOB HEADER
            # ------------------------------------------------

            with st.container(border=True):

                st.markdown(
                    "### 📋 Active Job"
                )

                st.markdown(
                    f"## 💼 {job_file.name}"
                )

                st.caption(
                    "Uploaded Job Description"
                )

                st.divider()

                header1, header2, header3 = st.columns(3)

                with header1:

                    st.metric(
                        "🛠 Required Skills",
                        len(job_keywords_display)
                    )

                with header2:

                    st.metric(
                        "📚 Skill Categories",
                        len(detected_categories)
                    )

                with header3:

                    st.metric(
                        "📄 Document",
                        "PDF"
                    )


            # =================================================
            # REQUIRED SKILLS
            # =================================================

            st.markdown("### 🧠 Required Skills")

            if job_keywords_display:

                skill_columns = st.columns(4)

                for index, skill in enumerate(
                    job_keywords_display
                ):

                    with skill_columns[
                        index % 4
                    ]:

                        st.success(
                            skill
                        )

            else:

                st.info(
                    "No technical skills detected."
                )


            # =================================================
            # JOB OVERVIEW
            # =================================================

            overview_col, requirement_col = st.columns(
                [1.5, 1]
            )

            # -------------------------------------------------
            # JOB DESCRIPTION
            # -------------------------------------------------

            with overview_col:

                with st.container(border=True):

                    st.markdown(
                        "### 📝 Job Description"
                    )

                    st.write(
                        job_text
                    )


            # -------------------------------------------------
            # REQUIREMENT SUMMARY
            # -------------------------------------------------

            with requirement_col:

                with st.container(border=True):

                    st.markdown(
                        "### 🎯 Requirement Summary"
                    )

                    st.write(
                        f"**Total Detected Skills:** "
                        f"{len(job_keywords_display)}"
                    )

                    st.write(
                        f"**Skill Categories:** "
                        f"{len(detected_categories)}"
                    )

                    if detected_categories:

                        st.markdown(
                            "#### Skill Areas"
                        )

                        for category in sorted(
                            detected_categories
                        ):

                            st.write(
                                f"• {category}"
                            )

                    else:

                        st.info(
                            "No categories detected."
                        )


            # =================================================
            # CANDIDATE MATCH AGAINST JOB
            # =================================================

            st.markdown(
                "### 🎯 Candidate Matching"
            )

            if results:

                # ---------------------------------------------
                # MATCH STATISTICS
                # ---------------------------------------------

                match1, match2, match3, match4 = st.columns(4)

                match_values = [
                    result["match_percentage"]
                    for result in results
                ]

                candidate_scores = [
                    result["candidate_score"]
                    for result in results
                ]

                if match_values:

                    highest_job_match = max(
                        match_values
                    )

                    average_job_match = round(
                        sum(match_values)
                        / len(match_values),
                        2
                    )

                else:

                    highest_job_match = 0
                    average_job_match = 0

                if candidate_scores:

                    highest_candidate_score = max(
                        candidate_scores
                    )

                else:

                    highest_candidate_score = 0

                with match1:

                    st.metric(
                        "👥 Candidates",
                        len(results)
                    )

                with match2:

                    st.metric(
                        "🎯 Best Resume Match",
                        f"{round(highest_job_match, 2)}%"
                    )

                with match3:

                    st.metric(
                        "📊 Average Match",
                        f"{average_job_match}%"
                    )

                with match4:

                    st.metric(
                        "⭐ Best Candidate Score",
                        f"{round(highest_candidate_score, 2)}"
                    )


                # ---------------------------------------------
                # CANDIDATE MATCH TABLE
                # ---------------------------------------------

                st.markdown(
                    "#### 🏆 Candidate Match Ranking"
                )

                job_match_data = []

                for rank, candidate in enumerate(
                    results,
                    start=1
                ):

                    job_match_data.append({

                        "Rank": rank,

                        "Candidate":
                            candidate["filename"],

                        "Role":
                            candidate["role"],

                        "Resume Match":
                            round(
                                candidate[
                                    "match_percentage"
                                ],
                                2
                            ),

                        "ATS Score":
                            candidate["score"],

                        "Candidate Score":
                            round(
                                candidate[
                                    "candidate_score"
                                ],
                                2
                            ),

                        "Recommendation":
                            candidate[
                                "recommendation"
                            ]
                    })


                job_match_df = pd.DataFrame(
                    job_match_data
                )

                st.dataframe(
                    job_match_df,
                    use_container_width=True,
                    hide_index=True
                )


            else:

                st.info(
                    "No candidates have been analyzed "
                    "against this job yet."
                )


            # =================================================
            # HIRING REQUIREMENTS
            # =================================================

            st.markdown(
                "### 📌 Hiring Requirements"
            )

            requirement1, requirement2 = st.columns(2)

            with requirement1:

                with st.container(border=True):

                    st.markdown(
                        "#### 🧠 Technical Requirements"
                    )

                    if job_keywords_display:

                        for skill in job_keywords_display:

                            st.write(
                                f"• {skill}"
                            )

                    else:

                        st.info(
                            "No technical requirements detected."
                        )


            with requirement2:

                with st.container(border=True):

                    st.markdown(
                        "#### 🎓 Candidate Expectations"
                    )

                    st.write(
                        "• Relevant technical experience"
                    )

                    st.write(
                        "• Skills matching the job description"
                    )

                    st.write(
                        "• Strong problem-solving ability"
                    )

                    st.write(
                        "• Relevant projects and experience"
                    )

                    st.write(
                        "• Strong overall resume-to-job match"
                    )


            # =================================================
            # RAW JOB DOCUMENT
            # =================================================

            with st.expander(
                "📄 View Full Job Description Text",
                expanded=False
            ):

                st.text(
                    job_text
                )


        else:

            st.warning(
                "The uploaded Job Description contains "
                "no readable text."
            )


# ============================================================
# RESUME ANALYSIS PAGE
# ============================================================

elif page == "📄 Resume Analysis":

    st.markdown("## 📄 Resume Analysis")

    st.caption(
        "Detailed extraction and AI-powered analysis of an individual resume."
    )

    # --------------------------------------------------------
    # CHECK DATA
    # --------------------------------------------------------

    if not results:

        st.info(
            "📄 No resumes analyzed yet. "
            "Upload resume(s) and a Job Description first."
        )

    else:

        # ----------------------------------------------------
        # CANDIDATE SELECTOR
        # ----------------------------------------------------

        candidate_names = [
            result["filename"]
            for result in results
        ]

        selected_resume = st.selectbox(
            "Select Resume",
            candidate_names,
            key="resume_analysis_selector"
        )


        # ----------------------------------------------------
        # FIND SELECTED RESUME
        # ----------------------------------------------------

        selected_result = None
        selected_rank = None

        for rank, result in enumerate(
            results,
            start=1
        ):

            if result["filename"] == selected_resume:

                selected_result = result
                selected_rank = rank

                break


        # ----------------------------------------------------
        # ANALYSIS
        # ----------------------------------------------------

        if selected_result:

            result = selected_result


            # =================================================
            # RESUME OVERVIEW
            # =================================================

            st.markdown("### 📋 Resume Overview")

            overview1, overview2, overview3, overview4 = (
                st.columns(4)
            )

            with overview1:

                st.metric(
                    "👤 Candidate",
                    result["filename"]
                )

            with overview2:

                st.metric(
                    "🏅 Rank",
                    f"#{selected_rank}"
                )

            with overview3:

                st.metric(
                    "🎓 Recommended Role",
                    result["role"]
                )

            with overview4:

                st.metric(
                    "💼 Experience",
                    (
                        "Fresher"
                        if result["experience"] == 0
                        else f"{result['experience']} years"
                    )
                )


            # =================================================
            # CONTACT INFORMATION
            # =================================================

            with st.expander(
                "📞 Contact Information",
                expanded=False
            ):

                contact1, contact2 = st.columns(2)

                with contact1:

                    st.write(
                        f"**📧 Email:** "
                        f"{result['email']}"
                    )

                    st.write(
                        f"**📱 Phone:** "
                        f"{result['phone']}"
                    )

                with contact2:

                    st.write(
                        f"**💼 LinkedIn:** "
                        f"{result['linkedin']}"
                    )

                    st.write(
                        f"**💻 GitHub:** "
                        f"{result['github']}"
                    )


            # =================================================
            # EDUCATION
            # =================================================

            with st.expander(
                "🎓 Education",
                expanded=False
            ):

                if not result["education"]:

                    st.info(
                        "Education details not detected."
                    )

                else:

                    for education in result["education"]:

                        st.markdown(
                            f"### {education['degree']}"
                        )

                        st.write(
                            f"**Field:** "
                            f"{education['field']}"
                        )

                        st.write(
                            f"**Institution:** "
                            f"{education['institution']}"
                        )

                        st.write(
                            f"**Year:** "
                            f"{education['year']}"
                        )

                        st.divider()


            # =================================================
            # TECHNICAL SKILLS
            # =================================================

            st.markdown("### 🧠 Technical Skills")

            if result["keywords"]:

                skill_columns = st.columns(4)

                for index, skill in enumerate(
                    result["keywords"]
                ):

                    with skill_columns[
                        index % 4
                    ]:

                        st.success(skill)

            else:

                st.info(
                    "No technical skills detected."
                )


            # =================================================
            # MISSING JOB SKILLS
            # =================================================

            with st.expander(
                "⚠️ Missing Job Skills",
                expanded=False
            ):

                if result["missing_skills"]:

                    missing_columns = st.columns(3)

                    for index, skill in enumerate(
                        result["missing_skills"]
                    ):

                        with missing_columns[
                            index % 3
                        ]:

                            st.warning(skill)

                else:

                    st.success(
                        "No major missing job skills detected."
                    )


            # =================================================
            # PROJECTS
            # =================================================

            st.markdown("### 🚀 Projects")

            if not result["projects"]:

                st.info(
                    "No projects detected."
                )

            else:

                for project in result["projects"]:

                    with st.container(
                        border=True
                    ):

                        st.markdown(
                            f"#### 📌 {project['name']}"
                        )

                        if project["description"]:

                            for description in project[
                                "description"
                            ]:

                                st.write(
                                    f"• {description}"
                                )

                        else:

                            st.caption(
                                "No project description detected."
                            )

                        if project["technologies"]:

                            st.write(
                                "**🛠 Technologies**"
                            )

                            technology_columns = (
                                st.columns(3)
                            )

                            for index, technology in enumerate(
                                project["technologies"]
                            ):

                                with technology_columns[
                                    index % 3
                                ]:

                                    st.success(
                                        technology
                                    )


            # =================================================
            # CERTIFICATIONS
            # =================================================

            st.markdown("### 🏆 Certifications")

            if not result["certifications"]:

                st.info(
                    "No certifications detected."
                )

            else:

                certification_columns = (
                    st.columns(3)
                )

                for index, certification in enumerate(
                    result["certifications"]
                ):

                    with certification_columns[
                        index % 3
                    ]:

                        st.success(
                            f"✓ {certification}"
                        )


            # =================================================
            # SOFT SKILLS
            # =================================================

            st.markdown("### 🧠 Soft Skills")

            if not result["soft_skills"]:

                st.info(
                    "No soft skills detected."
                )

            else:

                soft_skill_columns = st.columns(3)

                for index, skill in enumerate(
                    result["soft_skills"]
                ):

                    with soft_skill_columns[
                        index % 3
                    ]:

                        st.success(skill)


            # =================================================
            # STRENGTHS
            # =================================================

            st.markdown("### 💪 Strengths")

            if not result["strengths"]:

                st.info(
                    "No strengths detected."
                )

            else:

                strength_columns = st.columns(2)

                for index, strength in enumerate(
                    result["strengths"]
                ):

                    with strength_columns[
                        index % 2
                    ]:

                        st.success(strength)


            # =================================================
            # AREAS FOR IMPROVEMENT
            # =================================================

            st.markdown(
                "### ⚠️ Areas for Improvement"
            )

            if not result["weaknesses"]:

                st.success(
                    "No major weaknesses detected."
                )

            else:

                weakness_columns = st.columns(2)

                for index, weakness in enumerate(
                    result["weaknesses"]
                ):

                    with weakness_columns[
                        index % 2
                    ]:

                        st.warning(weakness)


            # =================================================
            # AI SUGGESTIONS
            # =================================================

            st.markdown("### 💡 AI Suggestions")

            if not result["suggestions"]:

                st.success(
                    "No suggestions required."
                )

            else:

                suggestion_columns = st.columns(2)

                for index, suggestion in enumerate(
                    result["suggestions"]
                ):

                    with suggestion_columns[
                        index % 2
                    ]:

                        st.info(suggestion)


            # =================================================
            # AI SUMMARY
            # =================================================

            with st.container(
                border=True
            ):

                st.markdown(
                    "### 📝 AI Candidate Summary"
                )

                st.info(
                    result["summary"]
                )


            # =================================================
            # SCORE ANALYSIS
            # =================================================

            st.markdown("### 📊 Score Analysis")

            score1, score2, score3 = st.columns(3)

            with score1:

                st.metric(
                    "🛡️ ATS Score",
                    f"{result['score']}%"
                )

            with score2:

                st.metric(
                    "🎯 Resume Match",
                    f"{round(result['match_percentage'], 2)}%"
                )

            with score3:

                st.metric(
                    "⭐ Candidate Score",
                    f"{round(result['candidate_score'], 2)}/100"
                )


            # -------------------------------------------------
            # SCORE PROGRESS
            # -------------------------------------------------

            st.write(
                f"ATS Score — {result['score']}%"
            )

            st.progress(
                min(
                    int(result["score"]),
                    100
                )
            )

            st.write(
                f"Resume Match — "
                f"{round(result['match_percentage'], 2)}%"
            )

            st.progress(
                min(
                    int(result["match_percentage"]),
                    100
                )
            )

            st.write(
                f"Candidate Score — "
                f"{round(result['candidate_score'], 2)}/100"
            )

            st.progress(
                min(
                    int(result["candidate_score"]),
                    100
                )
            )


            # =================================================
            # HIRING RECOMMENDATION
            # =================================================

            st.markdown(
                "### 🤖 Hiring Recommendation"
            )

            if (
                "Not Recommended"
                in result["recommendation"]
            ):

                st.warning(
                    result["recommendation"]
                )

            else:

                st.success(
                    result["recommendation"]
                )


            # =================================================
            # PDF REPORT
            # =================================================

            st.markdown(
                "### 📄 Resume Report"
            )

            pdf_filename = (
                f"{result['filename']}_Report.pdf"
            )

            try:

                analyzer.generate_pdf_report(
                    result,
                    pdf_filename
                )

                with open(
                    pdf_filename,
                    "rb"
                ) as pdf_file:

                    pdf_data = pdf_file.read()

                st.download_button(
                    label="📄 Download PDF Report",
                    data=pdf_data,
                    file_name=pdf_filename,
                    mime="application/pdf",
                    key=f"resume_pdf_{selected_rank}"
                )

            except Exception as error:

                st.error(
                    f"Unable to generate PDF report: {error}"
                )


# ============================================================
# REPORTS PAGE
# ============================================================

elif page == "📊 Reports":

    st.markdown("## 📊 Recruitment Reports")

    st.caption(
        "Review recruitment results and download candidate reports."
    )

    # --------------------------------------------------------
    # CHECK DATA
    # --------------------------------------------------------

    if not results:

        st.info(
            "📄 No recruitment report is available yet. "
            "Upload resumes and a Job Description first."
        )

    else:

        # ====================================================
        # REPORT OVERVIEW
        # ====================================================

        st.markdown("### 📈 Report Overview")

        report1, report2, report3, report4 = st.columns(4)

        with report1:

            st.metric(
                "👥 Candidates Evaluated",
                len(results)
            )

        with report2:

            st.metric(
                "🛡️ Highest ATS",
                f"{highest_ats}%"
            )

        with report3:

            st.metric(
                "🎯 Highest Match",
                f"{round(highest_match, 2)}%"
            )

        with report4:

            st.metric(
                "⭐ Average Score",
                f"{average_score}/100"
            )


        st.divider()


        # ====================================================
        # COMPLETE RECRUITMENT REPORT
        # ====================================================

        st.markdown(
            "### 📋 Complete Recruitment Report"
        )

        report_df = csv_df[
            [
                "Rank",
                "Candidate",
                "Role",
                "ATS Score",
                "Resume Match",
                "Candidate Score",
                "Recommendation"
            ]
        ].copy()


        report_df["ATS Score"] = report_df[
            "ATS Score"
        ].apply(
            lambda x: f"{x}%"
        )


        report_df["Resume Match"] = report_df[
            "Resume Match"
        ].apply(
            lambda x: f"{round(x, 2)}%"
        )


        report_df["Candidate Score"] = report_df[
            "Candidate Score"
        ].apply(
            lambda x: f"{round(x, 2)}/100"
        )


        st.dataframe(
            report_df,
            use_container_width=True,
            hide_index=True
        )


        st.divider()


        # ====================================================
        # CSV EXPORT
        # ====================================================

        st.markdown(
            "### 📥 Export Recruitment Data"
        )

        csv_data = csv_df.to_csv(
            index=False
        ).encode("utf-8")


        st.download_button(
            label="📥 Download Complete CSV Report",
            data=csv_data,
            file_name="AI_Recruitment_Report.csv",
            mime="text/csv",
            key="complete_csv_report"
        )


        st.divider()


        # ====================================================
        # INDIVIDUAL PDF REPORTS
        # ====================================================

        st.markdown(
            "### 📄 Candidate PDF Reports"
        )

        st.caption(
            "Select a candidate to generate and download their detailed PDF report."
        )


        candidate_names = [
            result["filename"]
            for result in results
        ]


        selected_report_candidate = st.selectbox(
            "Select Candidate",
            candidate_names,
            key="report_candidate_selector"
        )


        selected_report_result = None


        for result in results:

            if (
                result["filename"]
                == selected_report_candidate
            ):

                selected_report_result = result

                break


        if selected_report_result:

            result = selected_report_result


            # ------------------------------------------------
            # REPORT PREVIEW
            # ------------------------------------------------

            with st.container(
                border=True
            ):

                st.markdown(
                    f"### 👤 {result['filename']}"
                )

                preview1, preview2, preview3 = (
                    st.columns(3)
                )

                with preview1:

                    st.metric(
                        "🛡️ ATS Score",
                        f"{result['score']}%"
                    )

                with preview2:

                    st.metric(
                        "🎯 Resume Match",
                        f"{round(result['match_percentage'], 2)}%"
                    )

                with preview3:

                    st.metric(
                        "⭐ Candidate Score",
                        f"{round(result['candidate_score'], 2)}/100"
                    )


                st.write(
                    f"🎓 **Role:** {result['role']}"
                )

                st.write(
                    f"🤖 **Recommendation:** "
                    f"{result['recommendation']}"
                )


            # ------------------------------------------------
            # GENERATE PDF
            # ------------------------------------------------

            pdf_filename = (
                f"{result['filename']}_Report.pdf"
            )


            try:

                analyzer.generate_pdf_report(
                    result,
                    pdf_filename
                )


                with open(
                    pdf_filename,
                    "rb"
                ) as pdf_file:

                    pdf_data = pdf_file.read()


                st.download_button(
                    label="📄 Download Candidate PDF Report",
                    data=pdf_data,
                    file_name=pdf_filename,
                    mime="application/pdf",
                    key="reports_pdf_download"
                )


            except Exception as error:

                st.error(
                    f"Unable to generate PDF report: {error}"
                )


        st.divider()


        # ====================================================
        # REPORT SUMMARY
        # ====================================================

        st.markdown(
            "### 📝 Recruitment Summary"
        )

        st.info(
            f"""
            **Candidates Evaluated:** {len(results)}

            **Top Candidate:** {top_candidate}

            **Highest ATS Score:** {highest_ats}%

            **Highest Resume Match:** {round(highest_match, 2)}%

            **Average Candidate Score:** {average_score}/100

            **Processing Time:** {processing_time} seconds
            """
        )

# ============================================================
# ANALYTICS PAGE
# ============================================================

elif page == "📈 Analytics":

    st.markdown("## 📈 Recruitment Analytics")

    st.caption(
        "Analyze candidate performance, hiring outcomes, "
        "skills, and recruitment trends."
    )

    # --------------------------------------------------------
    # CHECK DATA
    # --------------------------------------------------------

    if not results:

        st.info(
            "📊 No analytics available yet. "
            "Upload resumes and a Job Description first."
        )

    else:

        # ====================================================
        # KPI OVERVIEW
        # ====================================================

        st.markdown("### 📊 Recruitment Overview")

        analytics1, analytics2, analytics3, analytics4 = (
            st.columns(4)
        )

        average_ats = round(
            csv_df["ATS Score"].mean(),
            2
        )

        average_match = round(
            csv_df["Resume Match"].mean(),
            2
        )

        average_candidate_score = round(
            csv_df["Candidate Score"].mean(),
            2
        )

        with analytics1:

            st.metric(
                "👥 Candidates",
                len(results)
            )

        with analytics2:

            st.metric(
                "🛡️ Average ATS",
                f"{average_ats}%"
            )

        with analytics3:

            st.metric(
                "🎯 Average Match",
                f"{average_match}%"
            )

        with analytics4:

            st.metric(
                "⭐ Average Score",
                f"{average_candidate_score}/100"
            )


        st.divider()


        # ====================================================
        # SCORE COMPARISON
        # ====================================================

        st.markdown(
            "### 📊 Candidate Performance"
        )

        performance_df = csv_df[
            [
                "Candidate",
                "ATS Score",
                "Resume Match",
                "Candidate Score"
            ]
        ].copy()

        performance_df = performance_df.set_index(
            "Candidate"
        )

        st.bar_chart(
            performance_df[
                [
                    "ATS Score",
                    "Resume Match",
                    "Candidate Score"
                ]
            ]
        )


        st.divider()


        # ====================================================
        # TOP CANDIDATES
        # ====================================================

        st.markdown(
            "### 🏆 Top Candidates"
        )

        top_candidates_df = csv_df[
            [
                "Rank",
                "Candidate",
                "Role",
                "ATS Score",
                "Resume Match",
                "Candidate Score",
                "Recommendation"
            ]
        ].copy()

        top_candidates_df = (
            top_candidates_df
            .sort_values(
                "Candidate Score",
                ascending=False
            )
            .head(5)
        )

        st.dataframe(
            top_candidates_df,
            use_container_width=True,
            hide_index=True
        )


        st.divider()


        # ====================================================
        # ROLE DISTRIBUTION
        # ====================================================

        st.markdown(
            "### 💼 Recommended Role Distribution"
        )

        role_counts = csv_df[
            "Role"
        ].value_counts()

        if not role_counts.empty:

            role_chart_df = pd.DataFrame(
                {
                    "Candidates": role_counts
                }
            )

            st.bar_chart(
                role_chart_df
            )

        else:

            st.info(
                "No role information available."
            )


        st.divider()


        # ====================================================
        # HIRING RECOMMENDATIONS
        # ====================================================

        st.markdown(
            "### 🤖 Hiring Recommendations"
        )

        recommendation_counts = (
            csv_df[
                "Recommendation"
            ]
            .value_counts()
        )

        recommendation_df = pd.DataFrame(
            {
                "Candidates":
                    recommendation_counts
            }
        )

        st.bar_chart(
            recommendation_df
        )


        # ====================================================
        # RECOMMENDATION SUMMARY
        # ====================================================

        recommendation_col1, recommendation_col2 = (
            st.columns(2)
        )

        with recommendation_col1:

            recommended_count = 0

            for result in results:

                recommendation = (
                    result["recommendation"]
                    .lower()
                )

                if (
                    "recommended"
                    in recommendation
                    and
                    "not recommended"
                    not in recommendation
                ):

                    recommended_count += 1

            st.metric(
                "✅ Recommended Candidates",
                recommended_count
            )

        with recommendation_col2:

            not_recommended_count = 0

            for result in results:

                recommendation = (
                    result["recommendation"]
                    .lower()
                )

                if "not recommended" in recommendation:

                    not_recommended_count += 1

            st.metric(
                "❌ Not Recommended",
                not_recommended_count
            )


        st.divider()


        # ====================================================
        # SKILL ANALYTICS
        # ====================================================

        st.markdown(
            "### 🧠 Skill Analytics"
        )

        skill_frequency = {}

        for result in results:

            for skill in result["keywords"]:

                skill_name = skill.strip()

                if skill_name:

                    skill_frequency[skill_name] = (
                        skill_frequency.get(
                            skill_name,
                            0
                        ) + 1
                    )


        if skill_frequency:

            skill_df = pd.DataFrame(
                {
                    "Candidates": skill_frequency
                }
            )

            skill_df = skill_df.sort_values(
                "Candidates",
                ascending=False
            ).head(15)

            st.bar_chart(
                skill_df
            )

        else:

            st.info(
                "No skill data available."
            )


        st.divider()


        # ====================================================
        # SKILL GAP ANALYTICS
        # ====================================================

        st.markdown(
            "### ⚠️ Common Skill Gaps"
        )

        missing_frequency = {}

        for result in results:

            for skill in result[
                "missing_skills"
            ]:

                skill_name = skill.strip()

                if skill_name:

                    missing_frequency[skill_name] = (
                        missing_frequency.get(
                            skill_name,
                            0
                        ) + 1
                    )


        if missing_frequency:

            missing_df = pd.DataFrame(
                {
                    "Candidates Missing Skill":
                        missing_frequency
                }
            )

            missing_df = missing_df.sort_values(
                "Candidates Missing Skill",
                ascending=False
            ).head(15)

            st.bar_chart(
                missing_df
            )

        else:

            st.success(
                "No major skill gaps detected."
            )


        st.divider()


        # ====================================================
        # SCORE DISTRIBUTION
        # ====================================================

        st.markdown(
            "### 📈 Candidate Score Distribution"
        )

        score_distribution = csv_df[
            [
                "Candidate",
                "Candidate Score"
            ]
        ].copy()

        score_distribution = (
            score_distribution
            .set_index("Candidate")
        )

        st.line_chart(
            score_distribution
        )


        st.divider()


        # ====================================================
        # DETAILED ANALYTICS TABLE
        # ====================================================

        st.markdown(
            "### 📋 Detailed Analytics"
        )

        detailed_analytics = csv_df[
            [
                "Rank",
                "Candidate",
                "Role",
                "ATS Score",
                "Resume Match",
                "Candidate Score",
                "Recommendation"
            ]
        ].copy()

        st.dataframe(
            detailed_analytics,
            use_container_width=True,
            hide_index=True
        )


        # ====================================================
        # ANALYTICS SUMMARY
        # ====================================================

        st.divider()

        st.markdown(
            "### 📝 Analytics Summary"
        )

        best_match = csv_df.loc[
            csv_df["Resume Match"].idxmax()
        ]

        best_score = csv_df.loc[
            csv_df["Candidate Score"].idxmax()
        ]

        st.info(
            f"""
            👥 **Candidates Evaluated:** {len(results)}

            🏆 **Best Resume Match:** {best_match['Candidate']}
            ({round(best_match['Resume Match'], 2)}%)

            ⭐ **Highest Candidate Score:** {best_score['Candidate']}
            ({round(best_score['Candidate Score'], 2)}/100)

            🛡️ **Average ATS Score:** {average_ats}%

            🎯 **Average Resume Match:** {average_match}%

            🤖 **Average Candidate Score:** {average_candidate_score}/100
            """
        )

# ============================================================
# SETTINGS PAGE
# ============================================================

elif page == "⚙️ Settings":

    st.markdown("## ⚙️ Settings")

    st.caption(
        "Application configuration, analysis information, "
        "and system status."
    )


    # ========================================================
    # APPLICATION INFORMATION
    # ========================================================

    st.markdown("### 🤖 Application")

    with st.container(border=True):

        app_col1, app_col2 = st.columns(2)

        with app_col1:

            st.write(
                "**Application Name**"
            )

            st.write(
                "AI Recruitment Assistant"
            )

            st.write(
                "**Version**"
            )

            st.write(
                "1.0.0"
            )

        with app_col2:

            st.write(
                "**Purpose**"
            )

            st.write(
                "AI-powered resume screening, "
                "candidate ranking, skill analysis, "
                "and hiring recommendations."
            )

            st.write(
                "**Interface**"
            )

            st.write(
                "Streamlit"
            )


    # ========================================================
    # SUPPORTED FILES
    # ========================================================

    st.markdown("### 📄 Supported Files")

    file_col1, file_col2 = st.columns(2)

    with file_col1:

        with st.container(border=True):

            st.markdown(
                "#### 📑 Resume"
            )

            st.success(
                "PDF supported"
            )

            st.write(
                "Multiple resumes can be uploaded "
                "and evaluated in a single analysis."
            )

    with file_col2:

        with st.container(border=True):

            st.markdown(
                "#### 💼 Job Description"
            )

            st.success(
                "PDF supported"
            )

            st.write(
                "One Job Description is used as the "
                "reference for candidate evaluation."
            )


    # ========================================================
    # ANALYSIS MODULES
    # ========================================================

    st.markdown(
        "### 🧠 Analysis Modules"
    )

    modules = [
        "Resume Text Extraction",
        "Skill Detection",
        "Contact Information Extraction",
        "Experience Extraction",
        "Education Extraction",
        "Project Extraction",
        "Certification Extraction",
        "Soft Skill Detection",
        "ATS Scoring",
        "Resume-to-Job Matching",
        "Candidate Ranking",
        "Strength Analysis",
        "Weakness Analysis",
        "AI Suggestions",
        "Candidate Summary",
        "Hiring Recommendation",
        "PDF Report Generation",
        "CSV Report Generation"
    ]

    module_columns = st.columns(3)

    for index, module in enumerate(modules):

        with module_columns[
            index % 3
        ]:

            st.success(
                f"✓ {module}"
            )


    # ========================================================
    # SCORING CONFIGURATION
    # ========================================================

    st.markdown(
        "### ⚖️ Scoring Configuration"
    )

    with st.container(border=True):

        st.write(
            "**ATS Score**"
        )

        st.write(
            "Measures the candidate's detected skills "
            "against the required Job Description skills."
        )

        st.write(
            "**Resume Match**"
        )

        st.write(
            "Measures the overall similarity between "
            "the resume and Job Description."
        )

        st.write(
            "**Candidate Score**"
        )

        st.write(
            "Combines resume matching and ATS performance "
            "to produce the overall candidate score."
        )


    # ========================================================
    # CURRENT SYSTEM STATUS
    # ========================================================

    st.markdown(
        "### 📊 Current System Status"
    )

    status1, status2, status3, status4 = st.columns(4)

    with status1:

        if uploaded_files:

            st.success(
                f"📄 {len(uploaded_files)} Resume(s) Loaded"
            )

        else:

            st.info(
                "📄 No Resumes Loaded"
            )

    with status2:

        if job_file:

            st.success(
                "💼 Job Description Loaded"
            )

        else:

            st.info(
                "💼 No Job Description"
            )

    with status3:

        if results:

            st.success(
                f"👥 {len(results)} Candidates Analyzed"
            )

        else:

            st.info(
                "👥 No Candidates Analyzed"
            )

    with status4:

        if results:

            st.success(
                "🟢 Analysis Ready"
            )

        else:

            st.info(
                "🟡 Waiting for Analysis"
            )


    # ========================================================
    # ANALYSIS RESET
    # ========================================================

    st.markdown(
        "### 🔄 Analysis"
    )

    with st.container(border=True):

        st.write(
            "To start a new recruitment analysis, "
            "upload a new set of resumes and Job Description."
        )

        st.warning(
            "Refreshing the application will clear "
            "the current uploaded analysis."
        )

        if st.button(
            "🔄 Refresh Application",
            use_container_width=True
        ):

            st.rerun()


    # ========================================================
    # ABOUT
    # ========================================================

    st.markdown(
        "### ℹ️ About"
    )

    st.info(
        """
        **AI Recruitment Assistant**

        An AI-powered recruitment platform designed to
        automate resume extraction, candidate evaluation,
        ranking, skill analysis, and hiring recommendations.

        The system processes multiple resumes against a
        Job Description and provides structured recruitment
        insights for each candidate.
        """
    )


    # ========================================================
    # FOOTER
    # ========================================================

    st.divider()

    st.caption(
        "AI Recruitment Assistant • Version 1.0.0"
    )