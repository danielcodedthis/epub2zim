# FAQ

**What is a ZIM file?**
An open file format for offline content, made by the [openZIM](https://openzim.org)
project and used by Kiwix for Wikipedia. It holds many HTML pages, pictures and a search
index in one compressed file.

**Which readers can open the result?**
Zimi, Kiwix (desktop, Android, iOS, kiwix-serve), and anything built on libzim.

**Does anything leave my computer?**
No. epub2zim runs locally and needs no internet (the fonts are bundled). AI assistants
connected over MCP see what their tools return; if the model itself is a cloud service,
that text goes to that service.

**What about PDFs or MOBI files?**
Convert them to EPUB first, e.g. with [Calibre](https://calibre-ebook.com)
(`ebook-convert book.pdf book.epub`). PDFs convert poorly; the result is like a scanned
book, so use the [title list](scanned-books.md) strategy.

**Can I convert DRM-protected books?**
No. epub2zim reads standard EPUB files only.

**Is converting a book legal?**
Converting a book you own for personal use is generally fine where format-shifting is
allowed, but laws differ. Please don't share ZIM files of copyrighted books. Public-domain
books (e.g. from Project Gutenberg) are a great place to start.

**Can I edit an article after building?**
Not inside the ZIM. Change the settings or title list and build again; it takes seconds.

**Why “page file” and not “page”?**
EPUBs have no fixed pages. A *page file* is one HTML file in the book's reading order. In
scanned books one file is one printed page, so the two are related by the *page offset*.

**Why are some words links?**
Wiki-style links to other articles. Switch them off or raise the minimum title length in
step 3.

**How do I back up?**
Copy the data folder. Each book's folder contains its EPUB, settings and title list, so
you can rebuild anytime.
