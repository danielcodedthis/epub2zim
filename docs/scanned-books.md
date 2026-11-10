# Scanned books walkthrough

Scanned books converted to EPUB (for example by the Internet Archive) are the hardest
case: one HTML file per printed page, no table of contents, no headings, and the page
number and running header printed in the middle of the text. epub2zim was built for
exactly this. Expect 15–60 minutes for a big reference book, most of it checking.

## 1. Confirm it's a scan

Step 1 says **“Looks like a scanned book”** and suggests *Title list*. You'll see many
files, 0 headings, and a page offset (e.g. *printed page 1 is file 45*).

Open *Peek inside* and read a few pages in the middle. Typical scan text:

```
Page 204 160 Depressive Disorders Major Depressive Disorder Diagnostic Criteria A. Five (or more)…
```

`Page 204` is the converter's label, `160` the printed page, `Depressive Disorders` the
running header. All three are removed automatically.

## 2. Get a first title list

In step 2 choose **✍️ Title list**, then **Fill from**:

- **Running headers (scans):** reads the header printed at the top of each page. Right-hand
  pages usually carry the section name, left-hand pages the chapter. Gives a good skeleton
  quickly.
- **Pattern:** when sections start with a fixed phrase. For a manual where every section
  starts with “<Name> Diagnostic Criteria”:

  ```
  ((?:[A-Z][\w'’/,()-]+ ){1,10})Diagnostic Criteria
  ```

  The part in `( )` becomes the title. Test patterns with *Peek inside → regular expression*
  first.
- **Table of contents:** if a contents list exists but is incomplete, start from it.

You can also paste a list you made elsewhere, e.g. typed from the printed contents page,
using `p.123` printed page numbers.

## 3. Clean it up

- Delete entries that aren't sections (the book's own title used as a running header,
  “Contents”, “Index”).
- Add `=` group lines (Section I, Appendix…) and `-` levels for chapter → disorder nesting.
- Keep the book's spelling, including OCR errors. Use the third column for the exact
  starting words when they differ from the title you want.

## 4. Preview, fix, repeat

Click **Preview articles** (step 4). Work through:

1. **Not found:** search each one in step 1. Usually the spelling differs
   (`Bipolar | Disorder` instead of `Bipolar I Disorder`) or the page is off. Fix it and
   preview again.
2. **Very short articles:** a title matched a mention instead of the heading. Add or correct
   the page, or use more specific text to look for.
3. **Very long articles:** a title is missing from the list.
4. **First words:** each article should start with its own content.

## 5. Make articles nicer

In the *Scanned-book clean-up* box:

- **Section headings:** phrases that start sections inside articles, one per line, e.g.

  ```
  Diagnostic Criteria
  Diagnostic Features
  Prevalence
  Development and Course
  Differential Diagnosis
  Comorbidity
  ```

  They only become headings at the start of a sentence and before a capital letter, so
  prose mentions stay prose.
- **List detection:** puts `A. … B. …` and `1. … 2. …` items on their own lines (great for
  criteria lists).
- **Paragraph length:** scans lose paragraph breaks; epub2zim rebuilds them at sentence ends.

## 6. Aliases and build

Add aliases for abbreviations in step 3 (`PTSD = Posttraumatic Stress Disorder`), then
build. Every article from a scan ends with a small note that the text comes from OCR.

## What can't be fixed automatically

- OCR spelling errors inside the text.
- Tables flattened into one line of text.
- Footnotes that ended up in the middle of a paragraph.
