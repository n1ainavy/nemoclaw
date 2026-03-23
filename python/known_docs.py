"""
Known document databases for all 15 Navy / DoD policy sources.

Each entry is a 3-tuple: (document_number, title, date_released)
  date_released: "Month YYYY" or "DD Mon YYYY" or "" if unknown.
  Dates reflect the most recent version/revision of each document.
"""

# ============================================================
# 01 - RESPERSMAN
# Articles are identified by chapter-article number.
# ============================================================
RESPERSMAN_ARTICLES = [
    # Chapter 1000 - Administrative
    ("1000-010", "Establishment and Authority",                  "01 Oct 2005"),
    ("1000-020", "Definition of Terms",                         "01 Oct 2005"),
    ("1000-030", "Policy",                                      "01 Oct 2005"),
    ("1001-010", "Administrative Procedures",                    "15 Mar 2010"),
    ("1001-020", "Records Management",                          "15 Mar 2010"),
    # Chapter 1050 - Leave
    ("1050-010", "Leave Policy",                                "01 Nov 2014"),
    ("1050-020", "Leave Categories",                            "01 Nov 2014"),
    ("1050-030", "Leave Accounting",                            "01 Nov 2014"),
    # Chapter 1070 - Service Records
    ("1070-010", "Service Record Entries",                      "15 Sep 2018"),
    ("1070-020", "Official Military Personnel File",            "15 Sep 2018"),
    # Chapter 1120 - Enlisted Procurement
    ("1120-010", "Enlisted Accession Programs",                 "01 Jun 2016"),
    ("1120-020", "Procurement Standards",                       "01 Jun 2016"),
    ("1120-100", "Delayed Entry Program",                       "01 Jun 2016"),
    # Chapter 1130 - Enlisted Recruiting
    ("1130-010", "Recruiting Programs",                         "15 Feb 2015"),
    ("1130-020", "Recruiting Standards",                        "15 Feb 2015"),
    # Chapter 1160 - Retention
    ("1160-010", "Selective Reenlistment Bonus (SRB)",         "01 Oct 2022"),
    ("1160-020", "Reenlistment Procedures",                     "01 Oct 2020"),
    ("1160-030", "Enlisted Retention Control Program",          "15 Jan 2019"),
    ("1160-040", "Perform to Serve (PTS)",                      "01 Mar 2021"),
    # Chapter 1220 - Officer Procurement
    ("1220-010", "Officer Accession Programs",                  "15 Jul 2017"),
    ("1220-020", "Direct Appointment Procedures",               "15 Jul 2017"),
    # Chapter 1301 - Distribution
    ("1301-010", "Enlisted Distribution Policy",               "01 Sep 2019"),
    ("1301-020", "Assignment Procedures",                       "01 Sep 2019"),
    # Chapter 1306 - Special Programs
    ("1306-010", "Special Assignment Programs",                 "01 Aug 2018"),
    ("1306-100", "Navy Reserve Canvasser Recruiter Program",   "01 Aug 2018"),
    # Chapter 1320 - PCS
    ("1320-010", "PCS Orders Policy",                          "15 Apr 2021"),
    ("1320-020", "PCS Entitlements",                           "15 Apr 2021"),
    # Chapter 1420 - Advancement
    ("1420-010", "Advancement Policy",                         "01 Oct 2023"),
    ("1420-020", "Advancement Eligibility",                    "01 Oct 2023"),
    # Chapter 1430 - Advancement Procedures
    ("1430-010", "Advancement in Rate",                        "01 Oct 2023"),
    # Chapter 1440 - Special Duty
    ("1440-010", "Special Duty Assignment Pay",               "15 Jun 2020"),
    # Chapter 1500 - Training
    ("1500-010", "Training Policy",                            "01 Nov 2016"),
    ("1500-020", "AT/ADT Orders",                              "01 Nov 2016"),
    ("1500-030", "School Orders",                              "01 Nov 2016"),
    # Chapter 1610 - Performance Evaluation
    ("1610-010", "FITREP/Evaluation Policy",                   "01 Mar 2022"),
    ("1610-020", "Evaluation Procedures",                      "01 Mar 2022"),
    # Chapter 1640 - Discipline
    ("1640-010", "Discipline Procedures",                      "15 Aug 2017"),
    ("1640-020", "Non-Judicial Punishment",                    "15 Aug 2017"),
    # Chapter 1770 - Awards
    ("1770-010", "Awards Policy",                              "01 Jul 2020"),
    ("1770-020", "Award Procedures",                           "01 Jul 2020"),
    # Chapter 1820 - Retirement
    ("1820-010", "Reserve Retirement",                         "15 Jan 2021"),
    ("1820-020", "Transfer to Retired Reserve",               "15 Jan 2021"),
    # Chapter 1900 - Separation
    ("1900-010", "Separation Policy",                          "01 Sep 2019"),
    ("1900-020", "Administrative Separation",                  "01 Sep 2019"),
    ("1910-010", "Administrative Separation Procedures",       "01 Sep 2019"),
]

