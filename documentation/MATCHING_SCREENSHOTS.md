# System screenshots of NLP matching

Captured November 18, 2026 from the running Flask application at local port 5003. Four fictional editors and two jobs were prepared in a separate demonstration database. No private running database or real application was changed. The browser signed in normally and used the actual applicant comparison and selection interface.

Travel brief: “Cinematic travel editing in Premiere Pro with color grading”. Stored extraction: Adobe Premiere Pro, Color Grading; cinematic; travel.
Gaming brief: “Fast-paced gaming editing in CapCut”. Stored extraction: CapCut; fast-paced; gaming.

| Applicant | Travel score | Gaming score | Travel application after creator selection |
| --- | --- | --- | --- |
| Alex Full Match | 100% | 0% | Declined |
| Blair Partial Match | 75% | 0% | Accepted |
| Drew Profile Skills | 25% | 0% | Declined |
| Casey Gaming Editor | 0% | 100% | Declined |

Alex and Blair had approved cinematic/travel portfolio evidence. Alex also offered Color Grading. Drew offered Premiere Pro in the profile and had no portfolio. Casey offered CapCut and approved fast-paced/gaming evidence. Media links used example.com placeholders; the screenshots do not establish that any actual video was reviewed.

The creator selected Blair through the interface confirmation. The observed result was one accepted and three declined applications, zero pending applications and a job in progress. Score ranking did not force the highest-scoring choice. The screenshot names describe fixture roles; they are not assessments of real people.

## Files

- `screenshots/nlp-travel-extracted.jpg`: brief and all extracted categories.
- `screenshots/nlp-match-100.jpg`, `nlp-match-75.jpg`, `nlp-match-25.jpg`, `nlp-match-0.jpg`: complete applicant-card crops, retaining score, skills, proposal, portfolio evidence and selection control.
- `screenshots/nlp-gaming-match-100.jpg`: Casey for the gaming brief.
- `screenshots/nlp-selection-result.jpg`: resulting selected editor, job state and accepted/declined totals.
- Full-page source images: `nlp-travel-requirements-full.jpg`, `nlp-travel-applicants-full.jpg`, `nlp-gaming-applicants-full.jpg`, `nlp-selection-result-full.jpg`.

Crops remove surrounding page space only. No score, name, status or other content was composited or edited. Chapter 5 contains the seven focused screenshots as Figures 5.5–5.11. These browser observations supplement, and are not extra cases added to, the 49-test automated suite.
