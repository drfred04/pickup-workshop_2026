# Uploading the gate labs to D2L Brightspace

Files to upload (each is a single self-contained page):

| File | Activity |
| --- | --- |
| `water-gate-lab.html` | Holding Back the Water: A Gate Equilibrium Lab (3 sheets) |
| `stepped-gate-lab.html` | The Stepped Gate: Holding It Shut at the Hinge (2 sheets) |

These are copies of `../water_gate_lab.html` and `../stepped_gate_lab.html`. If you edit an original, copy it here again before re-uploading.

## 1. Add each lab as a Content topic

1. In the course, open **Content** and choose the module.
2. **Upload / Create → Upload Files**, then pick the `.html` file. Brightspace makes it a topic and shows the page inside the course, with its scripts running.
3. Rename the topic if you like (e.g. "Stepped Gate Lab").
4. Do **not** paste the code into **Create a File** or the HTML editor. Brightspace strips the scripts there and the lab will not work.

## 2. Add a dropbox for the reports

1. **Assignments → New Assignment**, one per lab (e.g. "Stepped Gate Lab Report").
2. Submission type: **File submission**, so students can upload the `.txt` report. Text submissions also work, for students who use **Copy report** and paste.
3. Link the assignment under the lab topic in the module, so students go straight from the lab to the dropbox.

Students click **Generate report**, then **Download report (.txt)**, and upload that file. Work is saved in the student's own browser as they go. It won't follow them to another computer or browser, so suggest they finish on one device.

## 3. Check it as a student

Use **View as Student** (or a test student account) to open each topic. Then:
- Click a check button.
- Reload the page and confirm the answer is still there.
- Download a report.

If the download is blocked inside Brightspace, **Copy report** is the fallback, and the page tells students to use it.

## 4. Grade a report

Open your local copy of the lab with `#instructor` added to the end of the address, for example:

`file:///…/water_gate/stepped_gate_lab.html#instructor`

Paste the student's report into the **Instructor: verify a submitted report** panel. It re-grades every answer, using the student's own random numbers and assumed reaction senses, and checks the integrity hash. Lines whose claimed PASS/FAIL disagrees with re-grading are flagged.

The hash catches casual editing of the report. It does not stop a determined student, because the page's own code can regenerate it.

## Notes

- The pages load fonts from Google Fonts. If that's blocked, they fall back to system fonts and still work.
- Each lab saves under its own browser-storage key, so the two labs don't interfere.
- Checked inside a frame at phone width (390 px) and in dark mode: no sideways scrolling, and all diagrams draw. On phones the sheet tabs stack vertically so every sheet is visible.