# ============================================================
# 02 - MILPERSMAN
# ============================================================
MILPERSMAN_ARTICLES = [
    # Chapter 1000 - General
    ("1000-010", "Applicability",                                       "15 Mar 2005"),
    ("1000-020", "Definitions",                                         "15 Mar 2005"),
    ("1000-030", "Waivers",                                             "15 Mar 2005"),
    # Chapter 1020 - Equal Opportunity
    ("1020-010", "Equal Opportunity Policy",                            "22 Aug 2019"),
    ("1020-020", "Sexual Harassment Prevention",                        "22 Aug 2019"),
    # Chapter 1050 - Leave
    ("1050-010", "Leave Policy",                                        "01 Nov 2020"),
    ("1050-020", "Leave Categories",                                    "01 Nov 2020"),
    ("1050-030", "Leave Procedures",                                    "01 Nov 2020"),
    ("1050-040", "Emergency Leave",                                     "01 Nov 2020"),
    ("1050-050", "Leave and Earnings Statement",                        "01 Nov 2020"),
    # Chapter 1070 - Records
    ("1070-010", "Official Military Personnel File",                    "15 Sep 2021"),
    ("1070-020", "Service Record Management",                           "15 Sep 2021"),
    ("1070-040", "Certificate of Release or Discharge (DD-214)",        "15 Sep 2021"),
    # Chapter 1080 - Physical Readiness
    ("1080-010", "Physical Fitness Standards",                          "01 Jan 2023"),
    # Chapter 1120 - Enlisted Procurement
    ("1120-010", "Enlisted Procurement Programs",                       "15 May 2018"),
    ("1120-020", "Officer Programs from Enlisted",                      "15 May 2018"),
    ("1120-100", "Enlistment Standards",                               "15 May 2018"),
    # Chapter 1130 - Recruiting
    ("1130-010", "Recruiting Policy",                                   "01 Aug 2017"),
    # Chapter 1160 - Retention
    ("1160-010", "Selective Reenlistment Bonus",                        "01 Oct 2023"),
    ("1160-030", "Career Reenlistment Objectives (CREO)",               "01 Oct 2022"),
    ("1160-040", "Perform to Serve (PTS)",                              "01 Jul 2022"),
    # Chapter 1220 - Officer Procurement
    ("1220-010", "Officer Procurement Programs",                        "15 Jun 2019"),
    ("1220-020", "Limited Duty Officer (LDO) Program",                  "15 Jun 2019"),
    ("1220-030", "Chief Warrant Officer (CWO) Program",                 "15 Jun 2019"),
    ("1220-040", "Meritorious Commissioning Program (MCP)",             "15 Jun 2019"),
    # Chapter 1301 - Distribution
    ("1301-010", "Enlisted Distribution Policy",                        "01 Sep 2020"),
    # Chapter 1306 - Special Programs
    ("1306-010", "Special Assignment Programs",                         "01 Mar 2021"),
    ("1306-100", "Nuclear Power Program",                               "01 Mar 2021"),
    ("1306-200", "SEAL/SWCC Programs",                                  "15 Nov 2020"),
    # Chapter 1320 - PCS
    ("1320-010", "Permanent Change of Station Orders",                  "15 Apr 2022"),
    ("1320-020", "PCS Entitlements and Procedures",                     "15 Apr 2022"),
    ("1320-040", "Overseas Tours",                                      "15 Apr 2022"),
    ("1320-050", "OCONUS Duty",                                         "15 Apr 2022"),
    # Chapter 1326 - Sea Duty
    ("1326-010", "Sea Duty Obligation",                                 "15 Oct 2021"),
    ("1326-020", "Sea/Shore Rotation",                                  "15 Oct 2021"),
    # Chapter 1350 - Training
    ("1350-010", "Voluntary Education Programs",                        "01 Sep 2020"),
    ("1350-020", "College Degree Programs",                             "01 Sep 2020"),
    # Chapter 1410 - Selection Boards
    ("1410-010", "Selection Board Process",                             "01 Jan 2022"),
    ("1410-020", "Continuation Boards",                                 "01 Jan 2022"),
    # Chapter 1420 - Advancement
    ("1420-010", "Advancement Policy",                                  "01 Oct 2023"),
    ("1420-020", "Advancement in Rate",                                 "01 Oct 2023"),
    ("1420-030", "Advancement Eligibility Requirements",                "01 Oct 2023"),
    # Chapter 1430 - Advancement Procedures
    ("1430-010", "Advancement Examination Procedures",                  "01 Oct 2023"),
    ("1430-020", "Final Multiple Score (FMS)",                          "01 Oct 2023"),
    # Chapter 1440 - Officer Assignments
    ("1440-010", "Officer Special Assignment",                          "15 Jun 2021"),
    # Chapter 1480 - EFMP
    ("1480-010", "Exceptional Family Member Program (EFMP)",            "01 May 2022"),
    # Chapter 1500 - Navy Training
    ("1500-010", "General Training Policy",                             "01 Nov 2019"),
    ("1500-020", "AT/ADT Training Orders",                              "01 Nov 2019"),
    ("1500-030", "A/C School Orders",                                   "01 Nov 2019"),
    # Chapter 1510 - Education
    ("1510-010", "Voluntary Education",                                 "15 Sep 2021"),
    ("1510-020", "Navy College Program",                                "15 Sep 2021"),
    ("1510-030", "Tuition Assistance",                                  "15 Sep 2021"),
    # Chapter 1560 - War College
    ("1560-010", "Naval War College",                                   "01 Aug 2018"),
    # Chapter 1600 - Legal
    ("1600-010", "Military Justice Overview",                           "01 Jan 2020"),
    ("1600-020", "Non-Judicial Punishment (NJP)",                       "01 Jan 2020"),
    ("1600-030", "Courts-Martial",                                      "01 Jan 2020"),
    # Chapter 1610 - Performance
    ("1610-010", "Enlisted Performance Evaluation",                     "01 Mar 2022"),
    ("1610-020", "Officer Fitness Reports",                             "01 Mar 2022"),
    # Chapter 1640 - Discipline
    ("1640-010", "Conduct and Discipline",                              "15 Aug 2021"),
    ("1640-020", "Administrative Separations – Misconduct",             "15 Aug 2021"),
    # Chapter 1700 - Welfare
    ("1700-010", "Family Support Programs",                             "01 Jul 2019"),
    ("1700-020", "Fleet and Family Support Centers (FFSC)",             "01 Jul 2019"),
    # Chapter 1710 - Chaplains
    ("1710-010", "Religious Programs",                                  "15 Mar 2018"),
    # Chapter 1730 - Financial Readiness
    ("1730-010", "Personal Financial Management",                       "01 Oct 2020"),
    # Chapter 1740 - Social Actions
    ("1740-010", "Social Actions Program",                              "15 May 2017"),
    # Chapter 1750 - Counseling
    ("1750-010", "Counseling Programs",                                 "01 Sep 2018"),
    # Chapter 1760 - Dependents
    ("1760-010", "Dependent Care",                                      "15 Apr 2021"),
    ("1760-020", "Family Care Plans",                                   "15 Apr 2021"),
    # Chapter 1770 - Awards
    ("1770-010", "Military Awards Policy",                              "01 Jul 2022"),
    ("1770-020", "Unit Awards",                                         "01 Jul 2022"),
    ("1770-030", "Civilian Awards",                                     "01 Jul 2022"),
    # Chapter 1780 - Family Readiness
    ("1780-010", "Family Readiness Programs",                           "15 Feb 2022"),
    # Chapter 1810 - Fleet Reserve
    ("1810-010", "Fleet Reserve",                                       "01 Jan 2021"),
    # Chapter 1820 - Retirement
    ("1820-010", "Active Duty Retirement",                              "15 Nov 2022"),
    ("1820-020", "Reserve Retirement",                                  "15 Nov 2022"),
    ("1820-030", "Disability Retirement",                               "15 Nov 2022"),
    # Chapter 1850 - Disability
    ("1850-010", "Disability Evaluation System",                        "01 May 2023"),
    ("1850-020", "Disability Determinations",                           "01 May 2023"),
    # Chapter 1900 - Separation
    ("1900-010", "Separation General Policy",                           "01 Sep 2022"),
    ("1900-020", "Administrative Separations",                          "01 Sep 2022"),
    ("1910-010", "Enlisted Separation Procedures",                      "01 Sep 2022"),
    ("1910-020", "Officer Separation Procedures",                       "01 Sep 2022"),
    ("1920-010", "Separation Processing",                               "01 Sep 2022"),
]

