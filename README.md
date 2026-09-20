# Umbrage Repository
[English](./README.md) | [Русский](./README_ru.md)

A repository of community-made templates for MediaTek devices used with the Umbrage project.

## What is a template?
In Umbrage, a template is a set of `DA`/`Auth`/`Preloader` files plus a `.yml` metafile. Tools compatible with Umbrage use it to figure out which files fit a given device.

A single template can hold several versions.

## What is a version?
A template version is one set of DA/Auth/Preloader files for a single device.

Versions can differ because of a device revision, a firmware version, the exploit used, or simply because a particular set of files happened to work with that device.

## Template formatting rules
- **1 device == 1 template.** The exception is when a device is literally the same board with the same firmware, just with different components soldered onto it.
- Values in the `vendor` and `model` fields must start with a capital letter.
- The `codename` field must be lowercase.
- Briefly describe in `name` and `description` what these files do or what to watch out for. Look at other templates for examples.
- Use `default: true` only for versions tested with Umbrage and known to work 100%. This flag means you recommend others use this version and that you tested it yourself.

## Adding or editing a template
Umbrage Beta 0.1.1 added a built-in template generator, which is the recommended way to make changes.

1. Run [Umbrage](https://github.com/progzone122/umbrage), pick a template to edit, or select files for a new one by hand.
2. Connect the device to confirm the files work.
   > If you can't test the files right now, pass `--skip-conn` when running Umbrage to skip the connection step.
   >
   > **PLEASE NOTE!** If you didn't verify the device works with these files in Umbrage, we **STRONGLY ASK YOU NOT** to mark this version as `Recommend this is a default version` or `default: true`.

3. Open `Other` → `Template generator` and export the template's metafile.

4. Fork this repo and move **ALL the files you used** into the `files` directory **WITHOUT RENAMING THEM**.

   If there's a file conflict, compare checksums with `sha256sum`. If they match, skip the replacement; the file is already in the repository.

   Otherwise, add `2`, `3`, `4`, and so on to the end of the filename to resolve it, then edit the metafile to point at the new names.

5. Move the metafile into `meta/<vendor>/<codename>.meta.yml`. *If a directory for your vendor doesn't exist yet, create it.*

6. Open a Pull Request and address any feedback.

**Huge thanks to everyone who contributes to Umbrage** 💖

You make life easier for other people!
