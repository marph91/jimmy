---
description: This page describes how to contribute to Jimmy.
---

## Contact

- General discussion at the
    - [Joplin forum](https://discourse.joplinapp.org/t/jimmy-a-joplin-import-tool/38503)
    - [Obsidian Forum](https://forum.obsidian.md/t/jimmy-convert-your-notes-to-markdown/88685)
- Report a bug or request a new feature at [GitHub](https://github.com/marph91/jimmy/issues/new/choose)
- Send an <a href="&#109;&#97;&#105;&#108;&#116;&#111;&colon;&#109;&#97;&#114;&#116;&#105;&#110;&period;&#100;&commat;&#97;&#110;&#100;&#105;&#120;&period;&#100;&#101;">email</a> (might be filtered by my spam filter)

## As non-programmer

- You can help the project by providing an export file. This helps to identify and fix issues.
- Add documentation or fix spelling mistakes
- Test the app
- Write in forums of your note application if Jimmy works for you

## How to add a new format?

Here is a [good example commit](https://github.com/marph91/jimmy/commit/362acf0319b130c5abb90324129b76c1b5ebefca).

The brief workflow is:

1. Discuss the format at the forum or GitHub
2. Implement at [src/](https://github.com/marph91/jimmy/tree/master/src/formats)
3. Provide an example file and [add a test](https://github.com/marph91/jimmy/blob/master/test/example_commands.sh)
4. Lint with [lint.sh](https://github.com/marph91/jimmy/blob/master/lint.sh)
5. Document at [docs/](https://github.com/marph91/jimmy/tree/master/docs/formats)