# ============================================================
# 03 - SECNAV INSTRUCTIONS & MANUALS
# ============================================================
SECNAVINST_DOCS = [
    # 1000s - Military Personnel
    ("1000.9D",   "Navy Overseas Duty Support Program",                         "08 Oct 2002"),
    ("1001.24A",  "Assignment of Navy and Marine Corps Officers",                "26 Aug 2008"),
    ("1020.8H",   "Navy Uniform Regulations",                                   "16 Feb 2023"),
    ("1050.3A",   "Counting of Time Lost to Military Service",                  "22 Nov 2004"),
    ("1070.27D",  "Individual Service Records",                                 "13 Mar 2020"),
    ("1080.1C",   "Navy Physical Readiness Program",                            "01 Jan 2023"),
    ("1120.10A",  "Enlisted Community Management",                              "17 Nov 2010"),
    ("1160.5D",   "Selective Reenlistment Bonus (SRB)",                         "14 Dec 2020"),
    ("1160.8",    "Enlisted Retention Program",                                 "02 Mar 2007"),
    ("1214.4",    "Command Senior Enlisted Leaders",                            "19 Dec 2019"),
    ("1220.3",    "Officer Temporary Duty for Education",                       "26 Sep 2003"),
    ("1220.7",    "Limited Duty Officer and Chief Warrant Officer Programs",     "20 Jun 2012"),
    ("1301.1A",   "Military Personnel Manual Update Procedures",                "09 Feb 2010"),
    ("1306.2E",   "Navy Enlisted Distribution",                                 "28 Jan 2013"),
    ("1320.5E",   "Permanent Change of Station Travel",                         "07 Jul 2020"),
    ("1410.1B",   "Officer Promotions",                                         "10 Dec 2019"),
    ("1420.1B",   "Advancement Manual for Enlisted Servicepeople",              "21 Aug 2009"),
    ("1430.16G",  "Advancement Manual for Enlisted Personnel",                  "19 Nov 2018"),
    ("1440.1E",   "Officer Special Assignment",                                 "24 Jul 2013"),
    ("1480.10B",  "Navy Exceptional Family Member Program (EFMP)",               "15 May 2020"),
    ("1500.22G",  "Voluntary Education Programs",                               "16 Nov 2016"),
    ("1510.32B",  "Navy College Program",                                       "28 Feb 2018"),
    ("1560.9",    "Interservice Training Review Organization (ITRO)",           "08 Dec 2005"),
    ("1610.7A",   "Performance Evaluation System",                              "30 Nov 2020"),
    ("1640.9A",   "Navy Drug and Alcohol Prevention Program",                   "28 Sep 2020"),
    ("1650.1J",   "Navy and Marine Corps Awards Manual",                        "25 Aug 2019"),
    ("1740.3D",   "Personal Financial Management Education",                    "19 Apr 2021"),
    ("1760.3A",   "Dependent Care Program",                                     "17 Dec 2018"),
    ("1770.3D",   "Casualty Assistance Program",                                "15 Jun 2020"),
    ("1780.1B",   "Navy Family Ombudsman Program",                              "17 Oct 2019"),
    ("1820.3",    "Continuation on Active Duty",                                "10 Aug 2012"),
    ("1850.4E",   "Disability Evaluation System",                               "08 Jun 2020"),
    ("1900.9A",   "Enlisted Separation Manual",                                 "22 Aug 2022"),
    # 3000s - Operations
    ("3060.1",    "Department of Defense Priority Reserve Component Program",    "21 Dec 2007"),
    ("3120.32E",  "Standard Organization and Regulations of the U.S. Navy",     "05 Nov 2019"),
    ("3306.1A",   "Department of the Navy Continuity of Operations",            "01 Apr 2020"),
    # 4000s - Logistics
    ("4001.3D",   "Assignment of Responsibilities for Acquisition",             "13 Jun 2018"),
    # 5000s - Administration
    ("5000.2F",   "Defense Acquisition Management Policies and Procedures",     "01 Apr 2022"),
    ("5030.8B",   "SECNAV Instruction for Navy/Marine Corps Public Affairs",    "01 Sep 2020"),
    ("5040.3B",   "Inspector General",                                          "19 Nov 2019"),
    ("5090.6A",   "Department of the Navy Environmental",                       "22 Sep 2020"),
    ("5100.13F",  "Navy Safety Program",                                        "04 Dec 2020"),
    ("5200.35E",  "Communications Security Material",                           "24 Mar 2009"),
    ("5200.39A",  "Critical Program Information Protection",                    "16 Nov 2016"),
    ("5210.8D",   "Department of the Navy Records Management",                  "31 Jan 2012"),
    ("5211.5F",   "Privacy Act Program",                                        "07 Jan 2021"),
    ("5239.3C",   "DON Cybersecurity Policy",                                   "17 Oct 2022"),
    ("5300.26E",  "DON Drug and Alcohol Abuse Prevention and Control",          "27 Nov 2017"),
    ("5350.3A",   "Establishment of the DON Ethics Program",                    "06 May 2014"),
    ("5370.7E",   "Conflicts of Interest",                                      "28 Sep 2020"),
    ("5400.15C",  "Responsibilities for Acquisition",                           "23 Jan 2019"),
    ("5450.338C", "Office of Naval Intelligence",                               "17 Apr 2019"),
    ("5510.30B",  "DON Personnel Security Program",                             "10 Mar 2020"),
    ("5510.36B",  "DON Information Security Program",                           "20 Jul 2022"),
    ("5520.3B",   "Law Enforcement Manual",                                     "21 Jun 2018"),
    ("5600.20D",  "Department of the Navy Correspondence Manual",               "05 Jun 2019"),
    ("5720.44C",  "DON Public Affairs Policy and Regulations",                  "01 Sep 2020"),
    # 7000s - Finance
    ("7000.26F",  "Financial Accounting Policy for Organizations",              "28 Sep 2020"),
    ("7220.7J",   "Foreign Gifts and Decorations Received",                     "30 Oct 2019"),
    ("7300.9F",   "Navy Comptroller Manual",                                    "15 Apr 2014"),
    # SECNAV MANUALS
    ("M-1650.1",  "Navy and Marine Corps Awards Manual",                        "25 Aug 2019"),
    ("M-5000.2",  "Defense Acquisition Guidebook",                              "01 Apr 2022"),
    ("M-5210.1",  "DON Records and Information Management",                     "17 Nov 2021"),
    ("M-5510.30", "DON Personnel Security Program",                             "10 Mar 2020"),
    ("M-5510.36", "DON Information Security Program",                           "20 Jul 2022"),
    ("M-5800.16", "LEGADMINMAN – Legal Administration Manual",                  "16 Dec 2020"),
]

