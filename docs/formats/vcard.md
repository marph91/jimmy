This page describes how to import notes from vCard to markdown.

## General Information

- [Website](https://en.wikipedia.org/wiki/VCard)
- Typical extension: `.vcf`

## Instructions

1. Export your contacts in vCard format
2. [Install jimmy](../index.md#installation)
3. Convert to markdown. Example: `jimmy-cli-linux vcards_20240811_175319.vcf--format vcard`

## Import Structure

- Each contact is a separate note.
- The note title is the name of the contact.
- Each attribute is a bullet point. If there are multiple values for the same attribute (for example multiple phone numbers), they are in a nested list.
