# MrSpongeHead Repository

A Kodi repository for add-ons by MrSpongeHead, including **SpongeTV**.

## Install in Kodi

1. **Settings → File manager → Add source.** Enter
   `https://mrspongehead.github.io/repository.mrspongehead/` and name it `mrspongehead`.
2. **Settings → Add-ons → Install from zip file → mrspongehead** and choose
   `repository.mrspongehead-x.y.z.zip`. (If Kodi asks, allow unknown sources first.)
3. **Install from repository → MrSpongeHead Repository → Video add-ons → SpongeTV.**

Kodi then keeps the add-ons up to date automatically.

## Publishing (maintainers)

`python3 tools/publish.py path/to/plugin.video.spongetv-x.y.z.zip` adds the zip, rebuilds
`zips/addons.xml` and its checksum, the repository zip and `index.html`. Commit and push;
GitHub Pages serves the files.

Licence: GPL-3.0-or-later.