# ============================================================
# 04 - BUPERS INSTRUCTIONS
# ============================================================
BUPERSINST_DOCS = [
    ("1000.3",    "Administration of Statutory Tour Lengths",               "12 Sep 2016"),
    ("1001.39F",  "Active Duty for Operational Support (ADOS)",             "22 Oct 2020"),
    ("1080.1D",   "Physical Readiness Program Administration",              "01 Jan 2023"),
    ("1120.6F",   "Enlisted Recruiting Standards",                          "15 Mar 2021"),
    ("1131.2D",   "Civilian Human Resources Manual",                        "30 Aug 2018"),
    ("1160.7",    "Enlisted Continuation Program",                          "12 Nov 2019"),
    ("1160.8",    "Enlisted Retention Programs",                            "12 Nov 2019"),
    ("1220.5E",   "Direct Appointment Programs",                            "01 Jul 2020"),
    ("1220.7",    "LDO/CWO Selection Boards",                               "01 Jul 2020"),
    ("1250.1F",   "Naval Reserve Officers' Training Corps (NROTC)",         "15 Aug 2019"),
    ("1326.3E",   "Sea/Shore Duty Rotation",                                "18 Jun 2021"),
    ("1350.2B",   "Voluntary Education Programs",                           "15 Sep 2021"),
    ("1370.1C",   "Voluntary Education",                                    "15 Sep 2021"),
    ("1420.1C",   "Advancement Manual",                                     "01 Oct 2023"),
    ("1430.16G",  "Advancement Manual for Enlisted Personnel",              "19 Nov 2018"),
    ("1440.5",    "Special Assignment Procedures",                          "20 Jan 2020"),
    ("1500.22F",  "Navy Education and Training Programs",                   "10 May 2019"),
    ("1610.10E",  "Performance Evaluation System",                          "30 Nov 2020"),
    ("1640.21D",  "Alcohol Abuse and Drug Control Policy",                  "14 Oct 2019"),
    ("1640.22A",  "Navy Drug Demand Reduction Program",                     "14 Oct 2019"),
    ("1700.22",   "Family Support Programs",                                "19 Jul 2018"),
    ("1710.11D",  "Chaplain Corps Professional Development",                "12 Mar 2020"),
    ("1770.2A",   "Death Gratuity",                                         "08 Feb 2018"),
    ("1780.2D",   "Family Readiness Programs",                              "15 Jun 2021"),
    ("1820.1",    "Retirement Eligibility",                                 "09 Jan 2019"),
    ("1900.8E",   "Discharge Authority",                                    "23 Sep 2020"),
    ("7220.6",    "Gifts to Senior Officials",                              "03 May 2017"),
]

