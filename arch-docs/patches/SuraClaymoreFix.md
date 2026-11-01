# SuraClaymoreFix

- **Source:** `src/SuraClaymoreFix/`
- **Ships:** `Zenderal - Sura Claymore Fix.esp`
- **FormID block:** none (overrides only)
- **Status:** built 2026-10-17, **not yet verified in game**. The cause is suspected, not proven.

## The report

Discord, 2026-10-13 and 2026-10-15, two players: at the first blacksmith in Riverville, buying a
claymore/greatsword gives you **4** of them. Selling them back crashes after the second one, and so
does dropping them. A second player gets the same crash selling things to that blacksmith.

## What was found

- The blacksmith is **Sura** (`FlusshaimShopSura 033B19`, "Sura's Sharp Steel"). Her merchant chest is
  `_00E_Merchant_FlusshaimSuraContainer 05BCD7:Skyrim.esm`. **[verified]**
- That chest lists `_01E_02_IronClaymore 0028D3` **twice**, as two separate count-1 entries. The
  duplicate is SureAI's own: base `Skyrim.esm`, FS and EGO all carry it. **[verified]**
- Eleven vendor chests in base Enderal have duplicated entries, but every other one is a book, food,
  potion, scroll, plan, nails or a ring. **Sura's is the only duplicated weapon** among Enderal's
  merchant chests. **[verified]** (Scan: `Containers/*Merchant*` in `reference/base/Skyrim`, `EnderalFS`
  and EGO.)
- In the live list, only `Enderal SE - Gameplay Overhaul.esp` overrides `05BCD7`. Neither
  `Sura_CustomMerchandise 0302F6` nor any claymore record is overridden by another plugin, apart from
  Pretty Unique Armory's unrelated `IronClaymoreColdNight`. This was checked with a byte grep of every
  plugin under `E:/Zenderal/mods`. **[verified]**
- **Item Stacking Tweaks SKSE 1.0.7** (Nexus 173918) is enabled. It splits inventory stacks by their
  stolen, quest, favourite and equipped state, and its hooks touch barter, drop and container
  transfer. Its source repo is gone, so the interaction could not be read. Duplicate container
  entries are harmless in vanilla Enderal, so the **suspected** cause is the two-entry stack
  combined with that plugin's split/merge hooks. This is unverified.
- The meshes were ruled out as far as a header read allows. Enderal Remastered Armory supplies
  `ironBidenhaender.nif` and `rusty/WitcherSword.nif`, and both have ordinary `bhkRigidBody` collision
  trees. A mesh fault also would not explain the "bought 4".
- No crash log from this machine involves a weapon; the reporters' logs were not available.

## What the patch does

It overrides `05BCD7` with EGO's record copied verbatim (the live EGO plugin was re-serialized
2026-10-17 and matches `reference/`), except that the two `0028D3` entries are merged into one entry
of **count 2**. The stock amount is unchanged. It masters EGO so that it loads after it.

## Testing it

1. In game, `coc FlusshaimShopSura`. **A chest that has already respawned keeps its old inventory**,
   so test on a save that has never visited Sura, or wait out the respawn. Buy one Iron Claymore,
   sell it back, buy again, then drop one.
2. If it still crashes, disable Item Stacking Tweaks and repeat. If that fixes it, the plugin is the
   cause, and this patch should be retired in favour of dropping or configuring that plugin.
3. If neither changes anything, get the reporter's NetScriptFramework crash log. The cause is
   elsewhere.
