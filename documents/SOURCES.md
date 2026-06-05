# Source Documents — The Unofficial Guide: Becoming a Sport Flight Instructor

## Domain summary

This Unofficial Guide covers **how to become a Flight Instructor with a Sport Pilot
rating (CFI-S) in the United States**, and the knowledge such an instructor is
expected to hold and teach. This knowledge is hard to find in one place: it is
scattered across federal regulations, separate FAA testing standards, advisory
circulars, and multi-hundred-page handbooks — each written in dense, cross-referencing
"FAA-ese." A prospective instructor normally has to know *which* document answers a
given question (e.g., aeronautical experience requirements live in 14 CFR Part 61, but
the practical-test tasks live in the ACS/PTS, and teaching theory lives in the Aviation
Instructor's Handbook). This RAG system makes that corpus searchable in plain language.

All documents are **public-domain U.S. Government / FAA publications**, downloaded from
official sources (faa.gov and govinfo.gov). Total: **10 documents, 1,099 pages.**

## Example questions this corpus should answer

1. What aeronautical experience is required before you can apply for a flight instructor certificate?
2. How does a sport pilot flight instructor's authorization differ from a regular CFI's?
3. What does the FAA say about the "law of primacy" and other laws of learning?
4. What tasks must an applicant demonstrate on the Flight Instructor practical test?
5. What endorsements must an instructor give a student before solo flight?

## Documents

| # | File | FAA designator | Source URL | Pages | What it covers |
|---|------|----------------|------------|-------|----------------|
| 1 | `14-CFR-Part-1_Definitions-and-Abbreviations.pdf` | 14 CFR Part 1 | https://www.govinfo.gov/content/pkg/CFR-2024-title14-vol1/pdf/CFR-2024-title14-vol1-part1.pdf | 16 | Regulatory definitions (incl. "sport pilot," "light-sport aircraft") and abbreviations. |
| 2 | `14-CFR-Part-61_Certification-Pilots-Flight-Instructors.pdf` | 14 CFR Part 61 | https://www.govinfo.gov/content/pkg/CFR-2024-title14-vol2/pdf/CFR-2024-title14-vol2-part61.pdf | 130 | Certification rules for pilots and flight/ground instructors — eligibility, experience, privileges, endorsements. The core regulation for this domain. |
| 3 | `14-CFR-Part-91_General-Operating-and-Flight-Rules.pdf` | 14 CFR Part 91 | https://www.govinfo.gov/content/pkg/CFR-2024-title14-vol2/pdf/CFR-2024-title14-vol2-part91.pdf | 163 | General operating and flight rules an instructor teaches and operates under. |
| 4 | `AC_61-65K_Certification-Pilots-Flight-Ground-Instructors.pdf` | AC 61-65K | https://www.faa.gov/documentLibrary/media/Advisory_Circular/AC_61-65K.pdf | 60 | Advisory Circular: guidance + sample endorsement wording for pilots and flight/ground instructors. |
| 5 | `FAA-G-ACS-2_ACS-Companion-Guide-for-Pilots.pdf` | FAA-G-ACS-2 | https://www.faa.gov/training_testing/testing/acs/acs_companion_guide_pilots.pdf | 27 | Companion guide explaining how to read and use the ACS, references, and acronyms. |
| 6 | `FAA-H-8083-2A_Risk-Management-Handbook.pdf` | FAA-H-8083-2A | https://www.faa.gov/sites/faa.gov/files/2022-06/risk_management_handbook_2A.pdf | 80 | Risk management frameworks (e.g., PAVE, IMSAFE, 5P) instructors must teach. |
| 7 | `FAA-H-8083-9A_Aviation-Instructors-Handbook.pdf` | FAA-H-8083-9A | https://www.govinfo.gov/content/pkg/GOVPUB-TD4-PURL-LPS109875/pdf/GOVPUB-TD4-PURL-LPS109875.pdf | 228 | The central teaching-theory text: learning theory, the teaching process, assessment, professionalism. |
| 8 | `FAA-S-8081-29_Sport-Pilot-and-Sport-Pilot-Flight-Instructor-PTS.pdf` | FAA-S-8081-29 | https://www.faa.gov/sites/faa.gov/files/training_testing/testing/test_standards/faa-s-8081-29.pdf | 197 | Practical Test Standards for the **sport pilot and sport pilot flight instructor** checkrides. Most domain-specific document. |
| 9 | `FAA-S-ACS-25_Flight-Instructor-Airplane-ACS.pdf` | FAA-S-ACS-25 | https://www.faa.gov/training_testing/testing/acs/cfi_airplane_acs_25.pdf | 111 | Airman Certification Standards for the Flight Instructor (Airplane) certificate — the oral/practical exam blueprint. |
| 10 | `FAA-S-ACS-6C_Private-Pilot-Airplane-ACS.pdf` | FAA-S-ACS-6C | https://www.faa.gov/training_testing/testing/acs/private_airplane_acs_6.pdf | 87 | Private Pilot ACS — the standard an instructor trains students *to*; useful for "what must my student be able to do?" questions. |

## Notes / provenance

- **Editions:** Regulations are the 2024 annual CFR edition from GovInfo. Testing standards
  and ACs are the current FAA editions as of June 2026. The Aviation Instructor's Handbook
  is the official GovInfo full-text edition (FAA-H-8083-9A); the newer 9B is published by
  the FAA only as a 145 MB high-resolution PDF that exceeds GitHub's 100 MB file limit, so
  the equivalent-content 9A full-text PDF was used to keep the repo pushable. Content
  relevant to this project (learning theory, the teaching process) is materially the same.
- **Text extraction:** all 10 PDFs are digitally created (selectable text) and verified to
  extract via `pdfplumber` without OCR.
- **"Oral exam mock-up guides":** the FAA does not publish a standalone oral-exam-questions
  document. The oral (knowledge) portion of the checkride is defined by the **ACS/PTS**
  (documents 8 and 9), which list every knowledge and risk-management element an examiner
  may ask about — these serve as the authoritative oral-exam blueprint. Commercial "oral
  exam guides" (e.g., ASA) are copyrighted and were intentionally not included.

## Optional additions (not yet downloaded)

If broader pilot-knowledge coverage is wanted, consider adding (both are large, ~500 pp):
- **Pilot's Handbook of Aeronautical Knowledge** (FAA-H-8083-25) — general aeronautical knowledge.
- **Airplane Flying Handbook** (FAA-H-8083-3) — flight maneuvers and techniques.

These were excluded from the core set to keep the corpus focused and within a reasonable
chunk budget; ask if you want them pulled in.