# ============================================================
# 05 - JTR (Joint Travel Regulations)
# ============================================================
JTR_DOCS = [
    ("JTR-Full",      "Joint Travel Regulations (Complete Document)",           "01 Jan 2024"),
    ("JTR-Ch01",      "Chapter 1 – General Rules and Regulations",              "01 Jan 2024"),
    ("JTR-Ch02",      "Chapter 2 – Temporary Duty (TDY) Travel",               "01 Jan 2024"),
    ("JTR-Ch03",      "Chapter 3 – Permanent Duty Travel (PCS)",                "01 Jan 2024"),
    ("JTR-Ch04",      "Chapter 4 – Transportation",                             "01 Jan 2024"),
    ("JTR-Ch05",      "Chapter 5 – Per Diem Allowances",                        "01 Jan 2024"),
    ("JTR-Ch06",      "Chapter 6 – Mileage Allowances",                         "01 Jan 2024"),
    ("JTR-Appendix-A","Appendix A – Definitions",                               "01 Jan 2024"),
    ("JTR-Appendix-B","Appendix B – CONUS Per Diem Rates",                      "01 Jan 2024"),
    ("JTR-Appendix-C","Appendix C – OCONUS Per Diem Rates",                     "01 Jan 2024"),
]

# ============================================================
# 06 - DoD DIRECTIVES (DoDD)
# ============================================================
DODD_DOCS = [
    ("1000.01E",  "DoD Civilian Human Resources Management",                    "23 Apr 2008"),
    ("1020.1",    "Nondiscrimination on the Basis of Handicap",                 "14 Oct 2020"),
    ("1030.01",   "Victim and Witness Assistance",                              "23 Apr 2004"),
    ("1035.01",   "Telework Policy",                                            "04 Apr 2007"),
    ("1145.01",   "Reserve Component Members",                                  "13 Jan 2021"),
    ("1200.7",    "Screening the Ready Reserve",                                "06 Nov 2008"),
    ("1215.06",   "Uniform Reserve Training and Retirement Categories",         "07 Nov 2011"),
    ("1235.10",   "Activation, Mobilization, and Demobilization",               "22 Jul 2014"),
    ("1250.1",    "National Guard Participation",                               "07 May 2019"),
    ("1304.19",   "Enlistment Bonuses",                                         "29 Jan 2014"),
    ("1322.18",   "Military Training",                                          "13 Jan 2009"),
    ("1342.13",   "Eligibility Requirements for Trial of Persons",              "12 Nov 2020"),
    ("1400.5",    "DoD Policy for Non-US Nationals",                            "10 May 2019"),
    ("1404.10",   "Emergency Essential Civilian Employees",                     "10 Apr 1992"),
    ("1440.1",    "DoD Civilian Equal Employment Opportunity",                  "21 Apr 2004"),
    ("1442.02",   "Personnel Actions for DoD Non-Appropriated Funds",           "19 Oct 2007"),
    ("2000.09",   "Interaction with Nongovernmental Organizations",             "27 Jul 2009"),
    ("2310.01E",  "DoD Detainee Program",                                       "19 Aug 2014"),
    ("3000.03E",  "DoD Executive Agent",                                        "22 Sep 2020"),
    ("3000.06",   "Combat Support Agencies",                                    "07 Aug 2019"),
    ("3020.40",   "Mission Assurance",                                          "01 Nov 2019"),
    ("3025.18",   "Defense Support of Civil Authorities",                       "29 Dec 2010"),
    ("3100.10",   "Space Policy",                                               "18 Oct 2012"),
    ("3115.09",   "DoD Intelligence Interrogations",                            "09 Oct 2008"),
    ("3150.09",   "The Chemical Weapons Convention",                            "05 Aug 2009"),
    ("4000.01",   "Management of Energy Commodities",                           "04 Sep 2013"),
    ("4630.05",   "Interoperability and Supportability",                        "05 May 2004"),
    ("5000.01",   "The Defense Acquisition System",                             "09 Sep 2020"),
    ("5010.42",   "DoD-Wide Continuous Process Improvement",                    "15 May 2008"),
    ("5100.01F",  "Functions of the Department of Defense",                     "21 Dec 2010"),
    ("5100.73",   "Major DoD Headquarters Activities",                          "05 Oct 2007"),
    ("5105.41",   "Defense Finance and Accounting Service (DFAS)",              "14 Nov 2019"),
    ("5105.83",   "Defense Human Resources Activity (DHRA)",                    "25 Jan 2019"),
    ("5120.08",   "DoD Civilians Injured or Ill During Military Operations",    "15 Jun 2011"),
    ("5200.01",   "DoD Information Security Program",                           "21 Apr 2020"),
    ("5205.07",   "Special Access Program Policy",                              "01 Jul 2010"),
    ("5210.2",    "Access to and Dissemination of Restricted Data",             "12 Jan 2018"),
    ("5210.41M",  "Nuclear Weapon Security Program",                            "13 Jul 2009"),
    ("5230.11",   "Disclosure of Classified Military Information",              "16 Jun 1992"),
    ("5400.07",   "DoD Freedom of Information Act Program",                     "02 Jan 2008"),
    ("5400.11",   "DoD Privacy Program",                                        "29 Oct 2014"),
    ("5500.07",   "Standards of Conduct",                                       "29 Nov 2007"),
    ("5525.5",    "DoD Cooperation with Civilian Law Enforcement",              "15 Jan 1986"),
    ("6025.13",   "Medical Quality Assurance",                                  "17 Feb 2011"),
    ("6200.04",   "Force Health Protection",                                    "09 Oct 2004"),
    ("7045.14",   "The Planning, Programming, Budgeting and Execution Process", "25 Jan 2013"),
    ("7730.65",   "DoD Readiness Reporting System",                             "11 Jun 2004"),
    ("8190.01F",  "Mobile Code",                                                "21 Jan 2022"),
    ("8500.01",   "Cybersecurity",                                              "14 Mar 2014"),
]

# ============================================================
# 07 - DoD INSTRUCTIONS (DoDI)
# ============================================================
DODI_DOCS = [
    ("1000.01",   "Personnel Records",                                          "22 Sep 2021"),
    ("1000.13",   "Identification (ID) Cards for Members of the Uniformed Services", "05 Jan 2021"),
    ("1000.29",   "DoD Civil Liberties Program",                                "17 May 2012"),
    ("1005.19",   "National Security Personnel System",                         "16 Nov 2010"),
    ("1010.04",   "Problematic Substance Use by DoD Personnel",                 "20 Feb 2020"),
    ("1010.10",   "Health Promotion and Disease/Injury Prevention",             "22 Sep 2021"),
    ("1020.03",   "Harassment Prevention and Response",                         "08 Feb 2021"),
    ("1025.7",    "Reserve Component Program",                                  "07 Jul 2020"),
    ("1035.01",   "Telework Policy",                                            "04 Apr 2012"),
    ("1100.22",   "Policy and Procedures for Determining Workforce Mix",        "01 Sep 2020"),
    ("1215.07",   "Service Credit for Non-Regular Retirement",                  "12 Apr 2005"),
    ("1220.06",   "Performance Management and Appraisal Program",               "26 Aug 2021"),
    ("1235.12",   "Accessing the Reserve Components",                           "26 Apr 2019"),
    ("1241.01",   "Reserve Component (RC) Line of Duty Determination",          "07 Apr 2017"),
    ("1300.04",   "Inter-Service Transfer of Commissioned Officers",            "27 Nov 2019"),
    ("1300.18",   "DoD Personnel Casualty Matters, Policies, and Procedures",   "08 Jan 2008"),
    ("1304.26",   "Qualification Standards for Enlistment, Appointment",        "13 Oct 2020"),
    ("1308.03",   "National Call to Service Program",                           "10 Apr 2006"),
    ("1315.09",   "Utilization of Enlisted Aides on Official Duty",             "18 Jan 2017"),
    ("1320.02",   "Commissioned Officers – Promotion",                          "02 Jan 2019"),
    ("1320.04",   "Military Officer Actions Requiring Presidential Approval",   "04 Jan 2010"),
    ("1322.10",   "Education Development",                                      "29 Apr 2008"),
    ("1322.24",   "Medical Readiness of Service Members",                       "02 Jan 2019"),
    ("1332.14",   "Enlisted Administrative Separations",                        "27 Aug 2014"),
    ("1332.30",   "Separation of Regular and Reserve Commissioned Officers",    "11 Dec 2008"),
    ("1333.05",   "Recall to Active Duty of Retired Officers",                  "11 Mar 1997"),
    ("1336.05",   "Retention of Soldiers and Sailors on Active Duty",           "09 May 2005"),
    ("1400.25",   "DoD Civilian Personnel Management System",                   "20 Nov 2015"),
    ("1404.12",   "Employment of Spouses of Active Duty Military",              "06 Nov 2019"),
    ("1435.01",   "Civilian Employees in Overseas Areas",                       "09 Oct 2020"),
    ("1438.01",   "Reduction in Force",                                         "20 Mar 2009"),
    ("1440.02",   "DoD Mentoring Program",                                      "15 Mar 2019"),
    ("1480.04",   "EFMP for DoD Family Members",                                "06 Apr 2020"),
    ("1500.20",   "Resale Activities – Standard of Conduct",                    "01 Sep 2015"),
    ("1510.08",   "Educational Assistance for Members of National Guard",        "14 Apr 2020"),
    ("1560.02",   "Reserve Component Senior Enlisted Advisor",                  "14 Mar 2007"),
    ("1612.01",   "Performance Management and Appraisal",                       "08 Jan 2021"),
    ("5000.02T",  "Operation of the Adaptive Acquisition Framework",            "23 Jan 2020"),
    ("5000.74",   "Defense Acquisition of Services",                            "05 Jan 2016"),
    ("5000.76",   "Trusted Systems and Networks (TSN)",                         "06 May 2014"),
    ("5010.43",   "Continuous Improvement (CI) Program",                        "25 May 2010"),
    ("6025.17",   "Military Health System",                                     "16 Jan 2009"),
    ("6025.19",   "Individual Medical Readiness",                               "09 Jun 2014"),
    ("6055.1",    "DoD Safety and Occupational Health Program",                 "19 Oct 2020"),
    ("8500.01",   "Cybersecurity",                                              "14 Mar 2014"),
    ("8510.01",   "Risk Management Framework (RMF) for DoD Systems",           "12 Mar 2014"),
    ("8582.01",   "National Information Assurance Partnership",                 "23 May 2006"),
]

# ============================================================
# 08 - DoD MANUALS (DoDM)
# ============================================================
DODM_DOCS = [
    ("1000.04",    "DoD Manpower Data Center",                                  "19 Mar 2019"),
    ("1000.13-V1", "DoD ID Cards – Volume 1: Overview",                         "07 Jan 2020"),
    ("1000.13-V2", "DoD ID Cards – Volume 2: Benefits for Surviving Dependents","07 Jan 2020"),
    ("1000.13-V3", "DoD ID Cards – Volume 3: Trusted Associate Sponsorship System","07 Jan 2020"),
    ("1005.01",    "DoD Identification Card Program",                           "07 Jan 2020"),
    ("3305.02",    "DoD Personnel Security Program Administration",             "03 Nov 2020"),
    ("4140.01",    "DoD Supply Chain Materiel Management Procedures",           "14 Feb 2019"),
    ("4160.21",    "Defense Materiel Disposition Procedures",                   "22 Oct 2015"),
    ("5100.76",    "Physical Security of Sensitive Conventional Arms",          "17 Apr 2012"),
    ("5105.21-V1", "Sensitive Compartmented Information – Volume 1",            "19 Oct 2012"),
    ("5105.21-V2", "Sensitive Compartmented Information – Volume 2",            "19 Oct 2012"),
    ("5105.21-V3", "Sensitive Compartmented Information – Volume 3",            "19 Oct 2012"),
    ("5200.01-V1", "DoD Information Security Program – Volume 1: Overview",    "26 Feb 2012"),
    ("5200.01-V2", "DoD Information Security Program – Volume 2: Marking",     "26 Feb 2012"),
    ("5200.01-V3", "DoD Information Security Program – Volume 3: Protection",  "26 Feb 2012"),
    ("5200.01-V4", "DoD Information Security Program – Volume 4: Controlled Unclassified","26 Feb 2012"),
    ("5200.45",    "Instructions for Developing Security Classification Guides","02 Apr 2013"),
    ("5240.01",    "Procedures Governing the Conduct of DoD Intelligence Activities","08 Aug 2016"),
    ("5400.07",    "DoD Freedom of Information Act Program",                    "28 Jun 2018"),
    ("5400.11-R",  "Department of Defense Privacy Program",                    "14 May 2007"),
    ("6025.18",    "Health Insurance Portability Procedures",                   "13 Mar 2019"),
    ("6500.1",     "Information Assurance Policy",                              "24 Oct 2002"),
    ("8910.1-M",   "DoD Reports Management Program",                           "26 Nov 2010"),
]

# ============================================================
# 09 - DIRECTIVE TYPE MEMORANDA (DTM)
# ============================================================
DTM_DOCS = [
    ("DTM-09-026",  "Responsible and Effective Use of Internet-based Capabilities",    "25 Feb 2009"),
    ("DTM-14-003",  "Implementation of Personnel Recovery",                            "06 Jan 2014"),
    ("DTM-14-005",  "Military Service by Transgender Persons",                         "18 Jun 2016"),
    ("DTM-16-003",  "Deferred Resignation",                                            "26 Feb 2016"),
    ("DTM-17-004",  "Physical Security of DoD Installations and Resources",            "16 Mar 2017"),
    ("DTM-18-004",  "DoD Civilian Expeditionary Workforce",                            "18 Sep 2018"),
    ("DTM-19-001",  "Implementation Guidance for National Defense",                    "15 Feb 2019"),
    ("DTM-19-004",  "Expansion of DoD Authority to Recruit",                           "30 Sep 2019"),
    ("DTM-20-004",  "Provision of COVID-19 Vaccination Benefits",                      "11 Dec 2020"),
    ("DTM-21-003",  "Guidance on COVID-19 Federal Workforce Vaccination Requirements", "07 Sep 2021"),
    ("DTM-22-001",  "Expansion of Military Service Opportunities",                     "04 Mar 2022"),
    ("DTM-22-003",  "Compensation and Leave for Federal Civilian Employees",           "09 May 2022"),
    ("DTM-23-001",  "Actions to Address Extremist Activity",                           "05 Jan 2023"),
    ("DTM-23-003",  "Anti-Harassment Policy",                                          "20 Apr 2023"),
]

# ============================================================
# 10 - CJCS INSTRUCTIONS
# ============================================================
CJCSI_DOCS = [
    ("1001.01B",  "Joint Manpower and Personnel Program",                        "01 Mar 2021"),
    ("1100.01E",  "Mission Assignments",                                         "14 Sep 2018"),
    ("1215.01B",  "Joint Individual Augmentation Procedures",                   "26 Feb 2019"),
    ("1500.01F",  "Joint Training Policy",                                       "13 Sep 2019"),
    ("2300.01D",  "Humanitarian and Civic Assistance Activities",               "12 Jan 2021"),
    ("2910.01F",  "Combatant Command Requirements Definition",                  "01 Oct 2015"),
    ("3010.02E",  "Guidance for Development of the Forces",                      "01 Apr 2019"),
    ("3020.05E",  "Business Continuity and Continuity of Operations",           "28 Nov 2016"),
    ("3121.01B",  "Standing Rules of Engagement/Standing Rules for Use of Force","13 Jun 2005"),
    ("3150.25G",  "CJCS Nuclear Weapon Security Manual",                        "18 Mar 2019"),
    ("3170.01I",  "Operation of the Joint Capabilities Integration and Development System","31 Jan 2022"),
    ("3205.01D",  "Joint Planning",                                              "07 Feb 2020"),
    ("3210.07D",  "Personnel Recovery",                                          "02 Apr 2013"),
    ("3211.01E",  "Personnel Recovery Command and Control",                     "01 Mar 2016"),
    ("3270.01C",  "Personnel Recovery within the Department of Defense",        "06 Jul 2020"),
    ("3500.01I",  "Joint Training Policy for the Armed Forces",                  "13 Sep 2019"),
    ("3710.01F",  "DoD Counterdrug Support",                                     "05 Oct 2017"),
    ("4310.01E",  "Materiel Identification of Government Property",             "01 Apr 2019"),
    ("5119.01G",  "Chairman of the Joint Chiefs of Staff Communication",        "19 Nov 2019"),
    ("5120.02E",  "Joint Doctrine Development Process",                          "10 Feb 2022"),
    ("5160.01D",  "Sovereignty, Jurisdictional, and Status of Forces Issues",  "21 Jan 2020"),
    ("5711.01F",  "Communication with Congress",                                 "19 Dec 2018"),
    ("5714.01E",  "Release of Information Concerning Missing Personnel",        "22 May 2019"),
    ("5760.01B",  "DoD Postal Policy",                                           "13 Sep 2017"),
    ("5810.01F",  "Implementation of the DoD Law of War Program",               "25 Mar 2020"),
    ("6210.01G",  "Defense Information System Network",                          "20 Feb 2020"),
    ("6251.01E",  "Multinational Information Sharing Networks",                  "05 Jan 2015"),
    ("6510.01F",  "Cyber Incident Handling Program",                             "10 Feb 2017"),
    ("6510.02",   "Cybersecurity",                                               "12 Mar 2014"),
    ("7401.01E",  "Logistics Data and Logistics Automated Information Systems", "01 Apr 2017"),
]

# ============================================================
# 11 - CJCS MANUALS
# ============================================================
CJCSM_DOCS = [
    ("0400.01B",  "Organizational Messages",                                     "07 Apr 2017"),
    ("3000.02B",  "Universal Joint Task List",                                   "01 Oct 2018"),
    ("3122.01C",  "Joint Operation Planning",                                    "04 Feb 2022"),
    ("3122.02D",  "Joint Operation Planning and Execution System Vol I",        "14 Jul 2020"),
    ("3122.03D",  "Joint Operation Planning and Execution System Vol II",       "14 Jul 2020"),
    ("3122.04",   "Joint Operation Planning Annexes",                           "01 Aug 2018"),
    ("3130.01A",  "Campaign Planning Procedures",                                "25 Jan 2021"),
    ("3130.03A",  "Planning and Execution Procedures",                           "21 Nov 2019"),
    ("3130.06B",  "Global Force Management Allocation Policies",                "12 Feb 2020"),
    ("3150.05A",  "Nuclear Matters Handbook",                                    "16 Nov 2020"),
    ("3150.13C",  "Nuclear Safety and Surety",                                   "08 Feb 2019"),
    ("5111.13",   "Joint Doctrine Publication Development",                      "05 Dec 2018"),
    ("6010.01",   "Defense Messaging System",                                    "19 Nov 2019"),
]

# ============================================================
# 12 - CJCS NOTICES
# ============================================================
CJCSN_DOCS = [
    ("5120",  "Notice on Joint Doctrine Development",               "Periodic"),
    ("5710",  "Notice on Legislative Activity",                     "Periodic"),
    ("5760",  "Notice on Postal Policy Updates",                    "Periodic"),
    ("6510",  "Notice on Cybersecurity Updates",                    "Periodic"),
]

# ============================================================
# 14 - UNIFORM REGULATIONS articles
# ============================================================
UNIFORM_REG_ARTICLES = [
    ("chapter-1",    "Chapter 1 – Authority, Administration, and Wear"),
    ("chapter-2",    "Chapter 2 – Grooming Standards"),
    ("chapter-3",    "Chapter 3 – General Uniform Policies"),
    ("chapter-4",    "Chapter 4 – Dress Uniforms"),
    ("chapter-5",    "Chapter 5 – Service Uniforms"),
    ("chapter-6",    "Chapter 6 – Working Uniforms"),
    ("chapter-7",    "Chapter 7 – Physical Training Uniforms"),
    ("chapter-8",    "Chapter 8 – Ceremonial Dress Uniforms"),
    ("chapter-9",    "Chapter 9 – Navy Nurse Corps"),
    ("chapter-10",   "Chapter 10 – Dental Corps"),
    ("article-1101", "Article 1101 – Authority and Scope"),
    ("article-1102", "Article 1102 – Grooming and Dress Policies"),
    ("article-1103", "Article 1103 – Uniform Policy"),
    ("article-1201", "Article 1201 – Hair Grooming Standards"),
    ("article-1202", "Article 1202 – Fingernail Standards"),
    ("article-2001", "Article 2001 – Wear Policy"),
    ("article-2101", "Article 2101 – Combination Cover"),
    ("article-2102", "Article 2102 – Full Dress Uniform"),
    ("article-2201", "Article 2201 – Dinner Dress Uniform"),
    ("article-3101", "Article 3101 – Service Uniform"),
    ("article-3501", "Article 3501 – Service Khaki"),
    ("article-4101", "Article 4101 – Working Uniform"),
    ("article-5101", "Article 5101 – Physical Training Uniform (PTU)"),
]

# ============================================================
# 15 - CAREER MANAGEMENT sections
# ============================================================
CAREER_MGMT_SECTIONS = [
    ("Career-Management/",                                     "Career Management Home"),
    ("Career-Management/Enlisted/",                            "Enlisted Career Management"),
    ("Career-Management/Enlisted/Advancement/",                "Enlisted Advancement"),
    ("Career-Management/Enlisted/Assignment/",                 "Enlisted Assignment"),
    ("Career-Management/Enlisted/Reenlistment/",               "Reenlistment"),
    ("Career-Management/Enlisted/Retention/",                  "Enlisted Retention"),
    ("Career-Management/Officer/",                             "Officer Career Management"),
    ("Career-Management/Officer/Advancement/",                 "Officer Advancement"),
    ("Career-Management/Officer/Assignment/",                  "Officer Assignment"),
    ("Career-Management/Officer/Promotions/",                  "Officer Promotions"),
    ("Career-Management/Training-Education/",                  "Training and Education"),
    ("Career-Management/Training-Education/Voluntary-Education/","Voluntary Education"),
    ("Career-Management/Training-Education/Professional-Development/","Professional Development"),
    ("Career-Management/Awards/",                              "Awards and Decorations"),
    ("Career-Management/Separations/",                         "Separations"),
    ("Career-Management/Retirement/",                          "Retirement"),
    ("Career-Management/Family-Support/",                      "Family Support Programs"),
    ("Career-Management/Legal/",                               "Legal Services"),
    ("Career-Management/Physical-Readiness/",                  "Physical Readiness"),
    ("Career-Management/Navy-College/",                        "Navy College"),
    ("Career-Management/Leave/",                               "Leave"),
    ("Career-Management/Pay-Benefits/",                        "Pay and Benefits"),
    ("Career-Management/Records/",                             "Service Records"),
    ("Career-Management/Recruiting/",                          "Recruiting Programs"),
]
